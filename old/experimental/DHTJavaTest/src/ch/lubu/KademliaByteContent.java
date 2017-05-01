package ch.lubu;

import kademlia.dht.KadContent;
import kademlia.node.KademliaId;

import java.nio.ByteBuffer;
import java.util.Base64;

/**
 * Created by lukas on 24.02.17.
 */
public class KademliaByteContent implements KadContent {

    private KademliaId key;
    private String owner;
    private byte[] data;

    private long created;
    private long updated;

    private KademliaByteContent() {
    }

    public KademliaByteContent(KademliaId key, String owner, byte[] data, long created, long updated) {
        this.key = key;
        this.owner = owner;
        this.data = data;
        this.created = created;
        this.updated = updated;
    }

    public KademliaByteContent(KademliaId key, String owner, byte[] data) {
        this.key = key;
        this.owner = owner;
        this.data = data;
        this.created = this.updated = System.currentTimeMillis() / 1000L;;
    }

    public static KademliaByteContent createFromBytes(byte[] content) {
        KademliaByteContent con = new KademliaByteContent();
        return (KademliaByteContent) con.fromSerializedForm(content);
    }

    @Override
    public KademliaId getKey() {
        return key;
    }

    @Override
    public String getType() {
        return KademliaByteContent.class.getName();
    }

    @Override
    public long getCreatedTimestamp() {
        return created;
    }

    @Override
    public long getLastUpdatedTimestamp() {
        return updated;
    }

    @Override
    public String getOwnerId() {
        return owner;
    }

    public byte[] getData() {
        return data.clone();
    }

    @Override
    public byte[] toSerializedForm() {
        ByteBuffer buff = ByteBuffer.allocate(20 + 4 + owner.getBytes().length + 4 + data.length + 16);
        buff.put(key.getBytes());
        buff.putInt(owner.getBytes().length);
        buff.put(owner.getBytes());
        buff.putInt(data.length);
        buff.put(data);
        buff.putLong(created);
        buff.putLong(updated);
        return Base64.getEncoder().encode(buff.array());
    }

    @Override
    public KadContent fromSerializedForm(byte[] bytes) {
        ByteBuffer buff = ByteBuffer.wrap(Base64.getDecoder().decode(bytes));
        byte[] keyBytes = new byte[KademliaId.ID_LENGTH/8];
        buff.get(keyBytes);
        int ownerLen = buff.getInt();
        byte[] ownerbytes = new byte[ownerLen];
        buff.get(ownerbytes);
        int dataLen = buff.getInt();
        byte[] data = new byte[dataLen];
        buff.get(data);
        long created = buff.getLong();
        long updated = buff.getLong();
        return new KademliaByteContent(new KademliaId(keyBytes), new String(ownerbytes), data, created, updated);
    }
}
