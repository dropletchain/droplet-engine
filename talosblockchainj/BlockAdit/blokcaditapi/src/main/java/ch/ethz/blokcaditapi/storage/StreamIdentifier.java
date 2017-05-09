package ch.ethz.blokcaditapi.storage;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * Created by lukas on 09.05.17.
 */

public class StreamIdentifier {

    private String owner;
    private int streamId;
    private byte[] nonce;
    private String txid;

    public StreamIdentifier(String owner, int streamId, byte[] nonce, String txid) {
        this.owner = owner;
        this.streamId = streamId;
        this.nonce = nonce;
        this.txid = txid;
    }

    public String getOwner() {
        return owner;
    }

    public int getStreamId() {
        return streamId;
    }

    public byte[] getNonce() {
        return nonce;
    }

    public String getTxid() {
        return txid;
    }

    public byte[] getTag() {
        return Util.hexStringToByteArray(this.txid);
    }

    public byte[] getKeyForBlockId(int id) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            md.update(this.owner.getBytes());
            md.update(String.valueOf(this.streamId).getBytes());
            md.update(this.nonce);
            md.update(String.valueOf(id).getBytes());
            return md.digest();
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return null;
    }
}
