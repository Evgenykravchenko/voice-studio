package local.voicestudio;

import java.nio.file.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.ObjectMapper;
import org.springframework.web.server.ResponseStatusException;
import static org.junit.jupiter.api.Assertions.*;

class ModelCatalogTest {
    @TempDir Path root;
    private ModelCatalog catalog() throws Exception {
        var python = root.resolve(".venv/bin/python"); Files.createDirectories(python.getParent());
        Files.writeString(python, """
            #!/bin/sh
            case "$4" in
              list) echo '{"supported":true,"freeBytes":1000000000,"models":[{"id":"test-model","installed":false,"sizeBytes":100,"downloadedBytes":0}]}' ;;
              download) echo '{"stage":"downloading","downloadedBytes":20,"totalBytes":100}'; sleep 0.2; echo '{"stage":"installed","downloadedBytes":100,"totalBytes":100}' ;;
              select) echo '{"ok":true}' ;;
            esac
            """);
        assertTrue(python.toFile().setExecutable(true));
        return new ModelCatalog(new StudioPaths(root), new ObjectMapper());
    }
    @Test void acceptsOnlyCatalogIdsAndDoesNotDuplicateActiveTransfers() throws Exception {
        var catalog = catalog();
        try {
            assertThrows(ResponseStatusException.class, () -> catalog.download("arbitrary-repository"));
            assertThrows(ResponseStatusException.class, () -> catalog.download("../escape"));
            catalog.download("test-model");
            assertTrue(java.util.List.of("queued","downloading").contains(catalog.download("test-model").status()));
        } finally { catalog.stop(); }
    }
    @Test void immediateCancelAndResumeCannotBeOverwrittenByTheOldProcess() throws Exception {
        var catalog = catalog();
        try {
            catalog.download("test-model"); catalog.cancel("test-model");
            assertEquals("cancelled",catalog.list().path("models").get(0).path("transfer").path("status").asString());
            catalog.download("test-model");
            var deadline = System.nanoTime() + java.util.concurrent.TimeUnit.SECONDS.toNanos(3);
            while (!catalog.list().path("models").get(0).path("transfer").path("status").asString().equals("installed") && System.nanoTime() < deadline) Thread.sleep(20);
            assertEquals("installed",catalog.list().path("models").get(0).path("transfer").path("status").asString());
        } finally { catalog.stop(); }
    }
    @Test void restartTurnsUnfinishedTransferIntoAResumableState() throws Exception {
        var folder = root.resolve("data/studio/models"); Files.createDirectories(folder);
        Files.writeString(folder.resolve("test-model.transfer.json"),"{\"status\":\"downloading\",\"stage\":\"downloading\",\"downloadedBytes\":20,\"totalBytes\":100,\"error\":null}");
        var catalog = catalog();
        try { assertEquals("cancelled",catalog.list().path("models").get(0).path("transfer").path("status").asString()); }
        finally { catalog.stop(); }
    }
    @Test void largeCatalogOutputIsDrainedBeforeWaitingForProcessExit() throws Exception {
        var catalog = catalog();
        var payload = "{\"supported\":true,\"models\":[],\"padding\":\"" + "x".repeat(200000) + "\"}";
        Files.writeString(root.resolve(".venv/bin/python"), "#!/bin/sh\ncat <<'CATALOG_JSON'\n" + payload + "\nCATALOG_JSON\n");
        try { assertEquals(200000, catalog.list().path("padding").asString().length()); }
        finally { catalog.stop(); }
    }

}
