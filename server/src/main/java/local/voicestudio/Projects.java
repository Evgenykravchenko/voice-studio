package local.voicestudio;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.time.Instant;
import java.util.*;
import jakarta.validation.Validator;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

/** SQLite is embedded in Java. Every successful response follows a committed transaction. */
@Service
public class Projects {
    public record Stored(String id, long revision, String createdAt, String updatedAt, ProjectDocument project) {}
    public record Summary(String id, long revision, String title, int sceneCount, String createdAt, String updatedAt) {}
    public record Create(String id, ProjectDocument project) {}
    public record Save(long revision, ProjectDocument project) {}
    public record Migration(ProjectDocument project) {}
    private final String url;
    private final ObjectMapper json;
    private final Validator validator;
    public Projects(StudioPaths paths,ObjectMapper json,Validator validator) throws IOException,SQLException {
        this.json=json;this.validator=validator;
        var data=paths.root().resolve("data/studio");Files.createDirectories(data);
        var natives=paths.root().resolve(".runtime/sqlite-native");Files.createDirectories(natives);
        System.setProperty("org.sqlite.tmpdir",natives.toString());
        url="jdbc:sqlite:"+data.resolve("studio.db");
        try(var connection=connection();var statement=connection.createStatement()) {
            statement.execute("PRAGMA journal_mode=WAL");
            statement.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY)");
            int version;try(var rows=statement.executeQuery("SELECT COALESCE(MAX(version),0) FROM schema_migrations")){rows.next();version=rows.getInt(1);}
            if(version>2)throw new IOException("Версия базы новее приложения. Обновите студию.");
            String[] migrations={"V1__projects.sql","V2__project_jobs.sql"};
            for(int next=version+1;next<=migrations.length;next++) {
                connection.setAutoCommit(false);
                try(var source=Projects.class.getResourceAsStream("/db/migration/"+migrations[next-1])) {
                    if(source==null)throw new IOException("Не найдена схема базы проектов.");
                    for(var sql:new String(source.readAllBytes(),StandardCharsets.UTF_8).split(";"))if(!sql.isBlank())statement.execute(sql);
                    statement.executeUpdate("INSERT INTO schema_migrations(version) VALUES("+next+")");connection.commit();
                }catch(Exception e){connection.rollback();throw e;}
            }
        }
    }
    private Connection connection() throws SQLException {
        var connection=DriverManager.getConnection(url);
        try(var statement=connection.createStatement()) {
            statement.execute("PRAGMA busy_timeout=5000");statement.execute("PRAGMA synchronous=FULL");statement.execute("PRAGMA foreign_keys=ON");
        }catch(SQLException e){connection.close();throw e;}
        return connection;
    }
    private String id(String value) {
        try {if(value==null || !UUID.fromString(value).toString().equals(value))throw new IllegalArgumentException();return value;}
        catch(IllegalArgumentException e){throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Проект не найден.");}
    }
    private String document(ProjectDocument project) {
        if(project==null || !validator.validate(project).isEmpty())throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Проверьте проект: название до 200 символов, до 500 сцен, текст сцены до 3000 символов.");
        var ids=new HashSet<String>();
        for(var scene:project.scenes()){
            if(!ids.add(scene.id()))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Идентификаторы сцен не должны повторяться.");
            if(scene.assembly()!=null && scene.assembly().edits()!=null)for(var edit:scene.assembly().edits().values())if(edit.end()!=null && edit.end()-edit.start()<.08-1e-6)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Оставьте в обрезанном фрагменте хотя бы 0,08 секунды.");
        }
        return json.writeValueAsString(project);
    }
    private String hash(String text) {
        try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8)));}
        catch(NoSuchAlgorithmException e){throw new IllegalStateException(e);}
    }
    public synchronized List<Summary> list() throws SQLException {
        var result=new ArrayList<Summary>();
        try(var connection=connection();var statement=connection.prepareStatement("SELECT id,revision,title,scene_count,created_at,updated_at FROM projects ORDER BY updated_at DESC,id" );var rows=statement.executeQuery()){
            while(rows.next())result.add(new Summary(rows.getString(1),rows.getLong(2),rows.getString(3),rows.getInt(4),rows.getString(5),rows.getString(6)));
        }return result;
    }
    private Stored read(Connection connection,String id) throws SQLException {
        try(var statement=connection.prepareStatement("SELECT revision,created_at,updated_at,document FROM projects WHERE id=?")){
            statement.setString(1,id);
            try(var rows=statement.executeQuery()){
                if(!rows.next())throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Проект не найден.");
                return new Stored(id,rows.getLong(1),rows.getString(2),rows.getString(3),json.readValue(rows.getString(4),ProjectDocument.class));
            }
        }
    }
    public synchronized Stored get(String value) throws SQLException {try(var connection=connection()){return read(connection,id(value));}}
    public synchronized Stored create(Create request) throws SQLException {
        if(request==null)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Передайте проект.");
        return create(id(request.id()),request.project(),false);
    }
    private Stored create(String id,ProjectDocument project,boolean migration) throws SQLException {
        var body=document(project);var hash=hash(body);var now=Instant.now().toString();
        try(var connection=connection()){
            connection.setAutoCommit(false);
            try {
                try(var statement=connection.prepareStatement("INSERT INTO projects(id,revision,title,scene_count,document,create_hash,created_at,updated_at) VALUES(?,1,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING")){
                    statement.setString(1,id);statement.setString(2,project.title());statement.setInt(3,project.scenes().size());statement.setString(4,body);statement.setString(5,hash);statement.setString(6,now);statement.setString(7,now);statement.executeUpdate();
                }
                if(!migration)try(var statement=connection.prepareStatement("SELECT create_hash FROM projects WHERE id=?")){
                    statement.setString(1,id);try(var rows=statement.executeQuery()){rows.next();if(!hash.equals(rows.getString(1)))throw new ResponseStatusException(HttpStatus.CONFLICT,"Этот идентификатор уже занят другим проектом.");}
                }
                var result=read(connection,id);connection.commit();return result;
            }catch(Exception e){connection.rollback();throw e;}
        }
    }
    public synchronized Stored migrate(ProjectDocument project) throws SQLException {
        var digest=hash(document(project));
        var id=UUID.nameUUIDFromBytes(("voice-studio-legacy:"+digest).getBytes(StandardCharsets.UTF_8)).toString();
        // Repeated browser migrations return the current server revision, never the old draft.
        return create(id,project,true);
    }
    public synchronized Stored save(String value,Save request) throws SQLException {
        var id=id(value);
        if(request==null || request.revision()<1)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Укажите версию проекта.");
        var body=document(request.project());
        try(var connection=connection()){
            connection.setAutoCommit(false);
            try {
                try(var statement=connection.prepareStatement("UPDATE projects SET revision=revision+1,title=?,scene_count=?,document=?,updated_at=? WHERE id=? AND revision=?")){
                    statement.setString(1,request.project().title());statement.setInt(2,request.project().scenes().size());statement.setString(3,body);statement.setString(4,Instant.now().toString());statement.setString(5,id);statement.setLong(6,request.revision());
                    if(statement.executeUpdate()!=1){read(connection,id);throw new ResponseStatusException(HttpStatus.CONFLICT,"Проект изменён в другой вкладке. Сохраните свою копию или загрузите серверную версию.");}
                }
                var result=read(connection,id);connection.commit();return result;
            }catch(Exception e){connection.rollback();throw e;}
        }
    }
    public synchronized void synchronizeTakes(String value,List<Job> completed) throws SQLException {
        var id=id(value);
        if(completed.isEmpty())return;
        try(var connection=connection()) {
            connection.setAutoCommit(false);
            try {
                var stored=read(connection,id);var linked=new HashSet<String>();
                try(var statement=connection.prepareStatement("SELECT job_id FROM project_jobs WHERE project_id=?")) {
                    statement.setString(1,id);try(var rows=statement.executeQuery()){while(rows.next())linked.add(rows.getString(1));}
                }
                var pending=completed.stream().filter(job->id.equals(job.request().projectId()) && job.status().equals("succeeded") && !linked.contains(job.id())).sorted(Comparator.comparing(Job::createdAt)).toList();
                var scenes=new ArrayList<ProjectDocument.Scene>();boolean changed=false;
                for(var scene:stored.project().scenes()) {
                    var ids=new ArrayList<>(scene.takeIds()==null?List.<String>of():scene.takeIds());String selected=scene.selectedTakeId();boolean chooseFirst=selected==null;boolean added=false;
                    var followSelections=new HashSet<String>();followSelections.add(selected!=null?selected:scene.audioIndex()!=null?"demo-"+scene.audioIndex():"none");
                    for(var job:pending)if(job.request().sceneId().equals(scene.id())) {
                        if(!ids.contains(job.id())){ids.add(job.id());if(job.request().selectionAtSubmission()!=null?followSelections.contains(job.request().selectionAtSubmission()):chooseFirst){selected=job.id();followSelections.add(selected);}added=true;}
                        try(var statement=connection.prepareStatement("INSERT INTO project_jobs(job_id,project_id) VALUES(?,?) ON CONFLICT(job_id) DO NOTHING")){statement.setString(1,job.id());statement.setString(2,id);statement.executeUpdate();}
                    }
                    if(added){changed=true;if(selected!=null && !ids.contains(selected))ids.addFirst(selected);while(ids.size()>100)ids.remove(Objects.equals(ids.getFirst(),selected)?1:0);scenes.add(new ProjectDocument.Scene(scene.id(),scene.title(),scene.text(),scene.speechLanguage(),scene.emotion(),scene.temperature(),scene.seed(),scene.audioIndex(),scene.voiceId(),scene.presetVoice(),scene.voiceDescription(),ids,selected,scene.assembly(),scene.voiceMode()));}
                    else scenes.add(scene);
                }
                if(changed)try(var statement=connection.prepareStatement("UPDATE projects SET document=?,revision=revision+1,updated_at=? WHERE id=?")) {
                    statement.setString(1,document(new ProjectDocument(stored.project().title(),scenes,stored.project().mix())));statement.setString(2,Instant.now().toString());statement.setString(3,id);statement.executeUpdate();
                }
                connection.commit();
            }catch(Exception e){connection.rollback();throw e;}
        }
    }

}
