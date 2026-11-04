package local.voicestudio;

import java.nio.file.*;
import java.util.List;
import java.util.concurrent.*;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

class VoiceProfilesTest {
    @TempDir Path root;
    private MockMultipartFile file() { return new MockMultipartFile("file","пример.mp3","audio/mpeg",new byte[]{1,2,3}); }
    private VoiceImport await(VoiceProfiles profiles, String id) throws Exception {
        long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(4);
        while(System.nanoTime()<deadline) { var task=profiles.get(id); if(List.of("ready","failed").contains(task.status())) return task; Thread.sleep(10); }
        throw new AssertionError("Preparation did not finish");
    }
    @Test void draftReviewAndAtomicCommitSurviveRestartAndDoNotOverwriteExistingVoice() throws Exception {
        var paths=new StudioPaths(root); var json=JsonMapper.builder().build();
        Files.createDirectories(paths.profiles().resolve("test-voice")); Files.writeString(paths.profiles().resolve("test-voice/profile.json"),"{}");
        SpeechWorker worker=new SpeechWorker() {
            public Job.Result generate(String id,GenerationRequest request,Consumer<Progress> progress) { throw new AssertionError(); }
            public PreparedVoice prepareVoice(String id,double start,double duration,String language,Consumer<Progress> progress) throws Exception {
                progress.accept(new Progress("transcribing",0,0));
                Files.write(root.resolve("data/studio/voice-imports/"+id+"/reference.wav"),new byte[]{1});
                return new PreparedVoice("Распознанный текст.",12,List.of());
            }
        };
        var queue=new Jobs(paths,json,worker);
        try {
            var profiles=new VoiceProfiles(paths,json,worker,queue);
            var task=await(profiles,profiles.upload(file(),"Мой голос",1,15,"ru").id());
            assertEquals("ready",task.status()); assertEquals(0,profiles.list().size());
            assertFalse(Files.exists(root.resolve("data/studio/voice-imports/"+task.id()+"/source")));
            var reopened=new VoiceProfiles(paths,json,worker,queue); assertEquals("ready",reopened.get(task.id()).status());
            var saved=reopened.save(task.id(),new VoiceProfiles.SaveVoice("Новый голос","Точная расшифровка — без изменений!"));
            assertEquals("saved",saved.status()); assertEquals(1,reopened.list().size());
            assertEquals("Точная расшифровка — без изменений!",reopened.list().getFirst().referenceText());
            assertEquals("{}",Files.readString(paths.profiles().resolve("test-voice/profile.json")));
            assertEquals(saved,reopened.save(task.id(),new VoiceProfiles.SaveVoice("Другое имя","Другой текст")));
            assertTrue(Files.isRegularFile(reopened.reference(saved.voiceId(),false)));
            var again=new VoiceProfiles(paths,json,worker,queue); assertEquals("saved",again.get(task.id()).status());
            assertEquals(0,again.tasks().size()); assertEquals(1,again.list().size());
            again.delete(saved.voiceId());
            assertTrue(again.list().isEmpty());
            assertThrows(ResponseStatusException.class,()->again.reference(saved.voiceId(),false));
            var afterDelete=new VoiceProfiles(paths,json,worker,queue);
            assertTrue(afterDelete.list().isEmpty());
            assertThrows(ResponseStatusException.class,()->afterDelete.get(task.id()));
            assertFalse(Files.exists(root.resolve("data/studio/voice-imports/"+task.id()+".json")));
        } finally { queue.stop(); }
    }
    @Test void invalidUploadsAndWorkerFailureNeverCreateUsableProfiles() throws Exception {
        var paths=new StudioPaths(root); var json=JsonMapper.builder().build();
        var worker=new SpeechWorker() {
            public Job.Result generate(String id,GenerationRequest request,Consumer<Progress> progress) { throw new AssertionError(); }
            public PreparedVoice prepareVoice(String id,double start,double duration,String language,Consumer<Progress> progress) { throw new IllegalArgumentException("В записи тишина."); }
        };
        var queue=new Jobs(paths,json,worker);
        try {
            var profiles=new VoiceProfiles(paths,json,worker,queue);
            assertThrows(ResponseStatusException.class,()->profiles.upload(file(),"",0,20,"ru"));
            assertThrows(ResponseStatusException.class,()->profiles.upload(file(),"Имя",Double.NaN,20,"ru"));
            assertThrows(ResponseStatusException.class,()->profiles.upload(file(),"Имя",0,31,"ru"));
            assertThrows(ResponseStatusException.class,()->profiles.upload(new MockMultipartFile("file","file.html","text/html",new byte[]{1}),"Имя",0,20,"ru"));
            var failed=await(profiles,profiles.upload(file(),"Имя",0,20,"ru").id());
            assertEquals("failed",failed.status()); assertEquals("В записи тишина.",failed.error());
            assertEquals(0,profiles.list().size());
            assertThrows(ResponseStatusException.class,()->profiles.save(failed.id(),new VoiceProfiles.SaveVoice("Имя","Текст")));
            profiles.discard(failed.id()); assertTrue(profiles.tasks().isEmpty());
            assertThrows(ResponseStatusException.class,()->profiles.reference("../other",false));
        } finally { queue.stop(); }
    }
    @Test void preparationAndSynthesisUseTheSameQueue() throws Exception {
        var paths=new StudioPaths(root); var json=JsonMapper.builder().build(); var started=new CountDownLatch(1); var release=new CountDownLatch(1);
        var worker=(SpeechWorker)(id,req,progress)->{ throw new AssertionError(); };
        var queue=new Jobs(paths,json,worker);
        try {
            queue.enqueue(()->{ started.countDown(); try { release.await(3,TimeUnit.SECONDS); } catch(InterruptedException e) { Thread.currentThread().interrupt(); } });
            assertTrue(started.await(1,TimeUnit.SECONDS));
            var profiles=new VoiceProfiles(paths,json,worker,queue); var task=profiles.upload(file(),"Имя",0,20,"ru");
            assertEquals("queued",profiles.get(task.id()).status());
            assertThrows(ResponseStatusException.class,()->profiles.discard(task.id()));
            release.countDown(); assertEquals("failed",await(profiles,task.id()).status());
        } finally { release.countDown(); queue.stop(); }
    }
    @Test void queuedPreparationKeepsTheSelectedRecognizerAndItsMetadataAcrossRestart() throws Exception {
        var paths=new StudioPaths(root); var json=JsonMapper.builder().build();
        var current=new java.util.concurrent.atomic.AtomicReference<>("recognizer-a");
        var used=new java.util.concurrent.atomic.AtomicReference<String>();
        var started=new CountDownLatch(1); var release=new CountDownLatch(1);
        var catalog=new ModelCatalog(paths,json) {
            @Override public String transcriptionModelId(String language) { return current.get(); }
        };
        var worker=new SpeechWorker() {
            public Job.Result generate(String id,GenerationRequest request,Consumer<Progress> progress) { throw new AssertionError(); }
            public PreparedVoice prepareVoice(String id,double start,double duration,String language,String modelId,Consumer<Progress> progress) throws Exception {
                used.set(modelId); Files.write(root.resolve("data/studio/voice-imports/"+id+"/reference.wav"),new byte[]{1});
                return new PreparedVoice("Точная речь.",8,List.of());
            }
        };
        var queue=new Jobs(paths,json,worker);
        try {
            queue.enqueue(()->{started.countDown();try{release.await(3,TimeUnit.SECONDS);}catch(InterruptedException e){Thread.currentThread().interrupt();}});
            assertTrue(started.await(1,TimeUnit.SECONDS));
            var profiles=new VoiceProfiles(paths,json,worker,queue,catalog);
            var task=profiles.upload(file(),"Новый голос",0,8,"ru");
            assertEquals("recognizer-a",task.modelId()); current.set("recognizer-b"); release.countDown();
            assertEquals("ready",await(profiles,task.id()).status()); assertEquals("recognizer-a",used.get());
            var reopened=new VoiceProfiles(paths,json,worker,queue,catalog);
            assertEquals("recognizer-a",reopened.get(task.id()).modelId());
            assertEquals("recognizer-a",reopened.save(task.id(),new VoiceProfiles.SaveVoice("Голос","Точная речь.")).modelId());
        } finally {release.countDown();queue.stop();catalog.stop();}
    }

