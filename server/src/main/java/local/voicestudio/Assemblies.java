package local.voicestudio;

import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.sql.SQLException;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import javax.sound.sampled.AudioSystem;
import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Service;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

/** Frozen montage jobs use only local, registered takes. Original audio is never edited. */
@Service
public class Assemblies {
    public record Clip(String sceneId,String sourceId,String path,double start,double end,double gap,double gainDb,long bytes,long modified) {}
    public record Manifest(List<Clip> clips,boolean leveling,boolean softEdges) {}
    public record Span(String sceneId,String sourceId,double start,double end,double trimStart,double trimEnd,double appliedGainDb) {}
    public record Result(double duration,int sampleRate,List<Double> peaks,List<Span> spans) {}
    public record Task(String id,String projectId,String fingerprint,String status,String createdAt,String error,Result result) {}
    public record Request(long revision) {}
    private final StudioPaths paths; private final Projects projects; private final Jobs jobs; private final ObjectMapper json;
    private final Map<String,Task> tasks=new ConcurrentHashMap<>();
    private final ThreadPoolExecutor executor=new ThreadPoolExecutor(1,1,0,TimeUnit.SECONDS,new ArrayBlockingQueue<>(2));
    private volatile Process process;
    public Assemblies(StudioPaths paths,Projects projects,Jobs jobs,ObjectMapper json) throws IOException {
        this.paths=paths;this.projects=projects;this.jobs=jobs;this.json=json;Files.createDirectories(base());
        try(var folders=Files.list(base())) {for(var folder:folders.filter(Files::isDirectory).toList()) {
            var file=folder.resolve("job.json");if(!Files.isRegularFile(file))continue;
            try{var task=json.readValue(file.toFile(),Task.class);if(!List.of("succeeded","failed").contains(task.status()))task=new Task(task.id(),task.projectId(),task.fingerprint(),"failed",task.createdAt(),"Сборка прервана перезапуском. Повторите её.",null);tasks.put(task.id(),task);persist(task);}catch(Exception ignored){System.err.println("Skipping invalid montage job");}
        }}
    }
    private Path base(){return paths.root().resolve("data/studio/assemblies");}
    private Path folder(String id){if(!id.matches("[0-9a-f-]{36}"))throw new ResponseStatusException(HttpStatus.NOT_FOUND);return base().resolve(id);}
    public Task get(String projectId,String id){var task=tasks.get(id);if(task==null || !task.projectId().equals(projectId))throw new ResponseStatusException(HttpStatus.NOT_FOUND);return task;}
    private ResponseStatusException bad(String message){return new ResponseStatusException(HttpStatus.BAD_REQUEST,message);}
    private Manifest manifest(ProjectDocument project) throws IOException {
        var clips=new ArrayList<Clip>();var mix=project.mix();double total=0;
        for(var scene:project.scenes()) {
            var assembly=scene.assembly();if(assembly!=null && Boolean.TRUE.equals(assembly.excluded()))continue;
            String sourceId=scene.selectedTakeId();Path source;
            if(sourceId!=null){var job=jobs.get(sourceId);if(!job.status().equals("succeeded"))throw bad("Сцена «"+scene.title()+"» ещё не готова.");source=paths.audio().resolve(sourceId+".wav");}
            else if(scene.audioIndex()!=null){sourceId="demo-"+scene.audioIndex();source=paths.sampleAudio(scene.audioIndex());}
            else throw bad("Нет записи в сцене «"+scene.title()+"». Создайте озвучку или исключите сцену из итога.");
            if(!Files.isRegularFile(source))throw bad("Не найден аудиофайл сцены «"+scene.title()+"».");
            double duration;
            try(var audio=AudioSystem.getAudioInputStream(source.toFile())){duration=audio.getFrameLength()/audio.getFormat().getFrameRate();}catch(Exception e){throw bad("Не удалось прочитать запись сцены «"+scene.title()+"».");}
            var edit=assembly!=null && assembly.edits()!=null?assembly.edits().get(sourceId):null;
            double start=edit==null?0:edit.start(),end=edit==null || edit.end()==null?duration:edit.end(),gain=edit==null || edit.gainDb()==null?0:edit.gainDb();
            double gap=assembly!=null && assembly.pauseAfter()!=null?assembly.pauseAfter():mix!=null && mix.gapSeconds()!=null?mix.gapSeconds():.25;
            if(!Double.isFinite(start+end+gain+gap) || start<0 || end-start<.08-1e-6 || end>duration+.025 || gain< -18 || gain>12 || gap<0 || gap>5)throw bad("Проверьте границы и громкость сцены «"+scene.title()+"».");
            end=Math.min(end,duration);total+=end-start+gap;if(total>7200)throw bad("Итоговая запись должна быть короче двух часов.");
            clips.add(new Clip(scene.id(),sourceId,source.toAbsolutePath().toString(),start,end,gap,gain,Files.size(source),Files.getLastModifiedTime(source).toMillis()));
        }
        if(clips.isEmpty())throw bad("Включите хотя бы одну сцену с записью.");
        var last=clips.removeLast();clips.add(new Clip(last.sceneId(),last.sourceId(),last.path(),last.start(),last.end(),0,last.gainDb(),last.bytes(),last.modified()));
        return new Manifest(clips,mix==null || !Boolean.FALSE.equals(mix.leveling()),mix==null || !Boolean.FALSE.equals(mix.softEdges()));
    }
    public synchronized Task submit(String projectId,long revision) throws Exception {
        var saved=projects.get(projectId);if(revision!=saved.revision())throw new ResponseStatusException(HttpStatus.CONFLICT,"Проект изменился. Дождитесь сохранения и повторите сборку.");
        var manifest=manifest(saved.project());var bytes=json.writeValueAsBytes(manifest);
        var fingerprint=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        for(var task:tasks.values())if(task.projectId().equals(projectId) && task.fingerprint().equals(fingerprint) && (!task.status().equals("failed")) && (!task.status().equals("succeeded") || Files.isRegularFile(folder(task.id()).resolve("master.wav")) && Files.isRegularFile(folder(task.id()).resolve("master.mp3"))))return task;
        var id=UUID.randomUUID().toString();var task=new Task(id,projectId,fingerprint,"queued",Instant.now().toString(),null,null);
        Files.createDirectories(folder(id));Files.write(folder(id).resolve("manifest.json"),bytes);persist(task);tasks.put(id,task);
        try{executor.execute(()->run(id));}catch(RejectedExecutionException e){update(new Task(id,projectId,fingerprint,"failed",task.createdAt(),"Очередь сборки заполнена. Повторите позже.",null));throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS,"Очередь сборки заполнена.");}
        return task;
    }
    private void run(String id){var task=tasks.get(id);try {
        update(new Task(id,task.projectId(),task.fingerprint(),"running",task.createdAt(),null,null));
        var builder=new ProcessBuilder(paths.root().resolve(".venv/bin/python").toString(),"-u","-m","voice_cloner.assembly",folder(id).resolve("manifest.json").toString());builder.directory(paths.root().toFile());paths.configurePython(builder);builder.redirectOutput(folder(id).resolve("progress.log").toFile());builder.redirectError(folder(id).resolve("error.log").toFile());
        process=builder.start();if(!process.waitFor(10,TimeUnit.MINUTES)){process.descendants().forEach(ProcessHandle::destroyForcibly);process.destroyForcibly();throw new IOException("Сборка превысила время ожидания.");}
        if(process.exitValue()!=0)throw new IOException("Не удалось собрать аудио. Проверьте записи, свободное место и повторите.");
        var result=json.readValue(folder(id).resolve("result.json").toFile(),Result.class);
        update(new Task(id,task.projectId(),task.fingerprint(),"succeeded",task.createdAt(),null,result));
    }catch(Exception e){update(new Task(id,task.projectId(),task.fingerprint(),"failed",task.createdAt(),e.getMessage(),null));}finally{var running=process;if(running!=null && running.isAlive()){running.descendants().forEach(ProcessHandle::destroyForcibly);running.destroyForcibly();}process=null;}}
    private void persist(Task task)throws IOException{var tmp=folder(task.id()).resolve("job.tmp");json.writeValue(tmp.toFile(),task);Files.move(tmp,folder(task.id()).resolve("job.json"),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
    private void update(Task task){try{persist(task);tasks.put(task.id(),task);}catch(IOException e){tasks.put(task.id(),new Task(task.id(),task.projectId(),task.fingerprint(),"failed",task.createdAt(),"Не удалось сохранить сборку.",null));}}
    public Path audio(String projectId,String id,String format){if(!List.of("wav","mp3").contains(format) || !get(projectId,id).status().equals("succeeded"))throw new ResponseStatusException(HttpStatus.NOT_FOUND);var file=folder(id).resolve("master."+format);if(!Files.isRegularFile(file))throw new ResponseStatusException(HttpStatus.NOT_FOUND);return file;}
    @PreDestroy public void close(){executor.shutdownNow();var running=process;if(running!=null){running.descendants().forEach(ProcessHandle::destroyForcibly);running.destroyForcibly();}}
}
