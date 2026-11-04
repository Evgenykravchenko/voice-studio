package local.voicestudio;

import java.util.function.Consumer;

public interface SpeechWorker extends AutoCloseable {
    record Progress(String stage, int part, int total) {}
    Job.Result generate(String id, GenerationRequest request, Consumer<Progress> progress) throws Exception;
    record PreparedVoice(String transcript, double duration, java.util.List<String> warnings) {}
    default PreparedVoice prepareVoice(String id, double start, double duration, String language, Consumer<Progress> progress) throws Exception { throw new UnsupportedOperationException("Подготовка голоса недоступна."); }
    default PreparedVoice prepareVoice(String id, double start, double duration, String language, String modelId, Consumer<Progress> progress) throws Exception { return prepareVoice(id,start,duration,language,progress); }
    default void cancelCurrent() {}
    default boolean isAlive() { return false; }
    default void close() {}
}
