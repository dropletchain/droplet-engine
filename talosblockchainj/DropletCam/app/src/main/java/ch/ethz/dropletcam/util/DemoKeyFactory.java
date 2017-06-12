package ch.ethz.dropletcam.util;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;

import java.nio.ByteBuffer;

import ch.ethz.blokcaditapi.policy.BasicStreamKey;
import ch.ethz.blokcaditapi.policy.StreamKey;
import ch.ethz.blokcaditapi.policy.StreamKeyFactory;

/**
 * Created by lukas on 16.05.17.
 * Demo key's no need to presist keys etc..
 */

public class DemoKeyFactory implements StreamKeyFactory {

    private static final String DEMO_PICTURE_KEY = "aaaaaaaaaaaaaaaa";

    @Override
    public StreamKey createStreamKey(NetworkParameters params, ECKey owner, int streamId) {
        return new BasicStreamKey(streamId, owner.toAddress(params), owner, 0, DEMO_PICTURE_KEY.getBytes());
    }

    @Override
    public StreamKey createStreamKey(NetworkParameters params, ECKey owner, byte[] key, int streamId) {
        return new BasicStreamKey(streamId, owner.toAddress(params), owner, 0, key);
    }

    @Override
    public StreamKey createShareStreamKey(Address owner, ECKey share, byte[] input, int streamId) {
        return new BasicStreamKey(streamId, owner, share, 0, DEMO_PICTURE_KEY.getBytes());
    }
}
