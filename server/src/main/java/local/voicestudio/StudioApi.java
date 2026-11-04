package local.voicestudio;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import jakarta.validation.Valid;
import org.springframework.web.multipart.MultipartFile;
import tools.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/api")
public class StudioApi {
    private final Jobs jobs;
    private final StudioPaths paths;
    private final VoiceProfiles profiles;
    private final ModelCatalog models;
    private final MediaInputs inputs;
    private final ModelImports modelImports;
    private final Projects projects;
    public StudioApi(Jobs jobs, StudioPaths paths, VoiceProfiles profiles, ModelCatalog models, MediaInputs inputs,ModelImports modelImports,Projects projects) { this.jobs = jobs; this.paths = paths; this.profiles = profiles; this.models = models; this.inputs=inputs; this.modelImports=modelImports;this.projects=projects; }

    @GetMapping("/health") public Map<String, Object> health() {
        var health = new LinkedHashMap<String,Object>(Map.of("status", "ready", "engine", "fish-s2-pro", "workerAlive", jobs.workerAlive(),
            "temperature", 0.8, "supportsTemperature", false, "languageMode", "text", "maxTextLength", 3000, "idleUnloadSeconds", 180, "projectRoot", paths.root().toString(), "supportsVoiceModes",true));
        health.put("supportsReferenceLanguages", true);
        return health;
    }
    @GetMapping("/models") public tools.jackson.databind.JsonNode models() throws IOException { return models.list(); }
    @PostMapping(value="/models/{id}/download", consumes=MediaType.APPLICATION_JSON_VALUE)
    @ResponseStatus(HttpStatus.ACCEPTED) public ModelCatalog.Transfer downloadModel(@PathVariable String id) throws IOException { return models.download(id); }
    @PostMapping(value="/models/{id}/cancel", consumes=MediaType.APPLICATION_JSON_VALUE)
    @ResponseStatus(HttpStatus.NO_CONTENT) public void cancelModel(@PathVariable String id) throws IOException { models.cancel(id); }
    @PostMapping(value="/models/{id}/select", consumes=MediaType.APPLICATION_JSON_VALUE)
    @ResponseStatus(HttpStatus.NO_CONTENT) public void selectModel(@PathVariable String id) throws IOException { models.select(id); }
    @PostMapping(value="/media",consumes=MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String,String> uploadMedia(@RequestParam MultipartFile file) throws IOException {return inputs.upload(file);}
    @GetMapping("/models/{id}/manifest") public tools.jackson.databind.JsonNode modelManifest(@PathVariable String id) throws IOException{return models.manifest(id);}
    @PostMapping(value="/models/{id}/import/chunk",consumes=MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String,Long> importChunk(@PathVariable String id,@RequestParam String path,@RequestParam long offset,@RequestParam MultipartFile file) throws IOException{return modelImports.chunk(id,path,offset,file);}
    @PostMapping(value="/models/{id}/import/complete",consumes=MediaType.APPLICATION_JSON_VALUE)
    @ResponseStatus(HttpStatus.ACCEPTED) public ModelCatalog.Transfer finishModelImport(@PathVariable String id) throws IOException{return modelImports.finish(id);}
    @GetMapping("/voices") public List<VoiceProfiles.Voice> voices() throws IOException { return profiles.list(); }
    @DeleteMapping("/voices/{id}") @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteVoice(@PathVariable String id) throws IOException {profiles.delete(id);}
    @GetMapping("/voice-imports") public List<VoiceImport> imports() { return profiles.tasks(); }
    @GetMapping("/voice-imports/{id}") public VoiceImport voiceImport(@PathVariable String id) { return profiles.get(id); }
    @PostMapping(value="/voice-imports", consumes=MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseStatus(HttpStatus.ACCEPTED)
    public VoiceImport uploadVoice(@RequestParam MultipartFile file, @RequestParam String name, @RequestParam(defaultValue="0") double start,
        @RequestParam(defaultValue="20") double duration, @RequestParam(defaultValue="ru") String language) throws IOException { return profiles.upload(file,name,start,duration,language); }
    @PostMapping(value="/voice-imports/{id}/save", consumes=MediaType.APPLICATION_JSON_VALUE)
    public VoiceImport saveVoice(@PathVariable String id, @RequestBody VoiceProfiles.SaveVoice body) throws IOException { return profiles.save(id,body); }
    @DeleteMapping("/voice-imports/{id}") @ResponseStatus(HttpStatus.NO_CONTENT)
    public void discardVoice(@PathVariable String id) throws IOException { profiles.discard(id); }
    @GetMapping("/voices/{id}/reference") public ResponseEntity<FileSystemResource> voiceReference(@PathVariable String id) { return reference(profiles.reference(id,false)); }
    @GetMapping("/voice-imports/{id}/reference") public ResponseEntity<FileSystemResource> draftReference(@PathVariable String id) { return reference(profiles.reference(id,true)); }
    private ResponseEntity<FileSystemResource> reference(Path path) { return ResponseEntity.ok().contentType(MediaType.parseMediaType("audio/wav")).cacheControl(CacheControl.noCache()).body(new FileSystemResource(path)); }
    @PostMapping(value="/jobs", consumes=MediaType.APPLICATION_JSON_VALUE)
    @ResponseStatus(HttpStatus.ACCEPTED)
    public Job generate(@Valid @RequestBody GenerationRequest request) throws IOException,java.sql.SQLException {
        String selection=null;
        if(request.projectId()!=null){
            projects.synchronizeTakes(request.projectId(),jobs.completedForProject(request.projectId()));
            var scene=projects.get(request.projectId()).project().scenes().stream().filter(value->value.id().equals(request.sceneId())).findFirst().orElseThrow(()->new ResponseStatusException(HttpStatus.BAD_REQUEST,"Сначала сохраните сцену в проекте."));
            selection=scene.selectedTakeId()!=null?scene.selectedTakeId():scene.audioIndex()!=null?"demo-"+scene.audioIndex():"none";
        }
        return jobs.submit(models.prepare(request).withSelectionAtSubmission(selection));
    }
    @GetMapping("/jobs") public List<Job> jobs(@RequestParam(required=false) List<String> ids) { return ids==null?jobs.list():jobs.lookup(ids); }
    @GetMapping("/recordings") public Jobs.RecordingPage recordings(@RequestParam(defaultValue="") String query,@RequestParam(defaultValue="1") int page,@RequestParam(defaultValue="12") int size) {return jobs.recordings(query,page,size);}
    @GetMapping("/jobs/{id}") public Job job(@PathVariable String id) { return jobs.get(id); }
    @GetMapping("/audio/{id}") public ResponseEntity<FileSystemResource> audio(@PathVariable String id) {
        if (!id.matches("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        if (!jobs.get(id).status().equals("succeeded")) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        var file = paths.audio().resolve(id + ".wav");
        if (!Files.isRegularFile(file)) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Аудиофайл не найден.");
        return ResponseEntity.ok().contentType(MediaType.parseMediaType("audio/wav"))
            // Let the same-origin UI's download attribute supply its user-facing name.
            .header(HttpHeaders.CONTENT_DISPOSITION, "inline")
            .cacheControl(CacheControl.noCache()).body(new FileSystemResource(file));
    }
}
