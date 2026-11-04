package local.voicestudio;

import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

class VoiceDeletionTest {
    @TempDir Path root;
    void profile(String id) throws Exception {
        var dir=root.resolve("data/profiles").resolve(id);Files.createDirectories(dir);
        Files.writeString(dir.resolve("profile.json"),"{\"name\":\"Test voice\",\"reference_text\":\"Reference text.\"}");
        Files.write(dir.resolve("reference.wav"),new byte[]{1,2,3});
    }
    GenerationRequest request(String voice) {return new GenerationRequest("scene","Scene","Text",voice,"calm","ru",1L);}
    Job.Result result(String id){return new Job.Result(id,"/api/audio/"+id,1,24000,List.of(.1),1,.8);}
    void finished(Jobs jobs,String id) throws Exception {
        long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
        while(System.nanoTime()<deadline){if(jobs.get(id).status().equals("succeeded"))return;Thread.sleep(10);}
        throw new AssertionError("Job did not finish");
    }
    @Test void deletesOnlySelectedProfileAndKeepsOriginalSourceAndGeneratedTakes() throws Exception {
        profile("first");profile("second");var paths=new StudioPaths(root);var json=JsonMapper.builder().build();
        var original=root.resolve("original.wav");Files.write(original,new byte[]{9});
        Files.createSymbolicLink(paths.profiles().resolve("first/original-link"),original);
        var jobs=new Jobs(paths,json,(id,req,progress)->result(id));
        try {
            var job=jobs.submit(request("first"));finished(jobs,job.id());
            Files.write(paths.audio().resolve(job.id()+".wav"),new byte[]{7,8});
            var profiles=new VoiceProfiles(paths,json,(id,req,progress)->result(id),jobs);
            profiles.delete("first");
            assertFalse(Files.exists(paths.profiles().resolve("first")));
            assertTrue(Files.exists(paths.profiles().resolve("second/reference.wav")));
            assertTrue(Files.exists(original));assertEquals(1,profiles.list().size());
            assertEquals("first",jobs.get(job.id()).request().voiceId());
            assertArrayEquals(new byte[]{7,8},Files.readAllBytes(paths.audio().resolve(job.id()+".wav")));
            assertTrue(Files.exists(paths.jobs().resolve(job.id()+".json")));
            assertThrows(ResponseStatusException.class,()->profiles.delete("../second"));
            assertThrows(ResponseStatusException.class,()->profiles.delete("missing"));
            assertThrows(ResponseStatusException.class,()->jobs.submit(request("first")));
            assertEquals(1,new VoiceProfiles(paths,json,(id,req,progress)->result(id),jobs).list().size());
        }finally{jobs.stop();}
    }
    @Test void rejectsDeletionForBothQueuedAndRunningVoices() throws Exception {
        profile("first");profile("second");var paths=new StudioPaths(root);var json=JsonMapper.builder().build();
        var entered=new CountDownLatch(1);var release=new CountDownLatch(1);
        SpeechWorker worker=(id,req,progress)->{entered.countDown();if(!release.await(3,TimeUnit.SECONDS))throw new IllegalStateException("timeout");return result(id);};
        var jobs=new Jobs(paths,json,worker);
        try {
            var profiles=new VoiceProfiles(paths,json,worker,jobs);
            var first=jobs.submit(request("first"));assertTrue(entered.await(1,TimeUnit.SECONDS));
            var second=jobs.submit(request("second"));
            assertEquals(409,assertThrows(ResponseStatusException.class,()->profiles.delete("first")).getStatusCode().value());
            assertEquals(409,assertThrows(ResponseStatusException.class,()->profiles.delete("second")).getStatusCode().value());
            assertTrue(Files.exists(paths.profiles().resolve("first/reference.wav")));
            release.countDown();finished(jobs,first.id());finished(jobs,second.id());
            profiles.delete("first");profiles.delete("second");assertTrue(profiles.list().isEmpty());
        }finally{release.countDown();jobs.stop();}
    }
}
