package local.voicestudio;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import org.springframework.core.io.FileSystemResource;
@RestController
@RequestMapping("/api/projects/{projectId}/assembly")
public class AssembliesApi {
    private final Assemblies assemblies;
    public AssembliesApi(Assemblies assemblies){this.assemblies=assemblies;}
    @PostMapping @ResponseStatus(HttpStatus.ACCEPTED)
    public Assemblies.Task submit(@PathVariable String projectId,@RequestBody Assemblies.Request request)throws Exception{return assemblies.submit(projectId,request.revision());}
    @GetMapping("/{id}") public Assemblies.Task get(@PathVariable String projectId,@PathVariable String id){return assemblies.get(projectId,id);}
    @GetMapping("/{id}/audio.{format}") public ResponseEntity<FileSystemResource> audio(@PathVariable String projectId,@PathVariable String id,@PathVariable String format){return ResponseEntity.ok().contentType(MediaType.parseMediaType(format.equals("mp3")?"audio/mpeg":"audio/wav")).header(HttpHeaders.CONTENT_DISPOSITION,"inline; filename=\"voice-studio-final."+format+"\"").cacheControl(CacheControl.noCache()).body(new FileSystemResource(assemblies.audio(projectId,id,format)));}
}
