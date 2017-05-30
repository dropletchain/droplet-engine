package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;

/**
 * Created by lukas on 30.05.17.
 * TODO
 */

public class IntervalKeyRegressionKey implements StreamKey {

    private int numKeys;
    private HashFunction leftHashFunc;
    private HashFunction rightHashFunc;

    private byte[] firstHashL;
    private byte[] firstHashR;

    private int streamId;
    private Address owner;
    private ECKey identityKey;

    private int curVersion;


    @Override
    public int getStreamId() {
        return streamId;
    }

    @Override
    public Address getOwnerAddress() {
        return owner;
    }

    @Override
    public Address getSignAddress() {
        return identityKey.toAddress(owner.getParameters());
    }

    @Override
    public ECKey getSignKey() {
        return identityKey;
    }

    @Override
    public int getCurVersion() {
        return 0;
    }

    @Override
    public byte[] getCurSymKey() {
        return new byte[0];
    }

    @Override
    public int updateVersion() {
        return curVersion++;
    }

    @Override
    public byte[] getSymKey(int version) {
        return new byte[0];
    }

    @Override
    public byte[] serialize() {
        return new byte[0];
    }

    @Override
    public int serializeLen() {
        return 0;
    }

    @Override
    public boolean canWrite() {
        return false;
    }
}
