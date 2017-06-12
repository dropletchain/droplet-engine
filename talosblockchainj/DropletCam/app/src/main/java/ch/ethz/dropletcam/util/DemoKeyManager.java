package ch.ethz.dropletcam.util;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.params.RegTestParams;

import ch.ethz.blokcaditapi.KeyManager;
import ch.ethz.blokcaditapi.policy.PolicyWallet;
import ch.ethz.blokcaditapi.policy.StreamKey;
import ch.ethz.blokcaditapi.policy.StreamKeyFactory;

/**
 * Created by lukas on 19.05.17.
 * ONLY FOR DEMO (HAACK)
 */

public class DemoKeyManager extends KeyManager {

    public static KeyManager getNew(NetworkParameters params, StreamKeyFactory factory) {
        DemoKeyManager manager = new DemoKeyManager();
        manager.wallet = new PolicyWallet(params);
        manager.streamKeyFactory = factory;
        return manager;
    }

    @Override
    public StreamKey getStreamKey(Address owner, int streamId) {
        StreamKey key = super.getStreamKey(owner, streamId);
        if (key == null) {
            ECKey ownerKey = this.wallet.getKeyForAddress(owner);
            key = this.streamKeyFactory.createStreamKey(RegTestParams.get(), ownerKey, streamId);
            this.myStreamKeys.add(key);
        }
        return key;
    }

    @Override
    public StreamKey getShareStreamKey(Address owner, int streamId) {
        StreamKey key = super.getShareStreamKey(owner, streamId);
        if (key == null) {
            ECKey sharekey = this.shareKeys.get(0);
            key = this.streamKeyFactory.createShareStreamKey(owner, sharekey, null, streamId);
            this.shareStreamKeys.add(key);
        }
        return key;
    }
}
