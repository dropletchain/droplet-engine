package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.ECKey;

/**
 * Created by lukas on 11.05.17.
 */

public interface StreamKey {

    public ECKey getOwnerKey();

    public byte[] getSymKey(int version);

    public byte[] serialize();

    public byte[] serializeLen();

}
