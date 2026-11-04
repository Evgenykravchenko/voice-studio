package local.voicestudio;

import java.nio.file.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.*;
import static org.junit.jupiter.api.Assertions.*;

class ModelImportsTest {
    @TempDir Path root;
    @Test void chunksMustMatchManifestPathOffsetAndSize() throws Exception {
        var json=new ObjectMapper();
        var catalog=new ModelCatalog(new StudioPaths(root),json){
            @Override public JsonNode manifest(String id){return json.readTree("{\"files\":[{\"path\":\"nested/model.bin\",\"size\":6},{\"path\":\"../escape\",\"size\":6}]}");}
        };
        try {
            var imports=new ModelImports(new StudioPaths(root),catalog);
            var chunk=new MockMultipartFile("file","anything.bin","application/octet-stream",new byte[]{1,2,3});
            assertThrows(ResponseStatusException.class,()->imports.chunk("restricted","other.bin",0,chunk));
            assertThrows(ResponseStatusException.class,()->imports.chunk("restricted","../escape",0,chunk));
            assertEquals(3L,imports.chunk("restricted","nested/model.bin",0,chunk).get("received"));
            assertThrows(ResponseStatusException.class,()->imports.chunk("restricted","nested/model.bin",1,chunk));
            assertEquals(6L,imports.chunk("restricted","nested/model.bin",3,chunk).get("received"));
            assertThrows(ResponseStatusException.class,()->imports.chunk("restricted","nested/model.bin",6,chunk));
            assertEquals(6,Files.size(root.resolve("data/studio/model-imports/restricted/nested/model.bin")));
        }finally{catalog.stop();}
    }
    @Test void mediaUploadUsesGeneratedNamesAndRejectsNonAudio() throws Exception {
        var media=new MediaInputs(new StudioPaths(root));
        assertThrows(ResponseStatusException.class,()->media.upload(new MockMultipartFile("file","script.py","text/plain",new byte[]{1})));
        assertThrows(ResponseStatusException.class,()->media.upload(new MockMultipartFile("file","empty.wav","audio/wav",new byte[0])));
        var bytes=new byte[]{1,2,3};var result=media.upload(new MockMultipartFile("file","../recording.wav","audio/wav",bytes));
        assertArrayEquals(bytes,Files.readAllBytes(root.resolve("data/studio/inputs").resolve(result.get("id")).resolve("source")));
    }
}
