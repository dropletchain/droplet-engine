package ch.ethz.blokcaditapi.policy;

/**
 * Created by lukas on 11.05.17.
 */

public class PolicyKeyException extends RuntimeException {
    public PolicyKeyException() {
        super();
    }

    public PolicyKeyException(String detailMessage) {
        super(detailMessage);
    }

    public PolicyKeyException(String detailMessage, Throwable throwable) {
        super(detailMessage, throwable);
    }

    public PolicyKeyException(Throwable throwable) {
        super(throwable);
    }
}
