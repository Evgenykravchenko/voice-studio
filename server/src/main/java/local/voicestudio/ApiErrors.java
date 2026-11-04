package local.voicestudio;

import java.io.IOException;
import java.util.Map;
import org.springframework.http.*;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.converter.HttpMessageNotReadableException;

@RestControllerAdvice
public class ApiErrors {
    @ExceptionHandler(ResponseStatusException.class) public ResponseEntity<?> status(ResponseStatusException e) {
        return ResponseEntity.status(e.getStatusCode()).contentType(MediaType.APPLICATION_JSON).body(Map.of("error", e.getReason() == null ? "Запрос не выполнен." : e.getReason()));
    }
    @ExceptionHandler({MethodArgumentNotValidException.class, HttpMessageNotReadableException.class}) public ResponseEntity<?> invalid(Exception e) {
        return ResponseEntity.badRequest().contentType(MediaType.APPLICATION_JSON).body(Map.of("error", "Проверьте текст (1–3000 символов), профиль, эмоцию и целочисленный seed от 0 до 4294967295."));
    }
    @ExceptionHandler(org.springframework.web.multipart.MaxUploadSizeExceededException.class) public ResponseEntity<?> uploadTooLarge(Exception e) {
        return ResponseEntity.status(413).contentType(MediaType.APPLICATION_JSON).body(Map.of("error", "Размер аудиофайла не должен превышать 50 МБ."));
    }
    @ExceptionHandler({org.springframework.web.method.annotation.MethodArgumentTypeMismatchException.class, org.springframework.web.bind.MissingServletRequestParameterException.class, org.springframework.web.multipart.support.MissingServletRequestPartException.class}) public ResponseEntity<?> invalidUpload(Exception e) {
        return ResponseEntity.badRequest().contentType(MediaType.APPLICATION_JSON).body(Map.of("error", "Выберите запись, имя, язык и фрагмент от 5 до 30 секунд."));
    }
    @ExceptionHandler(java.sql.SQLException.class) public ResponseEntity<?> database(java.sql.SQLException e) {
        return ResponseEntity.status(503).contentType(MediaType.APPLICATION_JSON).body(Map.of("error", "Не удалось сохранить или прочитать базу проектов. Проверьте свободное место и повторите."));
    }
    @ExceptionHandler(IOException.class) public ResponseEntity<?> disk(IOException e) {
        return ResponseEntity.status(503).contentType(MediaType.APPLICATION_JSON).body(Map.of("error", "Не удалось прочитать или сохранить данные проекта."));
    }
}
