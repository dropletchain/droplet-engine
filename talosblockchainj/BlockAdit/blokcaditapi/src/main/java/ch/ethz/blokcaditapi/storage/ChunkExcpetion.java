package ch.ethz.blokcaditapi.storage;

/**
 * Created by lukas on 09.05.17.
 */

public class ChunkExcpetion extends RuntimeException {
    public ChunkExcpetion(String detailMessage) {
        super(detailMessage);
    }
}
