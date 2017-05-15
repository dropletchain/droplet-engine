package ch.ethz.blokcaditapi.storage;

import org.bitcoinj.core.ECKey;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.InvalidKeyException;
import java.util.List;
import java.util.zip.DataFormatException;

import javax.crypto.BadPaddingException;

/**
 * Created by lukas on 08.05.17.
 */
public class CloudChunk {

    public static final int HASH_BYTES = 32;
    public static final int VERSION_BYTES = 4;
    public static final int MAC_BYTES = 16;

    byte[] key;
    int keyVersion;
    byte[] policyTag;
    byte[] encData;
    byte[] gcmTag;
    byte[] signature;

    private CloudChunk() {}

    CloudChunk(byte[] key, int keyVersion, byte[] policyTag, byte[] encData, byte[] gcmTag, byte[] signature) {
        this.key = key;
        this.keyVersion = keyVersion;
        this.policyTag = policyTag;
        this.encData = encData;
        this.gcmTag = gcmTag;
        this.signature = signature;
    }

    CloudChunk(byte[] key, int keyVersion, byte[] policyTag, byte[] encData, byte[] gcmTag, ECKey signKey) throws InvalidKeyException {
        this.key = key;
        this.keyVersion = keyVersion;
        this.policyTag = policyTag;
        this.encData = encData;
        this.gcmTag = gcmTag;
        this.updateSignature(signKey);
    }

    private void addPublicPart(ByteBuffer buffer, boolean withKey) {
        if(withKey)
            buffer.put(this.key);
        buffer.putInt(this.keyVersion);
        buffer.put(this.policyTag);
    }

    private void addDataPart(ByteBuffer buffer) {
        buffer.putInt(this.encData.length);
        buffer.put(this.encData);
        buffer.put(this.gcmTag);
    }

    public void updateSignature(ECKey key) throws InvalidKeyException {
        this.signature = StorageCrypto.signECDSA(key, this.encodeWithoutSignature());
    }

    public ChunkData retriveData(byte[] symKey, boolean useCompression) throws InvalidKeyException {
        byte[] data = null, finalData;
        try {
            data = StorageCrypto.decryptAESGcm(symKey, this.encData, this.encodePublicPart());
        } catch (BadPaddingException e) {
            throw new ChunkExcpetion("Chunk integrity check failed");
        }
        if (useCompression)
            try {
                finalData = StorageCrypto.decompressData(data);
            } catch (DataFormatException e) {
                e.printStackTrace();
                return null;
            }
        else
            finalData = data;
        return ChunkData.decodeFromByteString(finalData);
    }

    public boolean checkSignature(ECKey key) throws InvalidKeyException {
        return StorageCrypto.checkECDSASig(key, this.encodeWithoutSignature(), this.signature);
    }

    public byte[] encodePublicPart() {
        ByteBuffer result = ByteBuffer.allocate(HASH_BYTES * 2 + (Integer.SIZE/8));
        result.order(ByteOrder.LITTLE_ENDIAN);
        addPublicPart(result, true);
        return result.array();
    }

    public byte[] encodeWithoutSignature() {
        ByteBuffer result = ByteBuffer.allocate(HASH_BYTES * 2 + (Integer.SIZE/8) * 2 +
                MAC_BYTES + this.encData.length);
        result.order(ByteOrder.LITTLE_ENDIAN);
        addPublicPart(result, true);
        addDataPart(result);
        return result.array();
    }

    public byte[] encode() {
        ByteBuffer result = ByteBuffer.allocate(HASH_BYTES * 2 + (Integer.SIZE/8) * 2
                + this.encData.length + MAC_BYTES + this.signature.length);
        result.order(ByteOrder.LITTLE_ENDIAN);
        addPublicPart(result, true);
        addDataPart(result);
        result.put(this.signature);
        return result.array();
    }

    public static CloudChunk createCloudChunkFromByteString(byte[] cloudChunk) {
        ByteBuffer cloudChunkBuff = ByteBuffer.wrap(cloudChunk);
        byte[] key = new byte[HASH_BYTES];
        int keyVersion, encLen;
        byte[] policyTag = new byte[HASH_BYTES];
        byte[] macTag = new byte[MAC_BYTES];
        cloudChunkBuff.order(ByteOrder.LITTLE_ENDIAN);

        cloudChunkBuff.get(key);
        keyVersion = cloudChunkBuff.getInt();
        cloudChunkBuff.get(policyTag);
        encLen = cloudChunkBuff.getInt();
        byte[] encData = new byte[encLen];
        cloudChunkBuff.get(encData);
        cloudChunkBuff.get(macTag);
        byte[] signature = new byte[cloudChunkBuff.remaining()];
        cloudChunkBuff.get(signature);
        return new CloudChunk(key, keyVersion, policyTag, encData, macTag, signature);
    }


    public static CloudChunk createCloudChunk(StreamIdentifier ident, int blockId, ECKey key,
                                              int keyVersion, byte[] symKey, ChunkData data, boolean useCompression) throws InvalidKeyException {
        byte[] encodedData = data.encode();
        byte[] dataCompressed;
        if (useCompression)
            dataCompressed = StorageCrypto.compressData(encodedData);
        else
            dataCompressed = encodedData;

        CloudChunk chunk = new CloudChunk();
        chunk.key = ident.getKeyForBlockId(blockId);
        chunk.policyTag = ident.getTag();
        chunk.keyVersion = keyVersion;

        byte[] encData = StorageCrypto.encryptAESGcm(symKey, dataCompressed, chunk.encodePublicPart());
        List<byte[]> splitEncData = StorageCrypto.splitGCMCiphertext(encData);
        chunk.encData = splitEncData.get(0);
        chunk.gcmTag = splitEncData.get(1);
        chunk.updateSignature(key);
        return chunk;
    }
}
