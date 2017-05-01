package ch.lubu;

import kademlia.node.KademliaId;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * Created by lukas on 24.02.17.
 */
public class ChunkKey {

    private String userid;

    private String streamid;

    private long timestamp;

    public ChunkKey(String userid, String streamid, long timestamp) {
        this.userid = userid;
        this.streamid = streamid;
        this.timestamp = timestamp;
    }

    private byte[] getSha1(byte[] values) {
        MessageDigest md = null;
        try {
            md = MessageDigest.getInstance("SHA-1");
        }
        catch(NoSuchAlgorithmException e) {
            e.printStackTrace();
            return null;
        }
        return md.digest(values);
    }

    public KademliaId getKademliaKey() {
        String key = userid + streamid + String.valueOf(timestamp);
        return new KademliaId(getSha1(key.getBytes()));
    }

    public String getUserid() {
        return userid;
    }

    public String getStreamid() {
        return streamid;
    }

    public long getTimestamp() {
        return timestamp;
    }
}
