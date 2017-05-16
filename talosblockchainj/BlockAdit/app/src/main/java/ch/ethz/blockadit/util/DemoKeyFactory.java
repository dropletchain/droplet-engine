package ch.ethz.blockadit.util;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;

import ch.ethz.blokcaditapi.policy.StreamKey;
import ch.ethz.blokcaditapi.policy.StreamKeyFactory;

/**
 * Created by lukas on 16.05.17.
 */

public class DemoKeyFactory implements StreamKeyFactory {
    @Override
    public StreamKey createStreamKey(NetworkParameters params, ECKey owner, int streamId) {
        return null;
    }

    @Override
    public StreamKey createStreamKey(NetworkParameters params, ECKey owner, byte[] key, int streamId) {
        return null;
    }

    @Override
    public StreamKey createShareStreamKey(Address owner, ECKey share, byte[] input, int streamId) {
        return null;
    }
}
