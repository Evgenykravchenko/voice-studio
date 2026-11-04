package local.voicestudio;
import java.nio.file.Path;import java.util.*;
import jakarta.validation.Validation;import org.junit.jupiter.api.Test;import org.junit.jupiter.api.io.TempDir;
import org.springframework.web.server.ResponseStatusException;import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;
class AssemblyPersistenceTest {
 @TempDir Path root;
 @Test void editsSurviveReloadAndNewTakeReconciliation()throws Exception {
  var json=JsonMapper.builder().build();var store=new Projects(new StudioPaths(root),json,Validation.buildDefaultValidatorFactory().getValidator());
  var assembly=new ProjectDocument.Assembly(false,.4,Map.of("demo-0",new ProjectDocument.ClipEdit(.2,2.3,-2.0)));
  var scene=new ProjectDocument.Scene("scene-a","Scene","Exact text","ru","calm",.8,"",0,null,null,null,List.of(),null,assembly);
  var mix=new ProjectDocument.Mix(.3,true,true);var project=new ProjectDocument("Test",List.of(scene),mix);
  var saved=store.create(new Projects.Create(UUID.randomUUID().toString(),project));
  var take=UUID.randomUUID().toString();var request=new GenerationRequest("scene-a","Scene","Exact text",null,"calm","ru",42L,"fish-s2-pro",null,null,null,null,saved.id());
  store.synchronizeTakes(saved.id(),List.of(new Job(take,request,"succeeded","done",1,1,"2026-10-29T01:00:00Z","2026-10-29T01:00:01Z",null,new Job.Result(take,"/api/audio/"+take,1,24000,List.of(.1),42L,.8))));
  var reloaded=new Projects(new StudioPaths(root),json,Validation.buildDefaultValidatorFactory().getValidator()).get(saved.id()).project();
  assertEquals(assembly,reloaded.scenes().getFirst().assembly());assertEquals(mix,reloaded.mix());assertEquals("Exact text",reloaded.scenes().getFirst().text());assertEquals(take,reloaded.scenes().getFirst().selectedTakeId());
  assertThrows(ResponseStatusException.class,()->store.save(saved.id(),new Projects.Save(2,new ProjectDocument("Bad",List.of(scene),new ProjectDocument.Mix(6.0,true,true)))));
 }
}
