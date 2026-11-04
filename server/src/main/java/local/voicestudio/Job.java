package local.voicestudio;

import java.time.Instant;
import java.util.List;

public record Job(String id, GenerationRequest request, String status, String stage,
                  int part, int total, String createdAt, String completedAt, String error, Result result) {
    public record Result(String id, String url, double duration, int sampleRate, List<Double> peaks, long seed, Double temperature) {}
    public Job progress(String stage, int part, int total) {
        return new Job(id, request, "running", stage, part, total, createdAt, null, null, null);
    }
    public Job success(Result result) {
        return new Job(id, request, "succeeded", "done", total, total, createdAt, Instant.now().toString(), null, result);
    }
    public Job failed(String error) {
        return new Job(id, request, "failed", "failed", part, total, createdAt, Instant.now().toString(), error, null);
    }
}
