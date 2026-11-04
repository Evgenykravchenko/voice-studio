package local.voicestudio;
import java.nio.file.*;import java.util.*;import java.util.concurrent.*;import java.util.function.Consumer;
import jakarta.validation.Validation;import org.junit.jupiter.api.Test;import org.junit.jupiter.api.io.TempDir;import org.springframework.web.multipart.MultipartFile;import org.springframework.mock.web.MockMultipartFile;import org.springframework.web.server.ResponseStatusException;import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;
class CleanupsTest {
 @TempDir Path root;
 @Test void historySearchReachesEveryVersionAndSurvivesRestart()throws Exception {
  var paths=new StudioPaths(root);var json=JsonMapper.builder().build();var projects=new Projects(paths,json,Validation.buildDefaultValidatorFactory().getValidator());var model=new ModelCatalog(paths,json);
  var jobs=new Jobs(paths,json,(id,request,progress)->{throw new AssertionError("History reads must not start inference");});var assemblies=new Assemblies(paths,projects,jobs,json);
  try{
   var base=root.resolve("data/studio/cleanups");Files.createDirectories(base);
   for(int i=0;i<130;i++){var id=new UUID(0,i+1).toString();var task=new Cleanups.Task(id,"upload",null,null,null,null,"source",i==0?"Актёр — старый образец":"Version "+i,"",String.format("2026-01-01T00:%02d:%02dZ",i/60,i%60),Cleanups.Options.defaults(),id);json.writeValue(base.resolve(id+".json").toFile(),task);}
   var cleanups=new Cleanups(paths,projects,assemblies,jobs,model,new MediaInputs(paths),json);
   assertEquals(100,cleanups.list().size());assertEquals(130,cleanups.history("",1,6).total());
   for(int size:List.of(6,12,24)){var ids=new HashSet<String>();for(int page=1;page<=(130+size-1)/size;page++){var result=cleanups.history("",page,size);assertEquals(page,result.page());result.items().forEach(v->assertTrue(ids.add(v.task().id())));}assertEquals(130,ids.size());}
   var found=cleanups.history(" АКТЕР ",999,6);assertEquals(1,found.total());assertEquals(1,found.page());assertEquals(new UUID(0,1).toString(),found.items().getFirst().task().id());
   assertEquals(0,cleanups.history("missing",99,6).total());assertEquals(1,cleanups.history("missing",99,6).page());
   assertEquals(22,cleanups.history("",Integer.MAX_VALUE,6).page());
   assertEquals(found,new Cleanups(paths,projects,assemblies,jobs,model,new MediaInputs(paths),json).history("АКТЕР",1,6));
   assertThrows(ResponseStatusException.class,()->cleanups.history("",0,6));assertThrows(ResponseStatusException.class,()->cleanups.history("",1,100));assertThrows(ResponseStatusException.class,()->cleanups.history("x".repeat(201),1,6));
  }finally{jobs.stop();assemblies.close();model.stop();}
 }
 void wave(Path file)throws Exception {Files.createDirectories(file.getParent());var format=new javax.sound.sampled.AudioFormat(44100,16,1,true,false);try(var input=new javax.sound.sampled.AudioInputStream(new java.io.ByteArrayInputStream(new byte[44100*2]),format,44100)){javax.sound.sampled.AudioSystem.write(input,javax.sound.sampled.AudioFileFormat.Type.WAVE,file.toFile());}}
 Job await(Jobs jobs,String id)throws Exception{for(int i=0;i<100;i++){var j=jobs.get(id);if(List.of("succeeded","failed","cancelled").contains(j.status()))return j;Thread.sleep(10);}throw new AssertionError("Timeout");}
 @Test void explicitApplyPreservesDraftOriginalAndTrimAcrossReload()throws Exception {
  var paths=new StudioPaths(root);var json=JsonMapper.builder().build();var projects=new Projects(paths,json,Validation.buildDefaultValidatorFactory().getValidator());var model=new ModelCatalog(paths,json){@Override public GenerationRequest prepare(GenerationRequest request){return request;}};
  var worker=new SpeechWorker(){public Job.Result generate(String id,GenerationRequest r,Consumer<Progress> p)throws Exception{wave(paths.audio().resolve(id+".wav"));return new Job.Result(id,"/api/audio/"+id,1,44100,List.of(.1),1L,null);}};
  var jobs=new Jobs(paths,json,worker);var assemblies=new Assemblies(paths,projects,jobs,json);
  try{var original=jobs.submit(new GenerationRequest("s","Take","[whisper] Exact generated words.",null,"calm","auto",1L));await(jobs,original.id());var hash=Files.readAllBytes(paths.audio().resolve(original.id()+".wav"));
   var edit=new ProjectDocument.ClipEdit(.1,.9,-2.0);var scene=new ProjectDocument.Scene("s","Scene","Manually edited draft","auto","calm",.8,"",null,null,null,null,List.of(original.id()),original.id(),new ProjectDocument.Assembly(false,.6,Map.of(original.id(),edit)),"design");
   var project=projects.create(new Projects.Create(UUID.randomUUID().toString(),new ProjectDocument("Test",List.of(scene),new ProjectDocument.Mix(.3,true,true))));
   var cleanups=new Cleanups(paths,projects,assemblies,jobs,model,new MediaInputs(paths),json);var view=cleanups.scene(new Cleanups.Source(project.id(),"s",original.id(),null));assertEquals("succeeded",await(jobs,view.task().id()).status());
   projects.synchronizeTakes(project.id(),jobs.completedForProject(project.id()));assertEquals(project,projects.get(project.id()));assertNull(jobs.get(view.task().id()).request().projectId());assertEquals("[whisper] Exact generated words.",jobs.get(view.task().id()).request().text());
   assertEquals(409,assertThrows(ResponseStatusException.class,()->cleanups.apply(view.task().id(),99)).getStatusCode().value());
   var saved=cleanups.apply(view.task().id(),project.revision());var result=saved.project().scenes().getFirst();assertEquals("Manually edited draft",result.text());assertEquals("design",result.voiceMode());assertEquals(List.of(original.id(),view.task().id()),result.takeIds());assertEquals(view.task().id(),result.selectedTakeId());assertEquals(edit,result.assembly().edits().get(view.task().id()));assertEquals(.6,result.assembly().pauseAfter());assertArrayEquals(hash,Files.readAllBytes(paths.audio().resolve(original.id()+".wav")));assertEquals(saved,cleanups.apply(view.task().id(),1));assertTrue(new Cleanups(paths,projects,assemblies,jobs,model,new MediaInputs(paths),json).get(view.task().id()).applied());
   var settings=new Cleanups.Options(40,60,-15,75,true,true,100);var tuned=cleanups.tune(view.task().id(),settings);assertEquals("succeeded",await(jobs,tuned.task().id()).status());assertEquals(view.task().sourceId(),tuned.task().sourceId());assertEquals(view.task().id(),tuned.task().baseId());assertEquals(view.task().id(),tuned.task().originalSourceId());assertEquals(Cleanups.Options.defaults(),cleanups.get(view.task().id()).task().options());
   var twice=cleanups.apply(tuned.task().id(),saved.revision());assertEquals("Manually edited draft",twice.project().scenes().getFirst().text());assertEquals(edit,twice.project().scenes().getFirst().assembly().edits().get(tuned.task().id()));assertEquals(settings,new Cleanups(paths,projects,assemblies,jobs,model,new MediaInputs(paths),json).get(tuned.task().id()).task().options());
   assertThrows(ResponseStatusException.class,()->new Cleanups.Options(101,0,0,0,false,false));assertThrows(ResponseStatusException.class,()->new Cleanups.Options(0,0,0,0,false,false,101));assertThrows(ResponseStatusException.class,()->cleanups.parseOptions("{bad}"));

  }finally{jobs.stop();assemblies.close();model.stop();}
 }
 @Test void cancellingQueuedWorkNeverStartsItAndSurvivesRestart()throws Exception {
  var paths=new StudioPaths(root);var json=JsonMapper.builder().build();var entered=new CountDownLatch(1);var release=new CountDownLatch(1);var calls=new java.util.concurrent.atomic.AtomicInteger();
  var worker=new SpeechWorker(){public Job.Result generate(String id,GenerationRequest r,Consumer<Progress> p)throws Exception{calls.incrementAndGet();entered.countDown();release.await();return new Job.Result(id,"/api/audio/"+id,1,44100,List.of(.1),1,null);}};
  var jobs=new Jobs(paths,json,worker);String cancelled;
  try{var one=jobs.submit(new GenerationRequest("s","One","text",null,"calm","auto",1L));assertTrue(entered.await(2,TimeUnit.SECONDS));var two=jobs.submit(new GenerationRequest("s","Two","text",null,"calm","auto",1L));cancelled=two.id();jobs.cancel(cancelled);release.countDown();await(jobs,one.id());Thread.sleep(50);assertEquals(1,calls.get());assertEquals("cancelled",jobs.get(cancelled).status());}finally{release.countDown();jobs.stop();}
  var reopened=new Jobs(paths,json,worker);try{assertEquals("cancelled",reopened.get(cancelled).status());}finally{reopened.stop();}
 }
}
