package local.voicestudio;

import java.io.IOException;
import java.nio.file.*;
import java.nio.channels.FileChannel;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

@Service
public class ModelImports {
    private final StudioPaths paths;
    private final ModelCatalog catalog;
    public ModelImports(StudioPaths paths,ModelCatalog catalog){this.paths=paths;this.catalog=catalog;}
    public synchronized ModelCatalog.Transfer finish(String id) throws IOException{return catalog.importModel(id);}
    public synchronized Map<String,Long> chunk(String id,String name,long offset,MultipartFile file) throws IOException {
        if(catalog.transferActive(id))throw new ResponseStatusException(HttpStatus.CONFLICT,"Дождитесь завершения проверки модели.");
        var manifest=catalog.manifest(id);
        long expected=-1;
        for(var item:manifest.path("files"))if(item.path("path").asString().equals(name)){expected=item.path("size").asLong();break;}
        if(expected<0 || offset<0 || file.isEmpty() || file.getSize()>20*1024*1024 || offset+file.getSize()>expected)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Файл или размер не соответствует выбранной модели.");
        var directory=paths.root().resolve("data/studio/model-imports").resolve(id).normalize();
        var target=directory.resolve(name).normalize();
        if(!target.startsWith(directory) || name.contains("\\"))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Неверный путь файла.");
        Files.createDirectories(target.getParent());
        if(offset==0)Files.deleteIfExists(target);
        if((Files.exists(target)?Files.size(target):0)!=offset)throw new ResponseStatusException(HttpStatus.CONFLICT,"Импорт прерван. Выберите папку заново.");
        if(Files.getFileStore(directory).getUsableSpace()<file.getSize()+100_000_000)throw new ResponseStatusException(HttpStatus.CONFLICT,"Недостаточно свободного места для импорта.");
        try(var input=file.getInputStream();var output=Files.newOutputStream(target,StandardOpenOption.CREATE,StandardOpenOption.APPEND)){input.transferTo(output);}
        return Map.of("received",offset+file.getSize());
    }
}
