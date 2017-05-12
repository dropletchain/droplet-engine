package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;

/**
 * Created by lukas on 11.05.17.
 */

public interface StreamKey {

    public int getStreamId();

    public Address getSignAddress();

    public ECKey getSignKey();

    public byte[] getSymKey(int version);

    public byte[] serialize();

    public byte[] serializeLen();

    public boolean canWrite();
}
