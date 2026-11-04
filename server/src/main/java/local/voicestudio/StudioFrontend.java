package local.voicestudio;

import java.nio.file.Files;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.CacheControl;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/** Serves the compiled local studio; Node/Vite is only needed when building or developing. */
@Configuration
@Controller
public class StudioFrontend implements WebMvcConfigurer {
    private final StudioPaths paths;
    public StudioFrontend(StudioPaths paths) { this.paths = paths; }
    @Override public void addResourceHandlers(ResourceHandlerRegistry registry) {
        var location = paths.root().resolve("frontend/dist/client").toUri().toString();
        if (!location.endsWith("/")) location += "/";
        registry.addResourceHandler("/**").addResourceLocations(location).setCacheControl(CacheControl.noCache());
    }
    @GetMapping("/") public ResponseEntity<FileSystemResource> home() {
        var index = paths.root().resolve("frontend/dist/client/index.html");
        if (!Files.isRegularFile(index)) throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
            "Интерфейс ещё не собран. Выполните ./scripts/bootstrap.sh в папке проекта.");
        return ResponseEntity.ok().contentType(MediaType.TEXT_HTML).cacheControl(CacheControl.noStore())
            .body(new FileSystemResource(index));
    }
    @GetMapping("/audio/{name}") public ResponseEntity<FileSystemResource> localSample(@PathVariable String name) {
        if (!name.matches("scene-[1-3]\\.wav")) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        var file = paths.sampleAudio(name.charAt(6) - '1');
        if (!Files.isRegularFile(file)) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        return ResponseEntity.ok().contentType(MediaType.parseMediaType("audio/wav"))
            .cacheControl(CacheControl.noStore()).body(new FileSystemResource(file));
    }
}
