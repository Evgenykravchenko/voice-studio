package local.voicestudio;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment=SpringBootTest.WebEnvironment.RANDOM_PORT)
class FrontendServingTest {
    @TempDir static Path root;
    @LocalServerPort int port;
    @DynamicPropertySource static void project(DynamicPropertyRegistry registry) { registry.add("voice.project", () -> root.toString()); }
    @BeforeAll static void fixture() throws Exception {
        var client=root.resolve("frontend/dist/client"); Files.createDirectories(client.resolve("assets"));
        Files.writeString(client.resolve("index.html"),"<!doctype html><title>Voice Studio test</title>");
        Files.writeString(client.resolve("assets/app.js"),"console.log('local asset');");
        Files.createDirectories(root.resolve("data")); Files.writeString(root.resolve("data/private.json"),"private fixture");
    }
    private HttpResponse<String> get(String path) throws Exception {
        return HttpClient.newHttpClient().send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:"+port+path)).build(),HttpResponse.BodyHandlers.ofString());
    }
    @Test void servesCompiledStudioAndAssetsWithoutNodeAndKeepsApiRoutesSeparate() throws Exception {
        var page=get("/?view=models"); assertEquals(200,page.statusCode()); assertTrue(page.body().contains("Voice Studio test"));
        assertTrue(page.headers().firstValue("content-type").orElse("").contains("text/html"));
        assertTrue(page.headers().firstValue("cache-control").orElse("").contains("no-store"));
        assertEquals("console.log('local asset');",get("/assets/app.js").body());
        assertEquals(200,get("/api/health").statusCode());
        assertEquals(404,get("/api/not-a-route").statusCode());
        assertEquals(404,get("/data/private.json").statusCode());
        assertNotEquals(200,get("/assets/%2e%2e/%2e%2e/%2e%2e/data/private.json").statusCode());
    }
    @Test void anUnbuiltFrontendIsReportedInsteadOfAFalseReadyPage() throws Exception {
        var index=root.resolve("frontend/dist/client/index.html"); var contents=Files.readString(index);
        try { Files.delete(index); assertEquals(503,get("/").statusCode()); }
        finally { Files.writeString(index,contents); }
    }
    @Test void localSamplesStayOutsideBuildAndRetainLegacyPlaybackAndRangeRequests() throws Exception {
        var legacy=root.resolve("frontend/public/audio"); Files.createDirectories(legacy);
        Files.writeString(legacy.resolve("scene-1.wav"),"RIFF legacy local sample");
        assertEquals("RIFF legacy local sample",get("/audio/scene-1.wav").body());
        var samples=root.resolve("data/studio/samples"); Files.createDirectories(samples);
        Files.writeString(samples.resolve("scene-1.wav"),"RIFF private local sample");
        var preferred=get("/audio/scene-1.wav");
        assertEquals(200,preferred.statusCode()); assertEquals("RIFF private local sample",preferred.body());
        assertTrue(preferred.headers().firstValue("content-type").orElse("").startsWith("audio/"));
        assertTrue(preferred.headers().firstValue("cache-control").orElse("").contains("no-store"));
        var range=HttpClient.newHttpClient().send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:"+port+"/audio/scene-1.wav"))
            .header("Range","bytes=0-3").build(),HttpResponse.BodyHandlers.ofString());
        assertEquals(206,range.statusCode()); assertEquals("RIFF",range.body());
        assertFalse(Files.exists(root.resolve("frontend/dist/client/audio/scene-1.wav")));
        assertEquals(404,get("/audio/scene-2.wav").statusCode());
        assertEquals(404,get("/audio/scene-4.wav").statusCode());
        assertEquals(404,get("/audio/private.json").statusCode());
    }
}
