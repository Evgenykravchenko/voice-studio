package local.voicestudio;

import java.io.IOException;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.Test;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class ApiErrorsTest {
    @RestController static class FailedAudio {
        @GetMapping("/test-audio") void audio(HttpServletResponse response) throws IOException {
            response.setContentType("audio/wav");
            throw new IOException("Private file path must not reach the response");
        }
    }
    @Test void aReadFailureAfterAudioHeadersReturnsAJsonError() throws Exception {
        var mvc=MockMvcBuilders.standaloneSetup(new FailedAudio()).setControllerAdvice(new ApiErrors()).build();
        mvc.perform(get("/test-audio").accept("audio/*").header("Range","bytes=0-63"))
            .andExpect(status().isServiceUnavailable())
            .andExpect(content().contentTypeCompatibleWith("application/json"))
            .andExpect(jsonPath("$.error").value("Не удалось прочитать или сохранить данные проекта."));
    }
}
