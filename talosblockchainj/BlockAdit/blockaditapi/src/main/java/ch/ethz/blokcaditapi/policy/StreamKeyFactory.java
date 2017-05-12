package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.ECKey;

/**
 * Created by lukas on 11.05.17.
 */

public interface StreamKeyFactory {
    public StreamKey createStreamKey(ECKey owner);

    public StreamKey createShareStreamKey(ECKey share, byte[] input);
}
