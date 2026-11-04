package local.voicestudio;

import java.io.IOException;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

@Service
public class VoiceProfiles {
    public record Voice(String id, String name, String engine, String language, String referenceText, double duration, String referenceUrl) {}
    public record SaveVoice(String name, String transcript) {}
    private final StudioPaths paths;
    private final ObjectMapper json;
    private final SpeechWorker worker;
    private final Jobs queue;
    private final ModelCatalog modelCatalog;
    private final Path imports;
    private final ConcurrentMap<String, VoiceImport> tasks = new ConcurrentHashMap<>();
    public VoiceProfiles(StudioPaths paths, ObjectMapper json, SpeechWorker worker, Jobs queue) throws IOException { this(paths,json,worker,queue,null); }
    @Autowired public VoiceProfiles(StudioPaths paths, ObjectMapper json, SpeechWorker worker, Jobs queue, ModelCatalog modelCatalog) throws IOException {
        this.paths=paths; this.json=json; this.worker=worker; this.queue=queue; this.modelCatalog=modelCatalog;
        Files.createDirectories(paths.root().resolve(".runtime/uploads"));
        imports=paths.root().resolve("data/studio/voice-imports"); Files.createDirectories(imports); Files.createDirectories(paths.profiles());
        try(var dirs=Files.list(paths.profiles())) {
            for(var dir:dirs.filter(p->p.getFileName().toString().matches("\\.deleting-[0-9a-f-]{36}")).toList()) {
                try {deleteTree(dir);} catch(IOException e) {System.err.println("Could not finish voice deletion: "+dir.getFileName());}
            }
        }
        try (var files=Files.list(imports)) {
            for (var file:files.filter(p->p.getFileName().toString().endsWith(".json")).toList()) {
                try {
                    var task=json.readValue(file.toFile(),VoiceImport.class);
                    if (!task.id().matches("[0-9a-f-]{36}")) continue;
                    // A profile rename may have completed just before a crash; recover that commit.
                    if (Files.isRegularFile(paths.profiles().resolve("voice-"+task.id()).resolve("profile.json"))) task=task.saved("voice-"+task.id(),task.name(),task.transcript());
                    else if(task.status().equals("saved")) { Files.deleteIfExists(file); continue; }
                    else if (task.status().equals("queued") || task.status().equals("running")) task=task.failed("Подготовка прервана перезапуском. Загрузите запись ещё раз.");
                    tasks.put(task.id(),task); persist(task);
                    if (task.status().equals("failed")) clean(task.id());
                } catch (RuntimeException | IOException e) { System.err.println("Skipping invalid voice import: "+file.getFileName()); }
            }
        }
    }
    private ResponseStatusException bad(String message) { return new ResponseStatusException(HttpStatus.BAD_REQUEST,message); }
    private String name(String value) { if(value==null || value.strip().isEmpty() || value.strip().length()>80) throw bad("Введите имя голоса: от 1 до 80 символов."); return value.strip(); }
    public List<Voice> list() throws IOException {
        var result=new ArrayList<Voice>();
        try(var dirs=Files.list(paths.profiles())) {
            for(var dir:dirs.filter(Files::isDirectory).toList()) {
                var id=dir.getFileName().toString();
                if(!id.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,63}") || !Files.isRegularFile(dir.resolve("profile.json")) || !Files.isRegularFile(dir.resolve("reference.wav"))) continue;
                try {
                    var data=json.readTree(dir.resolve("profile.json").toFile());
                    result.add(new Voice(id,data.path("name").asString(id),"fish-s2-pro",data.path("language").asString("ru"),data.path("reference_text").asString(""),data.path("clip_duration_seconds").asDouble(),"/api/voices/"+id+"/reference"));
                } catch(RuntimeException e) { System.err.println("Skipping invalid profile: "+id); }
            }
        }
        return result.stream().sorted(Comparator.comparing(Voice::name,String.CASE_INSENSITIVE_ORDER)).toList();
    }
    public List<VoiceImport> tasks() { return tasks.values().stream().filter(t->!t.status().equals("saved")).sorted(Comparator.comparing(VoiceImport::createdAt).reversed()).limit(20).toList(); }
    public VoiceImport get(String id) { var task=tasks.get(id); if(task==null) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Подготовка голоса не найдена."); return task; }
    public synchronized VoiceImport upload(MultipartFile file, String displayName, double start, double duration, String language) throws IOException {
        displayName=name(displayName);
        if(!Double.isFinite(start) || start<0 || start>86400 || !Double.isFinite(duration) || duration<5 || duration>30) throw bad("Выберите фрагмент от 5 до 30 секунд и корректное начало.");
        if(language==null || !language.matches("auto|[a-z]{2,3}(?:-[A-Za-z0-9]+)?")) throw bad("Выберите язык записи.");
        if(file.isEmpty() || file.getSize()>50L*1024*1024) throw bad("Выберите аудиофайл размером до 50 МБ.");
        var filename=Objects.toString(file.getOriginalFilename(),"").toLowerCase(Locale.ROOT);
        if(!filename.matches(".*\\.(wav|mp3|m4a|flac|ogg|aac|aiff|aif|opus|webm)$")) throw bad("Поддерживаются WAV, MP3, M4A, FLAC, OGG, AAC, AIFF, Opus и WebM.");
        if(tasks.values().stream().filter(t->!t.status().equals("saved") && !t.status().equals("failed")).count()>=5) throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS,"Завершите или отмените предыдущие профили.");
        var modelId=modelCatalog==null?null:modelCatalog.transcriptionModelId(language);
        var id=UUID.randomUUID().toString(); var dir=imports.resolve(id); Files.createDirectory(dir);
        var task=new VoiceImport(id,displayName,language,start,duration,"queued","queued","",0,List.of(),null,Instant.now().toString(),null,modelId);
        try {
            file.transferTo(dir.resolve("source")); persist(task); tasks.put(id,task);
            queue.enqueue(()->prepare(id));
            return task;
        } catch(RejectedExecutionException e) {
            tasks.remove(id); clean(id); Files.deleteIfExists(imports.resolve(id+".json"));
            throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS,"Очередь заполнена. Попробуйте после завершения обработки.");
        } catch(IOException | RuntimeException e) { tasks.remove(id); clean(id); Files.deleteIfExists(imports.resolve(id+".json")); throw e; }
    }
    private void prepare(String id) {
        try {
            update(get(id).progress("starting")); var task=get(id);
            var result=worker.prepareVoice(id,task.start(),task.requestedDuration(),task.language(),task.modelId(),p->update(get(id).progress(p.stage())));
            if(result.transcript()==null || result.transcript().isBlank() || result.transcript().length()>5000 || result.duration()<5 || result.duration()>30.1 || !Files.isRegularFile(imports.resolve(id).resolve("reference.wav"))) throw new IOException("Не удалось подготовить эталон голоса.");
            Files.deleteIfExists(imports.resolve(id).resolve("source"));
            update(get(id).ready(result));
        } catch(Exception e) { update(get(id).failed(e.getMessage()==null?"Не удалось подготовить голос.":e.getMessage())); try { clean(id); } catch(IOException ignored) {} }
    }
    public synchronized VoiceImport save(String id, SaveVoice body) throws IOException {
        var task=get(id);
        if(task.status().equals("saved")) return task;
        if(!task.status().equals("ready")) throw new ResponseStatusException(HttpStatus.CONFLICT,"Дождитесь подготовки эталона.");
        var displayName=name(body.name()); var text=body.transcript();
        if(text==null || text.isBlank() || text.length()>5000) throw bad("Введите точную расшифровку записи: от 1 до 5000 символов.");
        var profileId="voice-"+id; var dir=imports.resolve(id);
        var metadata=new LinkedHashMap<String,Object>();
        metadata.put("id",profileId); metadata.put("name",displayName); metadata.put("engine","fish-s2-pro"); metadata.put("language",task.language());
        metadata.put("reference_audio","reference.wav"); metadata.put("reference_text",text.strip());
        metadata.put("clip_start_seconds",task.start()); metadata.put("clip_duration_seconds",task.duration()); metadata.put("created_at",Instant.now().toString());
        json.writeValue(dir.resolve("profile.json").toFile(),metadata);
        Files.move(dir,paths.profiles().resolve(profileId),StandardCopyOption.ATOMIC_MOVE);
        var saved=task.saved(profileId,displayName,text.strip()); tasks.put(id,saved); persist(saved); return saved;
    }
    public synchronized void discard(String id) throws IOException {
        var task=get(id);
        if(task.status().equals("queued") || task.status().equals("running")) throw new ResponseStatusException(HttpStatus.CONFLICT,"Дождитесь завершения обработки.");
        if(task.status().equals("saved")) throw new ResponseStatusException(HttpStatus.CONFLICT,"Голос уже сохранён.");
        clean(id); Files.deleteIfExists(imports.resolve(id+".json")); tasks.remove(id);
    }
    public synchronized void delete(String id) throws IOException {
        if(id==null || !id.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,63}")) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Голос не найден.");
        var directory=paths.profiles().resolve(id);
        var removed=paths.profiles().resolve(".deleting-"+UUID.randomUUID());
        // Share submit's monitor: a queued job must never lose its reference between
        // profile validation and enqueue. A new job sees either the profile or no profile.
        synchronized(queue) {
            if(!Files.isDirectory(directory,LinkOption.NOFOLLOW_LINKS) || !Files.isRegularFile(directory.resolve("profile.json"),LinkOption.NOFOLLOW_LINKS)) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Голос не найден.");
            if(queue.usesVoice(id)) throw new ResponseStatusException(HttpStatus.CONFLICT,"Голос используется в очереди или генерации. Дождитесь завершения и повторите удаление.");
            Files.move(directory,removed,StandardCopyOption.ATOMIC_MOVE);
        }
        for(var task:List.copyOf(tasks.values())) if(id.equals(task.voiceId())) {
            Files.deleteIfExists(imports.resolve(task.id()+".json")); tasks.remove(task.id());
        }
        deleteTree(removed);
    }
    public Path reference(String id, boolean draft) {
        Path file;
        if(draft) { var task=get(id); if(!task.status().equals("ready")) throw new ResponseStatusException(HttpStatus.NOT_FOUND); file=imports.resolve(id).resolve("reference.wav"); }
        else { if(!id.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,63}")) throw new ResponseStatusException(HttpStatus.NOT_FOUND); file=paths.profiles().resolve(id).resolve("reference.wav"); }
        if(!Files.isRegularFile(file)) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Эталон не найден."); return file;
    }
    private synchronized void persist(VoiceImport task) throws IOException { var tmp=imports.resolve(task.id()+".tmp"); json.writeValue(tmp.toFile(),task); Files.move(tmp,imports.resolve(task.id()+".json"),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING); }
    private void update(VoiceImport task) {
        try { persist(task); tasks.put(task.id(),task); }
        catch(IOException e) { tasks.put(task.id(),task.failed("Не удалось сохранить профиль. Проверьте свободное место.")); }
    }
    private void clean(String id) throws IOException {
        deleteTree(imports.resolve(id));
    }
    private void deleteTree(Path dir) throws IOException {
        if(!Files.exists(dir,LinkOption.NOFOLLOW_LINKS)) return;
        try(var files=Files.walk(dir)) { for(var file:files.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(file); }
    }
}
