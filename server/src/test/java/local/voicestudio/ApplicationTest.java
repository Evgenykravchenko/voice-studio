package local.voicestudio;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest(properties="voice.project=../.runtime/server-context-test")
class ApplicationTest {
    @Autowired StudioApi api;
    @Test void realApplicationWiresJavaAndPythonBridgeWithoutLoadingTheModel() {
        assertEquals("ready", api.health().get("status"));
        assertEquals(false, api.health().get("workerAlive"));
    }
}
