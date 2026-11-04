package local.voicestudio;

import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import jakarta.validation.Validation;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

class ProjectsTest {
    @TempDir Path root;
    Projects store() throws Exception {return new Projects(new StudioPaths(root),JsonMapper.builder().build(),Validation.buildDefaultValidatorFactory().getValidator());}
    ProjectDocument document(String text){return new ProjectDocument("Тестовый проект",List.of(new ProjectDocument.Scene("scene-a","Вступление",text,"ru","calm",.8,"",null,"voice-a",null,null,List.of(),null)));}
    GenerationRequest request(String project){return new GenerationRequest("scene-a","Scene","Exact generated source","voice-a","calm","ru",42L,"fish-s2-pro",null,null,null,null,project);}
    Job job(String project,String id){return new Job(id,request(project),"succeeded","done",1,1,"2026-10-29T01:00:00Z","2026-10-29T01:00:01Z",null,new Job.Result(id,"/api/audio/"+id,1,24000,List.of(.1),42,.8));}
    @Test void persistsExactTextSettingsAndTakeSelectionAcrossRestart() throws Exception {
        var store=store();var id=UUID.randomUUID().toString();var text="[whisper] Не меняй API.foo(42).\nСтрока с ё, кавычками: 'x'; <tag>.";
        var created=store.create(new Projects.Create(id,document(text)));
        assertEquals(1,created.revision());assertEquals(text,store.get(id).project().scenes().getFirst().text());
        var take=UUID.randomUUID().toString();store.synchronizeTakes(id,List.of(job(id,take)));
        var reopened=store().get(id);assertEquals(text,reopened.project().scenes().getFirst().text());
        assertEquals(take,reopened.project().scenes().getFirst().selectedTakeId());assertEquals(List.of(take),reopened.project().scenes().getFirst().takeIds());
        assertEquals(1,store.list().size());assertEquals(1,store.list().getFirst().sceneCount());assertTrue(Files.isRegularFile(root.resolve("data/studio/studio.db")));
        var json=JsonMapper.builder().build().valueToTree(reopened.project());assertTrue(json.path("scenes").get(0).has("audioIndex"));assertTrue(json.path("scenes").get(0).path("audioIndex").isNull());assertFalse(json.path("scenes").get(0).has("presetVoice"));
    }
    @Test void migrationAndCreateRetriesAreIdempotentAndNeverRestoreStaleContent() throws Exception {
        var store=store();var legacy=document("Original draft");var migrated=store.migrate(legacy);
        var updated=store.save(migrated.id(),new Projects.Save(migrated.revision(),document("Edited on server")));
        assertEquals(updated,store.migrate(legacy));assertEquals(1,store.list().size());
        var id=UUID.randomUUID().toString();var created=store.create(new Projects.Create(id,legacy));
        store.save(id,new Projects.Save(created.revision(),document("Later edit")));
        assertEquals("Later edit",store.create(new Projects.Create(id,legacy)).project().scenes().getFirst().text());
        assertThrows(ResponseStatusException.class,()->store.create(new Projects.Create(id,document("Different create request"))));
    }
    @Test void voiceModeSurvivesRestartAndAutomaticTakeLinking() throws Exception {
        var store=store();var scene=document("Keep exact script").scenes().getFirst();
        var design=new ProjectDocument.Scene(scene.id(),scene.title(),scene.text(),scene.speechLanguage(),scene.emotion(),scene.temperature(),scene.seed(),null,null,null,"Calm voice",List.of(),null,null,"design");
        var project=store.create(new Projects.Create(UUID.randomUUID().toString(),new ProjectDocument("Voice mode",List.of(design))));
        store.synchronizeTakes(project.id(),List.of(job(project.id(),UUID.randomUUID().toString())));
        var reopened=store().get(project.id()).project().scenes().getFirst();
        assertEquals("design",reopened.voiceMode());assertEquals("Calm voice",reopened.voiceDescription());assertEquals("Keep exact script",reopened.text());
    }
    @Test void staleAndConcurrentSavesCannotOverwriteNewerDrafts() throws Exception {
        var store=store();var p=store.create(new Projects.Create(UUID.randomUUID().toString(),document("Base")));
        var pool=Executors.newFixedThreadPool(2);
        try{
            var start=new CountDownLatch(1);
            var tasks=new ArrayList<Future<Boolean>>();
            for(var value:List.of("First editor","Second editor"))tasks.add(pool.submit(()->{start.await();try{store.save(p.id(),new Projects.Save(1,document(value)));return true;}catch(ResponseStatusException e){assertEquals(409,e.getStatusCode().value());return false;}}));
            start.countDown();int succeeded=0;for(var f:tasks)if(f.get(5,TimeUnit.SECONDS))succeeded++;
            assertEquals(1,succeeded);assertEquals(2,store.get(p.id()).revision());
            assertThrows(ResponseStatusException.class,()->store.save(p.id(),new Projects.Save(1,document("Stale"))));assertNotEquals("Stale",store.get(p.id()).project().scenes().getFirst().text());
        }finally{pool.shutdownNow();}
    }
    @Test void completedJobsStayWithTheirOwnProjectAndLinkOnlyOnce() throws Exception {
        var store=store();var a=store.create(new Projects.Create(UUID.randomUUID().toString(),document("A")));var b=store.create(new Projects.Create(UUID.randomUUID().toString(),document("B")));
        var take=UUID.randomUUID().toString();var other=UUID.randomUUID().toString();var jobs=List.of(job(a.id(),take),job(b.id(),other));
        store.synchronizeTakes(a.id(),jobs);var first=store.get(a.id());store.synchronizeTakes(a.id(),jobs);assertEquals(first,store.get(a.id()));
        assertEquals(List.of(take),first.project().scenes().getFirst().takeIds());assertEquals(List.of(),store.get(b.id()).project().scenes().getFirst().takeIds());
        store.synchronizeTakes(b.id(),jobs);assertEquals(List.of(other),store.get(b.id()).project().scenes().getFirst().takeIds());
    }
    @Test void invalidInputDoesNotWriteAndFailedSavesLeaveOriginalIntact() throws Exception {
        var store=store();var p=store.create(new Projects.Create(UUID.randomUUID().toString(),document("Keep this")));
        var scene=document("Text").scenes().getFirst();
        assertThrows(ResponseStatusException.class,()->store.save(p.id(),new Projects.Save(1,new ProjectDocument("Duplicate scenes",List.of(scene,scene)))));
        assertThrows(ResponseStatusException.class,()->store.save(p.id(),new Projects.Save(1,document("x".repeat(3001)))));
        assertEquals("Keep this",store.get(p.id()).project().scenes().getFirst().text());assertEquals(1,store.get(p.id()).revision());
        assertThrows(ResponseStatusException.class,()->store.get("../../outside"));assertThrows(ResponseStatusException.class,()->store.get(UUID.randomUUID().toString()));
    }
    @Test void automaticLinkingKeepsAnExplicitOldSelectionAfterMoreThanOneHundredTakes() throws Exception {
        var store=store();var created=store.create(new Projects.Create(UUID.randomUUID().toString(),document("Do not rewrite this draft.")));
        var completed=new ArrayList<Job>();for(int i=0;i<130;i++)completed.add(job(created.id(),new UUID(0,i+1).toString()));
        store.synchronizeTakes(created.id(),completed);var current=store.get(created.id());var scene=current.project().scenes().getFirst();var chosen=completed.getFirst().id();
        var ids=new ArrayList<>(scene.takeIds());ids.removeFirst();ids.addFirst(chosen);
        var selected=new ProjectDocument.Scene(scene.id(),scene.title(),scene.text(),scene.speechLanguage(),scene.emotion(),scene.temperature(),scene.seed(),scene.audioIndex(),scene.voiceId(),scene.presetVoice(),scene.voiceDescription(),ids,chosen,scene.assembly(),scene.voiceMode());
        var saved=store.save(created.id(),new Projects.Save(current.revision(),new ProjectDocument(current.project().title(),List.of(selected))));
        var newest=job(created.id(),new UUID(0,131).toString());completed.add(newest);store.synchronizeTakes(created.id(),completed);
        var reopened=store().get(created.id());var result=reopened.project().scenes().getFirst();assertEquals(chosen,result.selectedTakeId());assertTrue(result.takeIds().contains(chosen));assertTrue(result.takeIds().contains(newest.id()));assertEquals(100,result.takeIds().size());assertEquals(selected.text(),result.text());
        store.synchronizeTakes(created.id(),completed);assertEquals(reopened,store.get(created.id()));assertEquals(saved.revision()+1,reopened.revision());
    }
    @Test void aNewTakeFollowsItsSubmissionSelectionButNeverReplacesALaterManualChoice() throws Exception {
        var store=store();var p=store.create(new Projects.Create(UUID.randomUUID().toString(),document("Keep exact draft")));var a=job(p.id(),UUID.randomUUID().toString());var b=job(p.id(),UUID.randomUUID().toString());store.synchronizeTakes(p.id(),List.of(a,b));
        var base=store.get(p.id());var scene=base.project().scenes().getFirst();var manuallySelected=new ProjectDocument.Scene(scene.id(),scene.title(),scene.text(),scene.speechLanguage(),scene.emotion(),scene.temperature(),scene.seed(),scene.audioIndex(),scene.voiceId(),scene.presetVoice(),scene.voiceDescription(),scene.takeIds(),a.id(),scene.assembly(),scene.voiceMode());store.save(p.id(),new Projects.Save(base.revision(),new ProjectDocument(base.project().title(),List.of(manuallySelected))));
        var pending=job(p.id(),UUID.randomUUID().toString());pending=new Job(pending.id(),pending.request().withSelectionAtSubmission(b.id()),pending.status(),pending.stage(),pending.part(),pending.total(),pending.createdAt(),pending.completedAt(),pending.error(),pending.result());store.synchronizeTakes(p.id(),List.of(a,b,pending));assertEquals(a.id(),store.get(p.id()).project().scenes().getFirst().selectedTakeId());
        var next=job(p.id(),UUID.randomUUID().toString());next=new Job(next.id(),next.request().withSelectionAtSubmission(a.id()),next.status(),next.stage(),next.part(),next.total(),next.createdAt(),next.completedAt(),next.error(),next.result());store.synchronizeTakes(p.id(),List.of(a,b,pending,next));assertEquals(next.id(),store.get(p.id()).project().scenes().getFirst().selectedTakeId());assertEquals("Keep exact draft",store.get(p.id()).project().scenes().getFirst().text());
    }
}