    @Test void japaneseReferenceLanguageIsValidatedBeforeQueueingAndPersistsThroughReviewAndRestart() throws Exception {
        var paths=new StudioPaths(root); var json=JsonMapper.builder().build();
        var catalog=new ModelCatalog(paths,json) {
            @Override public String transcriptionModelId(String language) {
                if(!language.equals("ja")) throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"Unsupported language");
                return "japanese-recognizer";
            }
        };
        var worker=new SpeechWorker() {
            public Job.Result generate(String id,GenerationRequest request,Consumer<Progress> progress) { throw new AssertionError(); }
            public PreparedVoice prepareVoice(String id,double start,double duration,String language,String modelId,Consumer<Progress> progress) throws Exception {
                assertEquals("ja",language); assertEquals("japanese-recognizer",modelId);
                Files.write(root.resolve("data/studio/voice-imports/"+id+"/reference.wav"),new byte[]{1});
                return new PreparedVoice("こんにちは。",8,List.of());
            }
        };
        var queue=new Jobs(paths,json,worker);
        try {
            var profiles=new VoiceProfiles(paths,json,worker,queue,catalog);
            for(var language:List.of("", "../ja", "Japanese", "ja\n", "en"))
                assertThrows(ResponseStatusException.class,()->profiles.upload(file(),"Test voice",0,8,language));
            assertThrows(ResponseStatusException.class,()->profiles.upload(file(),"Test voice",0,8,null));
            assertTrue(profiles.tasks().isEmpty());
            try(var entries=Files.list(root.resolve("data/studio/voice-imports"))) { assertEquals(0,entries.count()); }
            var ready=await(profiles,profiles.upload(file(),"Test voice",0,8,"ja").id());
            assertEquals("ready",ready.status()); assertEquals("ja",ready.language());
            profiles.save(ready.id(),new VoiceProfiles.SaveVoice("Test voice","こんにちは。"));
            var reopened=new VoiceProfiles(paths,json,worker,queue,catalog);
            assertEquals("ja",reopened.list().getFirst().language());
            assertEquals("こんにちは。",reopened.list().getFirst().referenceText());
        } finally { queue.stop(); catalog.stop(); }
    }

}
