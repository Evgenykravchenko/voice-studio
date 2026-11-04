package local.voicestudio;

import java.util.List;
import java.util.Map;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonInclude;

/** A project snapshot keeps exact scene text and take IDs, without copying audio into SQL. */
public record ProjectDocument(
    @NotNull @Size(max=200) String title,
    @NotNull @Size(max=500) List<@NotNull @Valid Scene> scenes,
    @JsonInclude(JsonInclude.Include.NON_NULL) @Valid Mix mix
) {
    public ProjectDocument(String title,List<Scene> scenes){this(title,scenes,null);}
    public record Mix(@DecimalMin("0") @DecimalMax("5") Double gapSeconds, Boolean leveling, Boolean softEdges) {}
    public record ClipEdit(@NotNull @DecimalMin("0") @DecimalMax("7200") Double start,
        @DecimalMin("0") @DecimalMax("7200") Double end, @DecimalMin("-18") @DecimalMax("12") Double gainDb) {}
    public record Assembly(Boolean excluded, @DecimalMin("0") @DecimalMax("5") Double pauseAfter,
        @Size(max=103) Map<@Pattern(regexp="demo-[0-2]|[0-9a-f-]{36}") String,@NotNull @Valid ClipEdit> edits) {}
    public record Scene(
        @NotBlank @Size(max=100) String id,
        @NotNull @Size(max=200) String title,
        @NotNull @Size(max=3000) String text,
        @NotNull @Pattern(regexp="auto|[a-z]{2,3}(?:-[A-Za-z0-9]+)?") String speechLanguage,
        @NotNull @Pattern(regexp="calm|excited|whisper|laughing|angry") String emotion,
        @NotNull @DecimalMin("0.1") @DecimalMax("1.5") Double temperature,
        @NotNull @Size(max=32) String seed,
        @Min(0) @Max(2) Integer audioIndex,
        @JsonInclude(JsonInclude.Include.NON_NULL) @Pattern(regexp="[A-Za-z0-9][A-Za-z0-9_-]{0,63}") String voiceId,
        @JsonInclude(JsonInclude.Include.NON_NULL) @Size(max=64) String presetVoice,
        @JsonInclude(JsonInclude.Include.NON_NULL) @Size(max=1000) String voiceDescription,
        @JsonInclude(JsonInclude.Include.NON_NULL) @Size(max=100) List<@Pattern(regexp="[0-9a-f-]{36}") String> takeIds,
        @JsonInclude(JsonInclude.Include.NON_NULL) @Pattern(regexp="[0-9a-f-]{36}") String selectedTakeId,
        @JsonInclude(JsonInclude.Include.NON_NULL) @Valid Assembly assembly,
        @JsonInclude(JsonInclude.Include.NON_NULL) @Pattern(regexp="clone|preset|design|effect") String voiceMode
    ) {
        public Scene(String id,String title,String text,String speechLanguage,String emotion,Double temperature,String seed,Integer audioIndex,String voiceId,String presetVoice,String voiceDescription,List<String> takeIds,String selectedTakeId,Assembly assembly){this(id,title,text,speechLanguage,emotion,temperature,seed,audioIndex,voiceId,presetVoice,voiceDescription,takeIds,selectedTakeId,assembly,null);}
        public Scene(String id,String title,String text,String speechLanguage,String emotion,Double temperature,String seed,Integer audioIndex,String voiceId,String presetVoice,String voiceDescription,List<String> takeIds,String selectedTakeId){this(id,title,text,speechLanguage,emotion,temperature,seed,audioIndex,voiceId,presetVoice,voiceDescription,takeIds,selectedTakeId,null);}
    }
}
