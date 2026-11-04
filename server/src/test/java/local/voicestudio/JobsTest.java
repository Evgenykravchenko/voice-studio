package local.voicestudio;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.json.JsonMapper;
import java.nio.file.*;
import java.io.IOException;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.web.server.ResponseStatusException;
import static org.junit.jupiter.api.Assertions.*;

class JobsTest {
    @TempDir Path root;
    private StudioPaths paths() throws IOException {
        var paths = new StudioPaths(root);
        Files.createDirectories(paths.profiles().resolve("test-voice"));
        Files.writeString(paths.profiles().resolve("test-voice/profile.json"), "{}");
        return paths;
    }
    private GenerationRequest request(String text) { return new GenerationRequest("scene", "Сцена", text, "test-voice", "calm", "ru", 42L); }
    private Job.Result result(String id) { return new Job.Result(id, "/api/audio/"+id, 1.2, 44100, List.of(.1,.2), 42, .8); }
    private Job await(Jobs jobs, String id) throws Exception {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(4);
        while (System.nanoTime() < deadline) {
            var job = jobs.get(id);
            if (job.status().equals("succeeded") || job.status().equals("failed")) return job;
            Thread.sleep(10);
        }
        throw new AssertionError("Job did not finish");
    }
    @Test void jobsRunSeriallyAndSurviveReload() throws Exception {
        var inFlight = new AtomicInteger(); var maximum = new AtomicInteger();
        SpeechWorker worker = (id, req, progress) -> {
            maximum.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
            progress.accept(new SpeechWorker.Progress("generating", 1, 1));
            Thread.sleep(40); inFlight.decrementAndGet(); return result(id);
        };
        var paths = paths(); var json = JsonMapper.builder().build(); var jobs = new Jobs(paths, json, worker);
        String first;
        try {
            var a = jobs.submit(request("Первое.")); first = a.id(); var b = jobs.submit(request("Второе."));
            assertEquals("succeeded", await(jobs, a.id()).status());
            assertEquals("succeeded", await(jobs, b.id()).status()); assertEquals(1, maximum.get());
        } finally { jobs.stop(); }
        var reopened = new Jobs(paths, json, worker);
        try { assertEquals("Первое.", reopened.get(first).request().text()); assertEquals(2, reopened.list().size()); }
        finally { reopened.stop(); }
    }
    @Test void failureIsReportedAndNextRequestStillWorks() throws Exception {
        var jobs = new Jobs(paths(), JsonMapper.builder().build(), (id, req, progress) -> {
            if (req.text().equals("Плохой")) throw new IOException("Ошибка модели"); return result(id);
        });
        try {
            var failed = await(jobs, jobs.submit(request("Плохой")).id());
            assertEquals("failed", failed.status()); assertEquals("Ошибка модели", failed.error());
            assertEquals("succeeded", await(jobs, jobs.submit(request("Хороший")).id()).status());
            assertThrows(ResponseStatusException.class, () -> jobs.submit(new GenerationRequest("scene", "Сцена", "Текст", "../other", "calm", "ru", null)));
        } finally { jobs.stop(); }
    }
    @Test void interruptedJobIsRecoverableAfterRestart() throws Exception {
        var paths = paths(); var json = JsonMapper.builder().build(); Files.createDirectories(paths.jobs());
        var job = new Job("11111111-1111-1111-1111-111111111111", request("Текст"), "running", "generating", 1, 1, "2026-10-29T00:00:00Z", null, null, null);
        json.writeValue(paths.jobs().resolve(job.id()+".json").toFile(), job);
        var jobs = new Jobs(paths, json, (id, req, progress) -> result(id));
        try { assertEquals("failed", jobs.get(job.id()).status()); assertTrue(jobs.get(job.id()).error().contains("перезапущен")); }
        finally { jobs.stop(); }
    }
    @Test void cancellingQueuedJobImmediatelyFreesCapacity() throws Exception {
        var entered = new CountDownLatch(1); var release = new CountDownLatch(1);
        var calls = new AtomicInteger();
        var jobs = new Jobs(paths(), JsonMapper.builder().build(), (id, req, progress) -> {
            calls.incrementAndGet(); entered.countDown();
            if (!release.await(10, TimeUnit.SECONDS)) throw new IOException("Test worker timed out");
            return result(id);
        });
        try {
            var active = jobs.submit(request("Активное"));
            assertTrue(entered.await(2, TimeUnit.SECONDS));
            var pending = new java.util.ArrayList<Job>();
            for (int i = 0; i < 4; i++) pending.add(jobs.submit(request("Ожидающее " + i)));
            var full = assertThrows(ResponseStatusException.class, () -> jobs.submit(request("Не помещается")));
            assertEquals(429, full.getStatusCode().value());
            var cancelled = pending.removeLast();
            assertEquals("cancelled", jobs.cancel(cancelled.id()).status());
            var replacement = assertDoesNotThrow(() -> jobs.submit(request("После отмены")));
            release.countDown();
            assertEquals("succeeded", await(jobs, active.id()).status());
            for (var job : pending) assertEquals("succeeded", await(jobs, job.id()).status());
            assertEquals("succeeded", await(jobs, replacement.id()).status());
            assertEquals("cancelled", jobs.get(cancelled.id()).status());
            assertEquals(5, calls.get());
        } finally { release.countDown(); jobs.stop(); }
    }
    @Test void recordingPagesSearchAllPersistedJobsBeyondTheBootstrapWindow() throws Exception {
        var paths=paths();var json=JsonMapper.builder().build();Files.createDirectories(paths.jobs());
        for(int i=0;i<130;i++) {
            var id=new java.util.UUID(0,i+1).toString();var source=i==0?"Точный текст с ё":"Ordinary text";
            var req=new GenerationRequest("scene",String.format("Archive %03d",i),source,"test-voice","calm","ru",42L);
            var job=new Job(id,req,"succeeded","done",1,1,"2026-10-29T00:00:00Z","2026-10-29T00:01:00Z",null,result(id));
            json.writeValue(paths.jobs().resolve(id+".json").toFile(),job);
        }
        var failedId=java.util.UUID.randomUUID().toString();json.writeValue(paths.jobs().resolve(failedId+".json").toFile(),new Job(failedId,request("Failed"),"failed","failed",0,0,"2026-10-30T00:00:00Z",null,"failure",null));
        var jobs=new Jobs(paths,json,(id,req,p)->result(id));
        try {
            assertEquals(100,jobs.list().size());var first=jobs.recordings("",1,12);assertEquals(130,first.total());assertEquals(12,first.items().size());assertEquals(new java.util.UUID(0,130).toString(),first.items().getFirst().id());
            var all=new java.util.HashSet<String>();for(int page=1;page<=11;page++)for(var item:jobs.recordings("",page,12).items())assertTrue(all.add(item.id()));assertEquals(130,all.size());
            assertEquals(1,jobs.recordings("ARCHIVE 000",1,6).total());assertEquals(new java.util.UUID(0,1).toString(),jobs.recordings("ТОЧНЫЙ ТЕКСТ С Е",1,6).items().getFirst().id());
            assertEquals(List.of(),jobs.recordings("",Integer.MAX_VALUE,24).items());assertEquals(0,jobs.recordings("not present",1,24).total());
            assertThrows(ResponseStatusException.class,()->jobs.recordings("",0,12));assertThrows(ResponseStatusException.class,()->jobs.recordings("",1,100000));assertThrows(ResponseStatusException.class,()->jobs.recordings("x".repeat(201),1,12));
        }finally{jobs.stop();}
    }
}
