package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;

import java.security.SecureRandom;

/**
 * Created by lukas on 16.05.17.
 */

public class BasicStreamKeyFactory implements StreamKeyFactory {

    private SecureRandom random = new SecureRandom();

    public BasicStreamKeyFactory() {
    }

    @Override
    public StreamKey createStreamKey(NetworkParameters params, ECKey owner, int streamId) {
        byte[] symKey = new byte[BasicStreamKey.SYM_KEY_SIZE];
        random.nextBytes(symKey);
        return new BasicStreamKey(streamId, params, owner, 0, symKey);
    }

    @Override
    public StreamKey createStreamKey(NetworkParameters params, ECKey owner, byte[] key, int streamId) {
        return new BasicStreamKey(streamId, params, owner, 0, key);
    }

    @Override
    public StreamKey createShareStreamKey(Address owner, ECKey share, byte[] input, int streamId) {
        byte[] symKey = new byte[BasicStreamKey.SYM_KEY_SIZE];
        random.nextBytes(symKey);
        return new BasicStreamKey(streamId, owner, share, 0, symKey);
    }
}
