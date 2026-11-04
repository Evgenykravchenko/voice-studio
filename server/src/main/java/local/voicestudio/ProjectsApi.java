package local.voicestudio;

import java.sql.SQLException;
import java.util.List;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/projects")
public class ProjectsApi {
    private final Projects projects;
    private final Jobs jobs;
    public ProjectsApi(Projects projects,Jobs jobs){this.projects=projects;this.jobs=jobs;}
    @GetMapping public List<Projects.Summary> list() throws SQLException {return projects.list();}
    @GetMapping("/{id}") public Projects.Stored get(@PathVariable String id) throws SQLException {projects.synchronizeTakes(id,jobs.completedForProject(id));return projects.get(id);}
    @PostMapping(consumes=MediaType.APPLICATION_JSON_VALUE) @ResponseStatus(HttpStatus.CREATED)
    public Projects.Stored create(@RequestBody Projects.Create request) throws SQLException {return projects.create(request);}
    @PostMapping(value="/migrate",consumes=MediaType.APPLICATION_JSON_VALUE)
    public Projects.Stored migrate(@RequestBody Projects.Migration request) throws SQLException {return projects.migrate(request.project());}
    @PutMapping(value="/{id}",consumes=MediaType.APPLICATION_JSON_VALUE)
    public Projects.Stored save(@PathVariable String id,@RequestBody Projects.Save request) throws SQLException {return projects.save(id,request);}
}
