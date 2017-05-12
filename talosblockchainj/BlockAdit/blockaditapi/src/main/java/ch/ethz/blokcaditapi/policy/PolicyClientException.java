package ch.ethz.blokcaditapi.policy;

/**
 * Created by lukas on 09.05.17.
 */

public class PolicyClientException extends Exception {
    public PolicyClientException() {
    }

    public PolicyClientException(String detailMessage) {
        super(detailMessage);
    }

    public PolicyClientException(String detailMessage, Throwable throwable) {
        super(detailMessage, throwable);
    }

    public PolicyClientException(Throwable throwable) {
        super(throwable);
    }
}
