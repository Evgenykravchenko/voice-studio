package local.voicestudio;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

@Service
public class MediaInputs {
    private final StudioPaths paths;
    public MediaInputs(StudioPaths paths) {this.paths=paths;}
    public Map<String,String> upload(MultipartFile file) throws IOException {
        String name=Objects.requireNonNullElse(file.getOriginalFilename(),"").toLowerCase(Locale.ROOT);
        if (file.isEmpty() || file.getSize()>50*1024*1024 || !name.matches(".*\\.(wav|mp3|m4a|flac|ogg|aac|aiff|aif|opus|webm)$")) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Выберите аудиозапись до 50 МБ.");
        String id=UUID.randomUUID().toString();
        var directory=paths.root().resolve("data/studio/inputs").resolve(id);Files.createDirectories(directory);
        var temporary=directory.resolve("source.tmp");
        try {
            try(var stream=file.getInputStream()){Files.copy(stream,temporary);}
            Files.move(temporary,directory.resolve("source"),StandardCopyOption.ATOMIC_MOVE);
            return Map.of("id",id);
        } catch(IOException e) {Files.deleteIfExists(temporary);Files.deleteIfExists(directory);throw e;}
    }
}
