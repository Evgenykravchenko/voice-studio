package local.voicestudio;

import java.nio.file.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.ObjectMapper;
import org.springframework.web.server.ResponseStatusException;
import static org.junit.jupiter.api.Assertions.*;

class GenerationModelsTest {
    @TempDir Path root;
    private ModelCatalog catalog() throws Exception {
        var python = root.resolve(".venv/bin/python"); Files.createDirectories(python.getParent());
        Files.writeString(python, """
            #!/bin/sh
            cat <<'JSON'
            {"models":[
            {"id":"fish-s2-pro","task":"synthesis","ready":true,"active":true,"synthesisMode":"clone"},
            {"id":"piper-test","task":"synthesis","ready":true,"synthesisMode":"preset","presetVoices":["speaker"]},
            {"id":"design-test","task":"synthesis","ready":true,"synthesisMode":"design"},
            {"id":"dual-test","task":"synthesis","ready":true,"synthesisMode":"clone","synthesisModes":["clone","design"]},
            {"id":"manual-language","task":"synthesis","ready":true,"synthesisMode":"clone","autoLanguage":false,"languages":["ru","en"]},
            {"id":"text-language","task":"synthesis","ready":true,"synthesisMode":"clone","languageMode":"text","languages":["ru","en"]},
            {"id":"files-only","task":"synthesis","ready":false,"installed":true}]}
            JSON
            """);
        python.toFile().setExecutable(true);
        return new ModelCatalog(new StudioPaths(root), new ObjectMapper());
    }
    private GenerationRequest request(String model, String preset, String description, String text) {
        return new GenerationRequest("scene","Scene",text,"local-voice","calm","ru",42L,model,preset,description);
    }
    @Test void freezeRequestedModelAndDoNotRequireRecordingForPresets() throws Exception {
        var catalog = catalog();
        try {
            var preset = catalog.prepare(request("piper-test",null,null,"Текст [pause:0.5] дальше."));
            var projectId=java.util.UUID.randomUUID().toString();
            var scoped=catalog.prepare(new GenerationRequest("scene","Scene","Текст",null,"calm","ru",42L,"piper-test",null,null,null,null,projectId));
            assertEquals(projectId,scoped.projectId());
            assertEquals("piper-test",preset.modelId()); assertEquals("speaker",preset.presetVoice()); assertNull(preset.voiceId());
            var clone = catalog.prepare(request(null,null,null,"Текст"));
            assertEquals("fish-s2-pro",clone.modelId()); assertEquals("local-voice",clone.voiceId());
            assertThrows(ResponseStatusException.class, () -> catalog.prepare(request("files-only",null,null,"Текст")));
        } finally { catalog.stop(); }
    }
    @Test void rejectUnknownPresetMissingDescriptionAndUnsupportedMarkup() throws Exception {
        var catalog = catalog();
        try {
            assertThrows(ResponseStatusException.class, () -> catalog.prepare(request("piper-test","invented",null,"Текст")));
            assertThrows(ResponseStatusException.class, () -> catalog.prepare(request("design-test",null," ","Текст")));
            assertThrows(ResponseStatusException.class, () -> catalog.prepare(request("piper-test",null,null,"[whisper] Текст")));
            assertThrows(ResponseStatusException.class, () -> catalog.prepare(new GenerationRequest("scene","Scene","Text","local-voice","calm","auto",42L,"manual-language",null,null)));
            var design = catalog.prepare(request("design-test",null,"Низкий спокойный голос","Текст"));
            assertNull(design.voiceId()); assertEquals("Низкий спокойный голос",design.voiceDescription());
        } finally { catalog.stop(); }
    }
    @Test void explicitVoiceModeIsValidatedAndFrozenWithTheDescription() throws Exception {
        var catalog=catalog();
        try {
            var description="A calm natural speaker";
            var design=catalog.prepare(new GenerationRequest("scene","Scene","Text",null,"calm","en",42L,"dual-test",null,description,null,null,null,"design"));
            assertEquals("design",design.voiceMode());assertNull(design.voiceId());assertEquals(description,design.voiceDescription());
            var clone=catalog.prepare(request("dual-test",null,description,"Text"));
            assertEquals("auto",catalog.prepare(request("text-language",null,null,"Текст")).language());
            assertEquals("clone",clone.voiceMode());assertEquals("local-voice",clone.voiceId());assertNull(clone.voiceDescription());
            assertThrows(ResponseStatusException.class,()->catalog.prepare(new GenerationRequest("scene","Scene","Text",null,"calm","en",42L,"fish-s2-pro",null,description,null,null,null,"design")));
        } finally {catalog.stop();}
    }
}
