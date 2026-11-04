package local.voicestudio;

import java.io.*;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.sql.SQLException;
import org.springframework.stereotype.Service;
import org.springframework.http.HttpStatus;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

/** Explicit, non-destructive restoration. Processing never selects a take on its own. */
@Service
public class Cleanups {
    public record Options(int strength,int clarity,int warmth,int deEss,boolean leveling,boolean protectPeaks,Integer noiseReduction) {
        public Options(int strength,int clarity,int warmth,int deEss,boolean leveling,boolean protectPeaks){this(strength,clarity,warmth,deEss,leveling,protectPeaks,null);}
        public Options {if(noiseReduction!=null && (noiseReduction<0 || noiseReduction>100))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Проверьте уровень удаления шума.");if(strength<0 || strength>100 || clarity<0 || clarity>100 || warmth< -100 || warmth>100 || deEss<0 || deEss>100)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Проверьте значения настроек улучшения.");}
        public static Options defaults(){return new Options(30,20,0,35,true,true,100);}
    }
    public record Task(String id,String kind,String projectId,String sceneId,String originalSourceId,String assemblyId,String sourceId,String title,String sourceText,String createdAt,Options options,String baseId) {}
    public record Comparison(String beforeUrl,String afterUrl) {}
    public record View(Task task,Job job,String beforeUrl,boolean applied,Comparison comparison) {}
    public record HistoryPage(List<View> items,int total,int page,int size) {}
    public record Source(String projectId,String sceneId,String sourceId,String assemblyId,Options options) {
        public Source(String projectId,String sceneId,String sourceId,String assemblyId){this(projectId,sceneId,sourceId,assemblyId,null);}
    }
    public record Apply(long revision) {}
    private final StudioPaths paths;private final Projects projects;private final Assemblies assemblies;private final Jobs jobs;private final ModelCatalog models;private final MediaInputs inputs;private final ObjectMapper json;
    private final Map<String,Task> tasks=new LinkedHashMap<>();
    public Cleanups(StudioPaths paths,Projects projects,Assemblies assemblies,Jobs jobs,ModelCatalog models,MediaInputs inputs,ObjectMapper json)throws IOException{
        this.paths=paths;this.projects=projects;this.assemblies=assemblies;this.jobs=jobs;this.models=models;this.inputs=inputs;this.json=json;
        Files.createDirectories(base());try(var files=Files.list(base())){for(var file:files.filter(p->p.toString().endsWith(".json")).toList())try{var task=json.readValue(file.toFile(),Task.class);tasks.put(task.id(),task);}catch(Exception ignored){System.err.println("Skipping invalid cleanup metadata");}}
    }
    private Path base(){return paths.root().resolve("data/studio/cleanups");}
    private Task task(String id){var task=tasks.get(id);if(task==null)throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Обработка не найдена.");return task;}
    private Path input(Task t){return paths.root().resolve("data/studio/inputs").resolve(t.sourceId());}
    private void save(Task task)throws IOException{var file=base().resolve(task.id()+".json");var tmp=base().resolve(task.id()+".tmp");json.writeValue(tmp.toFile(),task);Files.move(tmp,file,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);tasks.put(task.id(),task);}
    private Job job(Task t){try{return jobs.get(t.id());}catch(ResponseStatusException e){return new Job(t.id(),null,"failed","failed",0,0,t.createdAt(),null,"Отправка прервалась. Повторите обработку.",null);}}
    public synchronized View get(String id)throws SQLException{var t=task(id);boolean applied=false;if(t.kind().equals("scene"))try{applied=projects.get(t.projectId()).project().scenes().stream().anyMatch(s->s.id().equals(t.sceneId()) && s.takeIds()!=null && s.takeIds().contains(id));}catch(ResponseStatusException ignored){}var job=job(t);var comparison=job.status().equals("succeeded") && Files.isRegularFile(paths.audio().resolve(id+".compare-before.wav")) && Files.isRegularFile(paths.audio().resolve(id+".compare-after.wav"))?new Comparison("/api/cleanups/"+id+"/comparison/before","/api/cleanups/"+id+"/comparison/after"):null;return new View(t,job,"/api/cleanups/"+id+"/before",applied,comparison);}
    public synchronized List<View> list()throws SQLException{var result=new ArrayList<View>();for(var t:tasks.values().stream().sorted(Comparator.comparing(Task::createdAt).reversed()).limit(100).toList())result.add(get(t.id()));return result;}
    public synchronized HistoryPage history(String query,int page,int size)throws SQLException{
        if(query==null || query.length()>200 || page<1 || !List.of(6,12,24).contains(size))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Проверьте параметры истории.");
        var search=query.strip().toLowerCase(Locale.ROOT).replace('ё','е');
        var matching=tasks.values().stream().filter(t->t.title().toLowerCase(Locale.ROOT).replace('ё','е').contains(search)).sorted(Comparator.comparing(Task::createdAt).thenComparing(Task::id).reversed()).toList();
        int current=Math.min(page,Math.max(1,(matching.size()+size-1)/size));var result=new ArrayList<View>();
        for(var t:matching.stream().skip((long)(current-1)*size).limit(size).toList())result.add(get(t.id()));
        return new HistoryPage(result,matching.size(),current,size);
    }
    private View start(String kind,String projectId,String sceneId,String original,String assemblyId,String sourceId,String title,String text,Options options,String baseId,Long seed)throws IOException,SQLException{
        var id=UUID.randomUUID().toString();var effective=options==null?Options.defaults():options;boolean separate=effective.noiseReduction()!=null;
        var cache=baseId!=null && (separate?Files.isRegularFile(paths.audio().resolve(baseId+".denoised.wav")) && Files.isRegularFile(paths.audio().resolve(baseId+".natural-restored.wav")):Files.isRegularFile(paths.audio().resolve(baseId+".restored.wav")));
        if(!separate && !cache && baseId!=null && tasks.containsKey(baseId) && task(baseId).options()==null && Files.isRegularFile(paths.audio().resolve(baseId+".wav")))cache=true;
        var request=new GenerationRequest("cleanup-"+id,title,"",null,"calm","auto",seed,"resemble-enhance",null,null,sourceId,null,null);
        if(!cache)request=models.prepare(request);
        var t=new Task(id,kind,projectId,sceneId,original,assemblyId,sourceId,title,text,Instant.now().toString(),effective,baseId==null?id:baseId);
        json.writeValue(input(t).resolve("cleanup.json").toFile(),Map.of("maxDuration",7200));save(t);
        jobs.submitWithId(id,new GenerationRequest(request.sceneId(),title,text,null,"calm","auto",request.seed(),request.modelId(),null,null,sourceId,null,null));return get(id);
    }
    private String copy(Path source)throws IOException{var id=UUID.randomUUID().toString();var folder=paths.root().resolve("data/studio/inputs").resolve(id);Files.createDirectories(folder);Files.copy(source,folder.resolve("source"));return id;}
    public synchronized View upload(MultipartFile file)throws IOException,SQLException{return upload(file,null);}
    public synchronized View upload(MultipartFile file,Options options)throws IOException,SQLException{var source=inputs.upload(file).get("id");var name=Objects.requireNonNullElse(file.getOriginalFilename(),"Аудиозапись");name=Path.of(name).getFileName().toString();return start("upload",null,null,null,null,source,name.substring(0,Math.min(170,name.length())),"",options,null,null);}
    public synchronized View scene(Source request)throws IOException,SQLException{
        var project=projects.get(request.projectId()).project();var scene=project.scenes().stream().filter(s->s.id().equals(request.sceneId())).findFirst().orElseThrow(()->new ResponseStatusException(HttpStatus.NOT_FOUND,"Сцена не найдена."));
        var selected=scene.selectedTakeId()!=null?scene.selectedTakeId():scene.audioIndex()!=null?"demo-"+scene.audioIndex():null;
        if(selected==null || !selected.equals(request.sourceId()))throw new ResponseStatusException(HttpStatus.CONFLICT,"Выбранный дубль изменился. Откройте улучшение ещё раз.");
        Path source;String text="";
        if(selected.matches("demo-[0-2]")){source=paths.sampleAudio(scene.audioIndex());}
        else{var job=jobs.get(selected);if(!job.status().equals("succeeded"))throw new ResponseStatusException(HttpStatus.CONFLICT,"Дубль ещё не готов.");source=paths.audio().resolve(selected+".wav");text=job.request().text();}
        if(!Files.isRegularFile(source))throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Запись дубля не найдена.");
        return start("scene",request.projectId(),scene.id(),selected,null,copy(source),scene.title(),text,request.options(),null,null);
    }
    public synchronized View assembled(Source request)throws IOException,SQLException{
        if(request.assemblyId()==null)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Сначала соберите итоговую запись.");
        var task=assemblies.get(request.projectId(),request.assemblyId());var source=assemblies.audio(request.projectId(),task.id(),"wav");
        return start("final",request.projectId(),null,null,task.id(),copy(source),projects.get(request.projectId()).project().title(),"",request.options(),null,null);
    }
    public synchronized View retry(String id)throws IOException,SQLException{var t=task(id);if(List.of("queued","running").contains(job(t).status()))return get(id);return start(t.kind(),t.projectId(),t.sceneId(),t.originalSourceId(),t.assemblyId(),t.sourceId(),t.title(),t.sourceText(),t.options(),t.baseId()==null?t.id():t.baseId(),job(t).request()==null?null:job(t).request().seed());}
    public synchronized View tune(String id,Options options)throws IOException,SQLException{
        var t=task(id);var j=job(t);if(!j.status().equals("succeeded"))throw new ResponseStatusException(HttpStatus.CONFLICT,"Дождитесь готового результата перед настройкой.");
        String original=t.originalSourceId();
        if(t.kind().equals("scene"))try{var scene=projects.get(t.projectId()).project().scenes().stream().filter(v->v.id().equals(t.sceneId())).findFirst().orElse(null);
            if(scene!=null && scene.selectedTakeId()!=null){var selected=tasks.get(scene.selectedTakeId());if(selected!=null && Objects.equals(selected.projectId(),t.projectId()) && Objects.equals(selected.sceneId(),t.sceneId()) && selected.sourceId().equals(t.sourceId()))original=selected.id();}
        }catch(ResponseStatusException ignored){}
        return start(t.kind(),t.projectId(),t.sceneId(),original,t.assemblyId(),t.sourceId(),t.title(),t.sourceText(),options,t.baseId()==null?t.id():t.baseId(),j.request().seed());
    }
    public synchronized Path comparison(String id,String side){var t=task(id);if(!List.of("before","after").contains(side) || !job(t).status().equals("succeeded"))throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Сравнение ещё не готово.");var file=paths.audio().resolve(id+".compare-"+side+".wav");if(!Files.isRegularFile(file))throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Обновите обработку для сравнения на одной громкости.");return file;}
    public Options parseOptions(String value){if(value==null || value.isBlank())return Options.defaults();try{return json.readValue(value,Options.class);}catch(Exception e){throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Проверьте настройки улучшения.");}}
    public synchronized View cancel(String id)throws SQLException{var t=task(id);jobs.cancel(t.id());return get(id);}
    public synchronized Projects.Stored apply(String id,long revision)throws SQLException{
        var t=task(id);var j=job(t);if(!t.kind().equals("scene") || !j.status().equals("succeeded") || j.result()==null)throw new ResponseStatusException(HttpStatus.CONFLICT,"Сначала дождитесь готового результата сцены.");
        var stored=projects.get(t.projectId());var source=stored.project().scenes().stream().filter(s->s.id().equals(t.sceneId())).findFirst().orElseThrow(()->new ResponseStatusException(HttpStatus.NOT_FOUND,"Сцена удалена. Улучшенная запись доступна для скачивания."));
        if(source.takeIds()!=null && source.takeIds().contains(id))return stored;
        if(stored.revision()!=revision)throw new ResponseStatusException(HttpStatus.CONFLICT,"Проект изменился. Обновите его перед сохранением дубля.");
        var selected=source.selectedTakeId()!=null?source.selectedTakeId():source.audioIndex()!=null?"demo-"+source.audioIndex():null;
        if(!Objects.equals(selected,t.originalSourceId()))throw new ResponseStatusException(HttpStatus.CONFLICT,"В сцене уже выбран другой дубль. Выберите исходный дубль, чтобы применить этот результат.");
        var ids=new ArrayList<>(source.takeIds()==null?List.<String>of():source.takeIds());ids.add(id);while(ids.size()>100){int i=Objects.equals(ids.getFirst(),selected)?1:0;ids.remove(i);}
        var assembly=source.assembly();if(assembly!=null && assembly.edits()!=null && assembly.edits().containsKey(t.originalSourceId())){
            var edits=new LinkedHashMap<>(assembly.edits());edits.put(id,edits.get(t.originalSourceId()));while(edits.size()>103){var remove=edits.keySet().stream().filter(k->!k.equals(id) && !k.equals(t.originalSourceId())).findFirst().orElseThrow();edits.remove(remove);}assembly=new ProjectDocument.Assembly(assembly.excluded(),assembly.pauseAfter(),edits);
        }
        var replacement=new ProjectDocument.Scene(source.id(),source.title(),source.text(),source.speechLanguage(),source.emotion(),source.temperature(),source.seed(),source.audioIndex(),source.voiceId(),source.presetVoice(),source.voiceDescription(),ids,id,assembly,source.voiceMode());
        var scenes=stored.project().scenes().stream().map(s->s.id().equals(source.id())?replacement:s).toList();return projects.save(t.projectId(),new Projects.Save(revision,new ProjectDocument(stored.project().title(),scenes,stored.project().mix())));
    }
    public synchronized Path before(String id){var file=input(task(id)).resolve("before.wav");if(!Files.isRegularFile(file))throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Исходник подготавливается.");return file;}
}
