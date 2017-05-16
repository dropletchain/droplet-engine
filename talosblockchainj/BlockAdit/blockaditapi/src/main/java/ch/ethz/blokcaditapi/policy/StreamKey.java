package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;

/**
 * Created by lukas on 11.05.17.
 */

public interface StreamKey {

    public int getStreamId();

    public Address getOwnerAddress();

    public Address getSignAddress();

    public ECKey getSignKey();

    public int getCurVersion();

    public byte[] getCurSymKey();

    public int updateVersion();

    public byte[] getSymKey(int version);

    public byte[] serialize();

    public int serializeLen();

    public boolean canWrite();
}
