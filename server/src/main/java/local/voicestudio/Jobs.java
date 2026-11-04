package local.voicestudio;

import java.io.IOException;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;
import jakarta.annotation.PreDestroy;

@Service
public class Jobs {
    public record RecordingPage(List<Job> items, int total, int page, int size) {}
    private final StudioPaths paths;
    private final ObjectMapper json;
    private final SpeechWorker worker;
    private final ConcurrentMap<String, Job> jobs = new ConcurrentHashMap<>();
    // Guarded by this, like submit/cancel and the first step of run.
    private final Map<String, Runnable> pending = new HashMap<>();
    private volatile String activeId;
    private volatile Thread activeThread;
    private final ThreadPoolExecutor executor = new ThreadPoolExecutor(1, 1, 0, TimeUnit.SECONDS, new ArrayBlockingQueue<>(4));

    public Jobs(StudioPaths paths, ObjectMapper json, SpeechWorker worker) throws IOException {
        this.paths = paths; this.json = json; this.worker = worker;
        Files.createDirectories(paths.jobs()); Files.createDirectories(paths.audio());
        try (var files = Files.list(paths.jobs())) {
            for (var file : files.filter(p -> p.getFileName().toString().endsWith(".json")).toList()) {
                try {
                    var job = json.readValue(file.toFile(), Job.class);
                    if (!List.of("succeeded","failed","cancelled").contains(job.status())) job = job.failed("Сервер перезапущен. Создайте дубль ещё раз.");
                    jobs.put(job.id(), job); save(job);
                } catch (RuntimeException | IOException ignored) { System.err.println("Skipping invalid job metadata: " + file.getFileName()); }
            }
        }
    }
    public List<Job> list() { return jobs.values().stream().sorted(Comparator.comparing(Job::createdAt).reversed()).limit(100).toList(); }
    public RecordingPage recordings(String query,int page,int size) {
        if(query==null || query.length()>200 || page<1 || !List.of(6,12,24).contains(size))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Проверьте поиск и размер страницы записей.");
        var needle=query.strip().toLowerCase(Locale.ROOT).replace('ё','е');
        var matches=jobs.values().stream().filter(job->job.status().equals("succeeded") && job.result()!=null)
            .filter(job->needle.isEmpty() || (job.request().title()+" "+job.request().text()).toLowerCase(Locale.ROOT).replace('ё','е').contains(needle))
            .sorted(Comparator.comparing(Job::createdAt).thenComparing(Job::id).reversed()).toList();
        // Do not clamp to the generated-only last page: the UI can append local samples.
        return new RecordingPage(matches.stream().skip(((long)page-1)*size).limit(size).toList(),matches.size(),page,size);
    }
    public List<Job> lookup(List<String> ids) {
        if(ids.size()>100 || ids.stream().anyMatch(id->!id.matches("[0-9a-f-]{36}")))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Неверный список записей.");
        return ids.stream().distinct().map(jobs::get).filter(Objects::nonNull).toList();
    }
    public List<Job> completedForProject(String projectId) {return jobs.values().stream().filter(job->projectId.equals(job.request().projectId()) && job.status().equals("succeeded")).toList();}
    public Job get(String id) {
        var job = jobs.get(id);
        if (job == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Задание не найдено.");
        return job;
    }
    public synchronized Job submit(GenerationRequest request) throws IOException {return submitWithId(UUID.randomUUID().toString(),request);}
    public synchronized Job submitWithId(String id,GenerationRequest request) throws IOException {
        if(!id.matches("[0-9a-f-]{36}") || jobs.containsKey(id))throw new ResponseStatusException(HttpStatus.CONFLICT,"Задание уже существует.");
        if (request.voiceId() != null && ( !request.voiceId().matches("[A-Za-z0-9][A-Za-z0-9_-]{0,63}") || !Files.isRegularFile(paths.profiles().resolve(request.voiceId()).resolve("profile.json")))) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Голосовой профиль не найден.");
        var job = new Job(id, request, "queued", "queued", 0, 0, Instant.now().toString(), null, null, null);
        save(job); jobs.put(id, job);
        Runnable task = () -> run(id); pending.put(id, task);
        try { enqueue(task); }
        catch (RejectedExecutionException e) { pending.remove(id); jobs.remove(id); Files.deleteIfExists(paths.jobs().resolve(id + ".json")); throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS, "Очередь заполнена. Дождитесь завершения текущих заданий."); }
        return job;
    }
    public void enqueue(Runnable task) { executor.execute(task); }
    public boolean usesVoice(String id) {
        return jobs.values().stream().anyMatch(job -> id.equals(job.request().voiceId()) && List.of("queued","running").contains(job.status()));
    }
    private void run(String id) {
        synchronized(this){pending.remove(id);if(!get(id).status().equals("queued"))return;activeId=id;activeThread=Thread.currentThread();update(get(id).progress("starting",0,0));}
        try {
            if(get(id).status().equals("cancelled"))return;
            var result = worker.generate(id, get(id).request(), p -> {if(!get(id).status().equals("cancelled"))update(get(id).progress(p.stage(), p.part(), p.total()));});
            if(!get(id).status().equals("cancelled"))update(get(id).success(result));
        } catch (Exception e) { if(!get(id).status().equals("cancelled"))update(get(id).failed(e.getMessage() == null ? "Не удалось создать озвучку." : e.getMessage())); } finally {activeId=null;activeThread=null;Thread.interrupted();}
    }
    public synchronized Job cancel(String id){
        var job=get(id);if(!List.of("queued","running").contains(job.status()))return job;
        var cancelled=new Job(id,job.request(),"cancelled","cancelled",job.part(),job.total(),job.createdAt(),Instant.now().toString(),null,null);update(cancelled);
        var task=pending.remove(id);if(task!=null)executor.remove(task);
        if(id.equals(activeId)){var thread=activeThread;if(thread!=null)thread.interrupt();worker.cancelCurrent();}return cancelled;
    }
    private synchronized void update(Job job) {
        var current=jobs.get(job.id());if(current!=null && current.status().equals("cancelled") && !job.status().equals("cancelled"))return;
        try { save(job); jobs.put(job.id(), job); }
        catch (IOException e) { jobs.put(job.id(), job.failed("Не удалось сохранить результат. Проверьте свободное место.")); }
    }
    private synchronized void save(Job job) throws IOException {
        var target = paths.jobs().resolve(job.id() + ".json");
        var temporary = target.resolveSibling(job.id() + ".tmp");
        json.writeValue(temporary.toFile(), job);
        Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
    }
    public boolean workerAlive() { return worker.isAlive(); }
    @PreDestroy public void stop() { executor.shutdownNow(); worker.close(); }
}
