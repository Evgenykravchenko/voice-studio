package local.voicestudio;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import java.util.concurrent.atomic.AtomicBoolean;
import static org.junit.jupiter.api.Assertions.*;
class LocalRequestsTest {
    @Test void rejectsForeignOriginAndReboundHost() throws Exception {
        for (var attack : new String[][]{{"127.0.0.1", "https://foreign.example"}, {"foreign.example", "http://127.0.0.1:4173"}}) {
            var request = new MockHttpServletRequest("POST", "/api/jobs"); request.setServerName(attack[0]); request.addHeader("Origin", attack[1]);
            var response = new MockHttpServletResponse(); var called = new AtomicBoolean();
            new LocalRequests().doFilter(request, response, (req,res) -> called.set(true));
            assertEquals(403, response.getStatus()); assertFalse(called.get());
        }
    }
    @Test void allowsTheLocalStudio() throws Exception {
        var request = new MockHttpServletRequest("POST", "/api/jobs"); request.setServerName("127.0.0.1"); request.addHeader("Origin", "http://127.0.0.1:4173");
        var response = new MockHttpServletResponse(); var called = new AtomicBoolean();
        new LocalRequests().doFilter(request, response, (req,res) -> called.set(true)); assertTrue(called.get());
    }
    @Test void acceptsTheCompiledStudioOnItsOwnLoopbackPortButNotANeighboringOrigin() throws Exception {
        for (var origin : new String[]{"http://127.0.0.1:7082", "http://127.0.0.1:7083", "http://foreign.example:7082", "null"}) {
            var request = new MockHttpServletRequest("POST", "/api/projects"); request.setServerName("127.0.0.1"); request.setServerPort(7082); request.addHeader("Origin", origin);
            var response = new MockHttpServletResponse(); var called = new AtomicBoolean();
            new LocalRequests().doFilter(request,response,(req,res)->called.set(true));
            assertEquals(origin.equals("http://127.0.0.1:7082"),called.get());
            assertEquals(origin.equals("http://127.0.0.1:7082") ? 200 : 403,response.getStatus());
        }
    }
}
