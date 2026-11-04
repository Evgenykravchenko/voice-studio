package local.voicestudio;
import java.util.List;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.http.*;
import org.springframework.core.io.FileSystemResource;
@RestController @RequestMapping("/api/cleanups")
public class CleanupsApi {
    private final Cleanups cleanups;public CleanupsApi(Cleanups cleanups){this.cleanups=cleanups;}
    @GetMapping public List<Cleanups.View> list()throws Exception{return cleanups.list();}
    @GetMapping("/history") public Cleanups.HistoryPage history(@RequestParam(defaultValue="") String query,@RequestParam(defaultValue="1") int page,@RequestParam(defaultValue="6") int size)throws Exception{return cleanups.history(query,page,size);}
    @GetMapping("/{id}") public Cleanups.View get(@PathVariable String id)throws Exception{return cleanups.get(id);}
    @PostMapping(consumes=MediaType.MULTIPART_FORM_DATA_VALUE) @ResponseStatus(HttpStatus.ACCEPTED) public Cleanups.View upload(@RequestParam MultipartFile file,@RequestParam(required=false) String settings)throws Exception{return cleanups.upload(file,cleanups.parseOptions(settings));}
    @PostMapping("/scene") @ResponseStatus(HttpStatus.ACCEPTED) public Cleanups.View scene(@RequestBody Cleanups.Source source)throws Exception{return cleanups.scene(source);}
    @PostMapping("/final") @ResponseStatus(HttpStatus.ACCEPTED) public Cleanups.View assembled(@RequestBody Cleanups.Source source)throws Exception{return cleanups.assembled(source);}
    @PostMapping("/{id}/retry") public Cleanups.View retry(@PathVariable String id)throws Exception{return cleanups.retry(id);}
    @PostMapping("/{id}/tune") public Cleanups.View tune(@PathVariable String id,@RequestBody Cleanups.Options options)throws Exception{return cleanups.tune(id,options);}
    @GetMapping("/{id}/comparison/{side}") public ResponseEntity<FileSystemResource> comparison(@PathVariable String id,@PathVariable String side){return ResponseEntity.ok().contentType(MediaType.parseMediaType("audio/wav")).cacheControl(CacheControl.noCache()).body(new FileSystemResource(cleanups.comparison(id,side)));}
    @PostMapping("/{id}/cancel") public Cleanups.View cancel(@PathVariable String id)throws Exception{return cleanups.cancel(id);}
    @PostMapping("/{id}/apply") public Projects.Stored apply(@PathVariable String id,@RequestBody Cleanups.Apply body)throws Exception{return cleanups.apply(id,body.revision());}
    @GetMapping("/{id}/before") public ResponseEntity<FileSystemResource> before(@PathVariable String id){return ResponseEntity.ok().contentType(MediaType.parseMediaType("audio/wav")).cacheControl(CacheControl.noCache()).body(new FileSystemResource(cleanups.before(id)));}
}
