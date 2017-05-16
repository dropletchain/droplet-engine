package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;

/**
 * Created by lukas on 11.05.17.
 */

public interface StreamKeyFactory {
    public StreamKey createStreamKey(NetworkParameters params, ECKey owner, int streamId);

    public StreamKey createStreamKey(NetworkParameters params, ECKey owner, byte[] key, int streamId);

    public StreamKey createShareStreamKey(Address owner, ECKey share, byte[] input, int streamId);
}
