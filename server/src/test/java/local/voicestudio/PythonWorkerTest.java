package local.voicestudio;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

class PythonWorkerTest {
    @TempDir Path root;

    @Test void cancellingRealChildInvalidatesItsStreamsBeforeFollowingJobStarts() throws Exception {
        Files.createDirectories(root.resolve(".venv/bin"));
        Files.createDirectories(root.resolve("outputs/studio"));
        var executable = root.resolve(".venv/bin/python");
        // A small real JSON-lines process exercises pipes/termination without ML packages.
        Files.writeString(executable, """
            #!/bin/sh
            while IFS= read -r command; do
              id=$(printf '%s' "$command" | cut -d '"' -f4)
              case "$command" in
                *block*)
                  printf '{"event":"progress","id":"%s","stage":"loading"}\n' "$id"
                  while :; do sleep 1; done
                  ;;
                *)
                  : > "outputs/studio/$id.wav"
                  printf '{"event":"completed","id":"%s","duration":1,"sampleRate":24000,"peaks":[0.2],"seed":42}\n' "$id"
                  ;;
              esac
            done
            """);
        assertTrue(executable.toFile().setExecutable(true));
        var worker = new PythonWorker(new StudioPaths(root), JsonMapper.builder().build());
        var entered = new CountDownLatch(1);
        var executor = Executors.newSingleThreadExecutor();
        try {
            var first = executor.submit(() -> worker.generate("11111111-1111-4111-8111-111111111111",
                new GenerationRequest("s", "First", "block", null, "calm", "en", 42L), p -> entered.countDown()));
            assertTrue(entered.await(3, TimeUnit.SECONDS));
            worker.cancelCurrent();
            assertFalse(worker.isAlive());
            assertInstanceOf(IOException.class, assertThrows(ExecutionException.class, () -> first.get(3, TimeUnit.SECONDS)).getCause());
            var second = worker.generate("22222222-2222-4222-8222-222222222222",
                new GenerationRequest("s", "Second", "ready", null, "calm", "en", 42L), p -> {});
            assertEquals(1, second.duration());
            assertEquals(List.of(.2), second.peaks());
            assertTrue(worker.isAlive());
        } finally {
            worker.close();
            executor.shutdownNow();
        }
        assertFalse(worker.isAlive());
    }
}
