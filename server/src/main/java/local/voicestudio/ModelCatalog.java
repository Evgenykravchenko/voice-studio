package local.voicestudio;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import org.springframework.stereotype.Service;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.*;
import tools.jackson.databind.node.ObjectNode;
import jakarta.annotation.PreDestroy;

/** Downloads only pinned catalog artifacts, without loading inference models. */
@Service
public class ModelCatalog {
    public record Transfer(String status, String stage, long downloadedBytes, long totalBytes, String error) {}
    private final StudioPaths paths;
    private final ObjectMapper json;
    private final Map<String, Transfer> transfers = new ConcurrentHashMap<>();
    private final Map<String, Integer> attempts = new HashMap<>();
    private final Map<String, Process> processes = new ConcurrentHashMap<>();
    private final ExecutorService queue = Executors.newSingleThreadExecutor();
    private volatile JsonNode cached;
    private volatile long checked;
    private volatile boolean closing;

    public ModelCatalog(StudioPaths paths, ObjectMapper json) throws IOException {
        this.paths = paths; this.json = json;
        Files.createDirectories(directory());
        try (var files = Files.list(directory())) {
            for (var file : files.filter(p -> p.getFileName().toString().matches("[a-z0-9-]+\\.transfer\\.json")).toList()) {
                try {
                    var value = json.readValue(file.toFile(), Transfer.class);
                    var id = file.getFileName().toString().replace(".transfer.json", "");
                    if (List.of("queued", "downloading", "verifying", "preparing").contains(value.status())) value = new Transfer("cancelled", "cancelled", value.downloadedBytes(), value.totalBytes(), null);
                    transfers.put(id, value);
                } catch (RuntimeException ignored) { }
            }
        }
    }
    private Path directory() { return paths.root().resolve("data/studio/models"); }
    private ProcessBuilder command(String action, String id) throws IOException {
        var args = new ArrayList<>(List.of(paths.root().resolve(".venv/bin/python").toString(), "-u", "-m", "voice_cloner.models", action));
        if (id != null) args.add(id);
        args.addAll(List.of("--root", paths.root().toString()));
        var logs = paths.root().resolve(".runtime/logs"); Files.createDirectories(logs);
        var builder = new ProcessBuilder(args).directory(paths.root().toFile());
        paths.configurePython(builder);
        builder.redirectError(ProcessBuilder.Redirect.appendTo(logs.resolve("model-downloads.log").toFile()));
        return builder;
    }
    private JsonNode call(String action, String id) throws IOException {
        var process = command(action, id).start();
        var output = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readAllBytes(); } catch (IOException e) { throw new UncheckedIOException(e); }
        });
        try {
            if (!process.waitFor(10, TimeUnit.SECONDS)) throw new IOException("Каталог моделей не ответил вовремя.");
            var result = json.readTree(output.get(2, TimeUnit.SECONDS));
            if (process.exitValue() != 0) throw new ResponseStatusException(HttpStatus.CONFLICT, result.path("error").asString("Не удалось выбрать модель."));
            return result;
        } catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new IOException(e); }
        catch (ExecutionException | TimeoutException e) { throw new IOException("Не удалось прочитать каталог моделей.", e); }
        finally { if (process.isAlive()) terminate(process); }
    }
    private synchronized JsonNode inventory() throws IOException {
        if (cached == null || System.currentTimeMillis() - checked > 2000) { cached = call("list", null); checked = System.currentTimeMillis(); }
        return cached;
    }
    public JsonNode list() throws IOException {
        var result = (ObjectNode) inventory().deepCopy();
        for (var value : result.path("models")) {
            var model = (ObjectNode) value;
            var transfer = transfers.get(model.path("id").asString());
            if (model.path("integration").asString().equals("ready") ? model.path("ready").asBoolean() : model.path("installed").asBoolean()) model.put("status", "installed");
            else model.put("status", transfer == null ? "available" : transfer.status().equals("installed") ? "available" : transfer.status());
            if (transfer != null) model.set("transfer", json.valueToTree(transfer));
        }
        return result;
    }
    private JsonNode require(String id) throws IOException {
        if (id != null && id.matches("[a-z0-9-]{1,64}")) for (var model : inventory().path("models")) if (id.equals(model.path("id").asString())) return model;
        throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Модель не найдена в каталоге.");
    }
    public synchronized Transfer download(String id) throws IOException {
        var model = require(id);
        if (!model.path("downloadable").asBoolean(true)) throw new ResponseStatusException(HttpStatus.CONFLICT, "Модель устанавливается со страницы автора.");
        var current = transfers.get(id);
        if (current != null && List.of("queued", "downloading", "verifying", "preparing").contains(current.status())) return current;
        if (model.path("integration").asString().equals("ready") ? model.path("ready").asBoolean() : model.path("installed").asBoolean()) return new Transfer("installed", "installed", model.path("sizeBytes").asLong(), model.path("sizeBytes").asLong(), null);
        var value = new Transfer("queued", "queued", model.path("downloadedBytes").asLong(), model.path("sizeBytes").asLong(), null);
        update(id, value);
        int attempt = attempts.merge(id, 1, Integer::sum);
        queue.execute(() -> run(id, attempt, "download"));
        return value;
    }
    private void run(String id, int attempt, String operation) {
        Process process;
        try {
            synchronized (this) {
                if (closing || !Objects.equals(attempts.get(id), attempt) || !transfers.get(id).status().equals("queued")) return;
                process = command(operation, id).start(); processes.put(id, process);
                var old = transfers.get(id); update(id, new Transfer("downloading", "downloading", old.downloadedBytes(), old.totalBytes(), null));
            }
            try (var reader = process.inputReader()) {
                for (String line; (line = reader.readLine()) != null;) {
                    var event = json.readTree(line);
                    synchronized (this) {
                        if (closing || !Objects.equals(attempts.get(id), attempt) || transfers.get(id).status().equals("cancelled")) continue;
                        var stage = event.path("stage").asString();
                        var old = transfers.get(id);
                        update(id, new Transfer(stage, stage, event.path("downloadedBytes").asLong(old.downloadedBytes()), event.path("totalBytes").asLong(old.totalBytes()), event.path("error").asString(null)));
                    }
                }
            }
            var code = process.waitFor();
            synchronized (this) {
                var old = transfers.get(id);
                if (!closing && Objects.equals(attempts.get(id), attempt) && !old.status().equals("cancelled") && (code != 0 || !old.status().equals("installed"))) update(id, new Transfer("failed", "failed", old.downloadedBytes(), old.totalBytes(), old.error() == null ? "Скачивание прервано. Проверьте подключение и повторите." : old.error()));
                cached = null;
            }
        } catch (Exception e) {
            synchronized (this) {
                var old = transfers.get(id);
                if (!closing && Objects.equals(attempts.get(id), attempt) && !old.status().equals("cancelled")) update(id, new Transfer("failed", "failed", old.downloadedBytes(), old.totalBytes(), "Не удалось скачать модель. Проверьте подключение и свободное место."));
            }
        } finally { var running = processes.remove(id); if (running != null && running.isAlive()) terminate(running); }
    }
    public boolean transferActive(String id){var transfer=transfers.get(id);return transfer!=null && List.of("queued","downloading","verifying","preparing").contains(transfer.status());}
    public JsonNode manifest(String id) throws IOException {
        var model=require(id);
        if(!model.path("gated").asBoolean())throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Для этой модели используйте установку из каталога.");
        return call("manifest",id);
    }
    public synchronized Transfer importModel(String id) throws IOException {
        var model=require(id);
        if(!model.path("gated").asBoolean())throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Для этой модели используйте установку из каталога.");
        var old=transfers.get(id);
        if(old!=null && List.of("queued","downloading","verifying","preparing").contains(old.status()))return old;
        var value=new Transfer("queued","queued",0,model.path("sizeBytes").asLong(),null);update(id,value);
        int attempt=attempts.merge(id,1,Integer::sum);queue.execute(()->run(id,attempt,"import"));return value;
    }
    public synchronized void cancel(String id) throws IOException {
        require(id);
        var old = transfers.get(id);
        if (old == null || !List.of("queued", "downloading", "verifying", "preparing").contains(old.status())) return;
        attempts.merge(id, 1, Integer::sum);
        update(id, new Transfer("cancelled", "cancelled", old.downloadedBytes(), old.totalBytes(), null));
        var process = processes.get(id); if (process != null) terminate(process);
        cached = null;
    }
    public synchronized void select(String id) throws IOException { require(id); call("select", id); cached = null; }
    public String transcriptionModelId(String language) throws IOException {
        for(var model:inventory().path("models")) {
            if(!model.path("task").asString().equals("transcription") || !model.path("active").asBoolean() || !model.path("ready").asBoolean())continue;
            boolean supported=language.equals("auto");
            for(var candidate:model.path("languages"))if(candidate.asString().equals(language))supported=true;
            if(!supported)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Выбранная модель распознавания не поддерживает язык записи. Выберите другую модель в разделе «Модели».");
            return model.path("id").asString();
        }
        throw new ResponseStatusException(HttpStatus.CONFLICT,"Сначала установите и выберите модель распознавания в разделе «Модели».");
    }
    public GenerationRequest prepare(GenerationRequest request) throws IOException {
        JsonNode model = null;
        if (request.modelId() != null) model = require(request.modelId());
        else for (var candidate : inventory().path("models")) if (candidate.path("task").asString().equals("synthesis") && candidate.path("active").asBoolean()) { model = candidate; break; }
        if (model == null || model.path("task").asString().equals("transcription") || !model.path("ready").asBoolean()) throw new ResponseStatusException(HttpStatus.CONFLICT, "Сначала установите модель озвучки в разделе «Модели».");
        var task=model.path("task").asString();
        boolean needsAudio=task.equals("conversion") || model.path("adapter").asString().equals("enhance");
        if (needsAudio && (request.sourceId()==null || !Files.isRegularFile(paths.root().resolve("data/studio/inputs").resolve(request.sourceId()).resolve("source")))) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Загрузите исходную запись.");
        if (!needsAudio && request.text().isBlank()) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Введите текст для озвучки.");
        var mode = model.path("synthesisMode").asString("clone");
        if(request.voiceMode()!=null){
            boolean supported=request.voiceMode().equals(mode);
            for(var candidate:model.path("synthesisModes"))if(candidate.asString().equals(request.voiceMode()))supported=true;
            if(!supported)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Эта модель не поддерживает выбранный способ создания голоса.");
            mode=request.voiceMode();
        }
        String preset = null;
        if (mode.equals("clone") && request.voiceId() == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Выберите голосовой профиль.");
        if (mode.equals("preset")) {
            preset = request.presetVoice() == null ? model.path("presetVoices").get(0).asString() : request.presetVoice();
            boolean found = false; for (var value : model.path("presetVoices")) if (value.asString().equals(preset)) found = true;
            if (!found) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Выберите готовый голос из списка.");
        }
        if (mode.equals("design") && (request.voiceDescription() == null || request.voiceDescription().isBlank())) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Опишите голос, который нужно создать.");
        if (model.path("markup").asString("plain").equals("plain") && request.text().replaceAll("(?i)\\[pause:\\d+(?:[.,]\\d+)?\\]", "").matches("(?s).*\\[[^]]*\\].*")) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Уберите теги эмоций в скобках: они предназначены для Fish. Паузы [pause:0.5] работают во всех моделях.");
        boolean emotionSupported = false; for (var feature : model.path("features")) if (feature.asString().equals("emotion")) emotionSupported = true;
        String language = (model.path("id").asString().equals("fish-s2-pro") || model.path("languageMode").asString().equals("text")) ? "auto" : request.language();
        if(language.equals("auto") && model.has("autoLanguage") && !model.path("autoLanguage").asBoolean())throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Для этой модели выберите язык озвучки явно.");
        if(!language.equals("auto") && model.path("languages").isArray() && model.path("languages").size()>0){
            boolean supported=false;for(var value:model.path("languages"))if(value.asString().equals(language))supported=true;
            if(!supported)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Выбранная модель не поддерживает этот язык. Измените язык озвучки.");
        }
        if (model.path("runtime").asString().equals("piper")) {
            if (!language.equals("ru") && !language.equals("auto")) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Этот голос Piper поддерживает русский язык.");
            language = "ru";
        }
        return new GenerationRequest(request.sceneId(),request.title(),request.text(),mode.equals("clone") ? request.voiceId() : null,emotionSupported ? request.emotion() : "calm",language,model.path("runtime").asString().equals("piper") ? null : request.seed(),model.path("id").asString(),preset,mode.equals("design") ? request.voiceDescription() : null,request.sourceId(),request.durationSeconds(),request.projectId(),mode);
    }
    private static void terminate(Process process) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); }
    private void update(String id, Transfer transfer) {
        transfers.put(id, transfer);
        try {
            var temporary = directory().resolve(id + ".transfer.tmp");
            json.writeValue(temporary.toFile(), transfer);
            Files.move(temporary, directory().resolve(id + ".transfer.json"), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException | RuntimeException e) { transfers.put(id, new Transfer("failed", "failed", transfer.downloadedBytes(), transfer.totalBytes(), "Не удалось сохранить состояние загрузки. Проверьте свободное место.")); }
    }
    @PreDestroy public void stop() {
        closing = true; queue.shutdownNow(); processes.values().forEach(ModelCatalog::terminate);
        try { queue.awaitTermination(3, TimeUnit.SECONDS); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
