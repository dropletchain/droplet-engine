package ch.ethz.blokcaditapi;

/**
 * Created by lukas on 12.05.17.
 */

public class BlockAditStreamException extends Exception {
    public BlockAditStreamException() {
    }

    public BlockAditStreamException(String detailMessage) {
        super(detailMessage);
    }

    public BlockAditStreamException(String detailMessage, Throwable throwable) {
        super(detailMessage, throwable);
    }

    public BlockAditStreamException(Throwable throwable) {
        super(throwable);
    }
}
