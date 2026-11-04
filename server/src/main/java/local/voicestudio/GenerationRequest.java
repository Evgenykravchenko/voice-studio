package local.voicestudio;

import jakarta.validation.constraints.*;

public record GenerationRequest(
    @NotBlank @Size(max=100) String sceneId,
    @NotBlank @Size(max=200) String title,
    @NotNull @Size(max=3000) String text,
    @Pattern(regexp="[A-Za-z0-9][A-Za-z0-9_-]{0,63}") String voiceId,
    @NotBlank @Pattern(regexp="calm|excited|whisper|laughing|angry") String emotion,
    @NotBlank @Pattern(regexp="auto|[a-z]{2,3}(?:-[A-Za-z0-9]+)?") String language,
    @Min(0) @Max(4294967295L) Long seed,
    @Pattern(regexp="[a-z0-9-]{1,64}") String modelId,
    @Size(max=64) String presetVoice,
    @Size(max=1000) String voiceDescription,
    @Pattern(regexp="[0-9a-f-]{36}") String sourceId,
    @DecimalMin("1") @DecimalMax("30") Double durationSeconds,
    @Pattern(regexp="[0-9a-f-]{36}") String projectId,
    @Pattern(regexp="clone|preset|design|effect") String voiceMode,
    @com.fasterxml.jackson.annotation.JsonInclude(com.fasterxml.jackson.annotation.JsonInclude.Include.NON_NULL)
    @Pattern(regexp="none|demo-[0-2]|[0-9a-f-]{36}") String selectionAtSubmission
) {
    public GenerationRequest(String sceneId,String title,String text,String voiceId,String emotion,String language,Long seed,String modelId,String presetVoice,String voiceDescription,String sourceId,Double durationSeconds,String projectId,String voiceMode) {
        this(sceneId,title,text,voiceId,emotion,language,seed,modelId,presetVoice,voiceDescription,sourceId,durationSeconds,projectId,voiceMode,null);
    }
    public GenerationRequest withSelectionAtSubmission(String selected) {
        return new GenerationRequest(sceneId,title,text,voiceId,emotion,language,seed,modelId,presetVoice,voiceDescription,sourceId,durationSeconds,projectId,voiceMode,selected);
    }
    public GenerationRequest(String sceneId,String title,String text,String voiceId,String emotion,String language,Long seed,String modelId,String presetVoice,String voiceDescription,String sourceId,Double durationSeconds,String projectId) {
        this(sceneId,title,text,voiceId,emotion,language,seed,modelId,presetVoice,voiceDescription,sourceId,durationSeconds,projectId,null);
    }
    public GenerationRequest(String sceneId, String title, String text, String voiceId, String emotion, String language, Long seed) {
        this(sceneId,title,text,voiceId,emotion,language,seed,null,null,null,null,null,null);
    }
    public GenerationRequest(String sceneId,String title,String text,String voiceId,String emotion,String language,Long seed,String modelId,String presetVoice,String voiceDescription) {
        this(sceneId,title,text,voiceId,emotion,language,seed,modelId,presetVoice,voiceDescription,null,null,null);
    }
    public GenerationRequest(String sceneId,String title,String text,String voiceId,String emotion,String language,Long seed,String modelId,String presetVoice,String voiceDescription,String sourceId,Double durationSeconds) {
        this(sceneId,title,text,voiceId,emotion,language,seed,modelId,presetVoice,voiceDescription,sourceId,durationSeconds,null);
    }

}
