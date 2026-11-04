package local.voicestudio;

import java.io.IOException;
import java.util.Set;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** No remote binding, wildcard CORS, form submissions or foreign web origins. */
@Component
public class LocalRequests extends OncePerRequestFilter {
    private static final Set<String> HOSTS = Set.of("127.0.0.1", "localhost", "::1", "[::1]");
    private static final Set<String> ORIGINS = Set.of("http://127.0.0.1:4173", "http://localhost:4173", "http://127.0.0.1:7080", "http://localhost:7080");
    @Override protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain) throws ServletException, IOException {
        var origin = request.getHeader("Origin");
        var host = request.getServerName();
        var originHost = host.equals("::1") ? "[::1]" : host;
        boolean sameOrigin = ("http://" + originHost + ":" + request.getServerPort()).equals(origin);
        if (!HOSTS.contains(host) || (origin != null && !sameOrigin && !ORIGINS.contains(origin))) {
            response.sendError(403); return;
        }
        chain.doFilter(request, response);
    }
}
