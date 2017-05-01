package ch.lubu;

/**
 * Created by lukas on 24.02.17.
 */
public class Entry {

    private long timestamp;

    private String metadata;

    private double value;

    public Entry(long timestamp, String metadata, double value) {
        this.timestamp = timestamp;
        this.metadata = metadata;
        this.value = value;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public String getMetadata() {
        return metadata;
    }

    public double getValue() {
        return value;
    }
}
