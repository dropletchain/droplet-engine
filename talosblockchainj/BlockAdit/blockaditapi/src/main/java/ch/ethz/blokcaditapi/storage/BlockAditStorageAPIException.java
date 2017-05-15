package ch.ethz.blokcaditapi.storage;

/**
 * Created by lukas on 15.05.17.
 */

public class BlockAditStorageAPIException extends Exception {
    public BlockAditStorageAPIException() {
    }

    public BlockAditStorageAPIException(String detailMessage) {
        super(detailMessage);
    }

    public BlockAditStorageAPIException(String detailMessage, Throwable throwable) {
        super(detailMessage, throwable);
    }

    public BlockAditStorageAPIException(Throwable throwable) {
        super(throwable);
    }
}
