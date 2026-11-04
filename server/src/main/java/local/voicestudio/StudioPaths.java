package local.voicestudio;

import java.nio.file.Path;
import java.io.File;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Autowired;

@Component
public record StudioPaths(Path root) {
    @Autowired public StudioPaths(@Value("${voice.project:.}") String root) { this(Path.of(root).toAbsolutePath().normalize()); }
    public Path jobs() { return root.resolve("data/studio/jobs"); }
    public Path audio() { return root.resolve("outputs/studio"); }
    public Path profiles() { return root.resolve("data/profiles"); }
    public Path sampleAudio(int index) {
        if (index < 0 || index > 2) throw new IllegalArgumentException("Unknown sample");
        var name = "scene-" + (index + 1) + ".wav";
        var local = root.resolve("data/studio/samples").resolve(name);
        return java.nio.file.Files.isRegularFile(local) ? local : root.resolve("frontend/public/audio").resolve(name);
    }
    public void configurePython(ProcessBuilder builder) {
        // The selected project owns imports even when a venv still has an editable
        // install pointing to another checkout, or PYTHONPATH was inherited.
        builder.environment().put("PYTHONPATH", root.resolve("src") + File.pathSeparator + root.resolve("vendor"));
        builder.environment().put("PYTHONPYCACHEPREFIX", root.resolve(".runtime/pycache").toString());
        builder.environment().put("PYTHONUNBUFFERED", "1");
    }
}
