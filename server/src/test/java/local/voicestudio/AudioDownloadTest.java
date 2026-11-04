package local.voicestudio;

import java.nio.file.*;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

class AudioDownloadTest {
    @TempDir Path root;
    @Test void playbackHeadersDoNotOverrideTheBrowserDownloadName() throws Exception {
        var paths=new StudioPaths(root);
        byte[] audio="RIFF-local-wave-fixture".getBytes(java.nio.charset.StandardCharsets.US_ASCII);
        var jobs=new Jobs(paths,JsonMapper.builder().build(),(id,request,progress)->{
            Files.write(paths.audio().resolve(id+".wav"),audio);
            return new Job.Result(id,"/api/audio/"+id,1.0,24000,List.of(.1),42,null);
        });
        try {
            var job=jobs.submit(new GenerationRequest("scene","Named recording","Hello",null,"calm","en",42L));
            long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
            while(!jobs.get(job.id()).status().equals("succeeded")&&System.nanoTime()<deadline)Thread.sleep(5);
            assertEquals("succeeded",jobs.get(job.id()).status());
            var response=new StudioApi(jobs,paths,null,null,null,null,null).audio(job.id());
            assertEquals("inline",response.getHeaders().getContentDisposition().getType());
            assertNull(response.getHeaders().getContentDisposition().getFilename());
            assertEquals("audio/wav",response.getHeaders().getContentType().toString());
            try(var stream=response.getBody().getInputStream()){assertArrayEquals(audio,stream.readAllBytes());}
        } finally {jobs.stop();}
    }
}
