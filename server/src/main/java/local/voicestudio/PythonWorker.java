package local.voicestudio;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;
import jakarta.annotation.PreDestroy;

@Component
public class PythonWorker implements SpeechWorker {
    private final StudioPaths paths;
    private final ObjectMapper json;
    private volatile Process process;
    private final Object lifecycle = new Object();
    private BufferedReader reader;
    private BufferedWriter writer;
    private final ScheduledExecutorService deadlines = Executors.newSingleThreadScheduledExecutor(r -> { var t = new Thread(r, "worker-deadline"); t.setDaemon(true); return t; });

    public PythonWorker(StudioPaths paths, ObjectMapper json) { this.paths = paths; this.json = json; }
    private void start() throws IOException {
        synchronized (lifecycle) {
            if (process != null && process.isAlive()) return;
            var logs = paths.root().resolve(".runtime/logs"); Files.createDirectories(logs);
            var builder = new ProcessBuilder(paths.root().resolve(".venv/bin/python").toString(), "-u", "-m", "voice_cloner.worker");
            builder.directory(paths.root().toFile());
            paths.configurePython(builder);
            builder.redirectError(ProcessBuilder.Redirect.appendTo(logs.resolve("python-worker.log").toFile()));
            process = builder.start();
            reader = process.inputReader(StandardCharsets.UTF_8);
            writer = process.outputWriter(StandardCharsets.UTF_8);
        }
    }
    @Override public synchronized Job.Result generate(String id, GenerationRequest request, Consumer<Progress> progress) throws Exception {
        var command = new LinkedHashMap<String, Object>();
        command.put("id", id); command.put("voiceId", request.voiceId()); command.put("text", request.text());
        command.put("sourceId",request.sourceId()); command.put("durationSeconds",request.durationSeconds());
        command.put("modelId", request.modelId()); command.put("presetVoice", request.presetVoice()); command.put("voiceDescription", request.voiceDescription());
        command.put("voiceMode",request.voiceMode());
        command.put("emotion", request.emotion()); command.put("language", request.language()); command.put("seed", request.seed());
        var event = exchange(id, command, progress);
        var peaks = new ArrayList<Double>(); event.path("peaks").forEach(p -> peaks.add(p.asDouble()));
        if (event.path("duration").asDouble() <= 0 || peaks.isEmpty() || !Files.isRegularFile(paths.audio().resolve(id + ".wav"))) throw new IOException("Python не сохранил готовую запись.");
        return new Job.Result(id, "/api/audio/" + id, event.path("duration").asDouble(), event.path("sampleRate").asInt(), peaks, event.path("seed").asLong(), event.path("temperature").isNumber()?event.path("temperature").asDouble():null);
    }
    @Override public synchronized PreparedVoice prepareVoice(String id, double start, double duration, String language, Consumer<Progress> progress) throws Exception {
        return prepareVoice(id,start,duration,language,null,progress);
    }
    @Override public synchronized PreparedVoice prepareVoice(String id, double start, double duration, String language, String modelId, Consumer<Progress> progress) throws Exception {
        var command = new LinkedHashMap<String,Object>();
        command.put("id",id); command.put("type","prepare_voice"); command.put("start",start); command.put("duration",duration); command.put("language",language);
        if(modelId!=null)command.put("modelId",modelId);
        var event = exchange(id, command, progress);
        var warnings = new ArrayList<String>(); event.path("warnings").forEach(w -> warnings.add(w.asString()));
        return new PreparedVoice(event.path("transcript").asString(), event.path("duration").asDouble(), warnings);
    }
    private tools.jackson.databind.JsonNode exchange(String id, Map<String, Object> command, Consumer<Progress> progress) throws Exception {
        if(Thread.currentThread().isInterrupted())throw new InterruptedException("Обработка отменена.");
        start();
        if(Thread.currentThread().isInterrupted()){invalidate(process);throw new InterruptedException("Обработка отменена.");}
        var running = process;
        var done = new AtomicBoolean(false);
        var timeout = deadlines.schedule(() -> { if (!done.get()) invalidate(running); }, "resemble-enhance".equals(command.get("modelId")) ? 360 : 15, TimeUnit.MINUTES);
        try {
            writer.write(json.writeValueAsString(command)); writer.newLine(); writer.flush();
            for (String line; (line = reader.readLine()) != null;) {
                var event = json.readTree(line);
                if (!id.equals(event.path("id").asString(""))) continue;
                switch (event.path("event").asString("")) {
                    case "progress" -> progress.accept(new Progress(event.path("stage").asString(), event.path("part").asInt(), event.path("total").asInt()));
                    case "failed" -> throw new IOException(event.path("error").asString("Python не смог выполнить обработку."));
                    case "completed" -> { return event; }
                    default -> { }
                }
            }
            throw new IOException("Python завершился или превысил время ожидания. Повторите обработку.");
        } catch (Exception error) { invalidate(running); throw error; }
        finally { done.set(true); timeout.cancel(false); }
    }
    private static void terminate(Process process) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); }
    private void invalidate(Process running) {
        if (running == null) return;
        synchronized (lifecycle) { if (process == running) process = null; }
        terminate(running);
    }
    @Override public void cancelCurrent(){invalidate(process);}
    @Override public boolean isAlive() { var running = process; return running != null && running.isAlive(); }
    @PreDestroy @Override public void close() {
        deadlines.shutdownNow();
        var running = process;
        synchronized (lifecycle) { if (process == running) process = null; }
        if (running != null) { running.descendants().forEach(ProcessHandle::destroy); running.destroy(); try { if (!running.waitFor(3, TimeUnit.SECONDS)) terminate(running); } catch (InterruptedException e) { Thread.currentThread().interrupt(); terminate(running); } }
    }
}
