package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Created by lukas on 16.05.17.
 */

public class BasicStreamKey implements StreamKey {

    public static int SYM_KEY_SIZE = 16;

    private Address owner;
    private int streamID;

    private ECKey identityKey;
    private int curKeyVersion = 0;

    private byte[] symKey;

    private BasicStreamKey() {};

    BasicStreamKey(int streamID,Address owner, ECKey identityKey, int curKeyVersion, byte[] symKey) {
        this.owner = owner;
        this.streamID = streamID;
        this.identityKey = identityKey;
        this.curKeyVersion = curKeyVersion;
        this.symKey = symKey;
    }

    BasicStreamKey(int streamID, NetworkParameters params, ECKey identityKey, int curKeyVersion, byte[] symKey) {
        this(streamID, identityKey.toAddress(params), identityKey, curKeyVersion, symKey);
    }

    @Override
    public int getStreamId() {
        return streamID;
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
        return curKeyVersion;
    }

    @Override
    public byte[] getCurSymKey() {
        return symKey;
    }

    @Override
    public int updateVersion() {
        curKeyVersion++;
        return curKeyVersion;
    }

    @Override
    public byte[] getSymKey(int version) {
        return symKey;
    }
    // totLen | streamId | keyVersion | symKey | lenOwner | owner | identKey
    @Override
    public byte[] serialize() {
        int len = serializeLen();
        ByteBuffer buffer = ByteBuffer.allocate(len);
        String owner = this.owner.toString();
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        buffer.putInt(len)
                .putInt(streamID)
                .putInt(curKeyVersion)
                .put(symKey)
                .putInt(owner.length())
                .put(owner.getBytes())
                .put(identityKey.getPrivKeyBytes());
        return buffer.array();
    }

    @Override
    public int serializeLen() {
        return 4 + 4 + 4 + SYM_KEY_SIZE + 4 + owner.toString().length() + identityKey.getPrivKeyBytes().length;
    }

    @Override
    public boolean canWrite() {
        return owner.equals(identityKey.toAddress(owner.getParameters()));
    }

    public StreamKey fromBytes(byte[] key) {
        BasicStreamKey bKey = new BasicStreamKey();
        ByteBuffer buffer = ByteBuffer.wrap(key);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        int lenTot = buffer.getInt();
        bKey.streamID = buffer.getInt();
        bKey.curKeyVersion = buffer.getInt();
        bKey.symKey = new byte[SYM_KEY_SIZE];
        buffer.get(bKey.symKey);

        int lenOwner = buffer.getInt();
        byte[] ownerBytes = new byte[lenOwner];
        buffer.get(ownerBytes);
        String ownerString = new String(ownerBytes);
        bKey.owner = Address.fromBase58(Address.getParametersFromAddress(ownerString), ownerString);

        byte[] priv = new byte[lenTot - 4 + 4 + 4 + SYM_KEY_SIZE - 4 - lenOwner];
        buffer.get(priv);
        bKey.identityKey = ECKey.fromPrivate(priv);
        return bKey;
    }
}
