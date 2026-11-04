package local.voicestudio;

import java.util.List;

public record VoiceImport(String id, String name, String language, double start, double requestedDuration,
    String status, String stage, String transcript, double duration, List<String> warnings, String error, String createdAt, String voiceId, String modelId) {
    public VoiceImport(String id,String name,String language,double start,double requestedDuration,String status,String stage,String transcript,double duration,List<String> warnings,String error,String createdAt,String voiceId) { this(id,name,language,start,requestedDuration,status,stage,transcript,duration,warnings,error,createdAt,voiceId,null); }
    public VoiceImport progress(String stage) { return new VoiceImport(id,name,language,start,requestedDuration,"running",stage,transcript,duration,warnings,null,createdAt,null,modelId); }
    public VoiceImport ready(SpeechWorker.PreparedVoice result) { return new VoiceImport(id,name,language,start,requestedDuration,"ready","review",result.transcript(),result.duration(),result.warnings(),null,createdAt,null,modelId); }
    public VoiceImport failed(String message) { return new VoiceImport(id,name,language,start,requestedDuration,"failed","error",transcript,duration,warnings,message,createdAt,null,modelId); }
    public VoiceImport saved(String profileId, String savedName, String text) { return new VoiceImport(id,savedName,language,start,requestedDuration,"saved","done",text,duration,warnings,null,createdAt,profileId,modelId); }
}
