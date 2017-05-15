package ch.ethz.blokcaditapi.storage;

import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.Sha256Hash;
import org.json.JSONException;
import org.json.JSONObject;
import org.spongycastle.util.encoders.Base64;

import java.nio.ByteBuffer;

/**
 * Created by lukas on 12.05.17.
 */

public class QueryToken {

    public static final String JSON_NONCE = "nonce";
    public static final String JSON_OWNER = "owner";
    public static final String JSON_STREAM_ID = "stream_id";
    public static final String JSON_CHUNK_IDENT = "chunk_key";
    public static final String JSON_SIGNATURE = "signature";
    public static final String JSON_PUB_KEY = "pubkey";

    private String owner;
    private int streamId;
    private byte[] nonce;
    private byte[] chunkKey;

    private byte[] signature;
    private String pubkeyHex;

    private QueryToken() {}

    public static byte[] getBytesSignature(String owner, int streamId, byte[] nonce, byte[] chunkKey) {
        String strStream = String.valueOf(streamId);
        ByteBuffer buff = ByteBuffer.allocate(owner.length() + strStream.length() + nonce.length + chunkKey.length);
        buff.put(owner.getBytes()).put(strStream.getBytes()).put(nonce).put(chunkKey);
        return buff.array();
    }

    private static byte[] signMessage(ECKey key, byte[] data) {
        Sha256Hash hash = Sha256Hash.of(data);
        return key.sign(hash).encodeToDER();
    }

    private static boolean verifyMessage(ECKey key, byte[] data, byte[] signature) {
        Sha256Hash hash = Sha256Hash.of(data);
        return key.verify(hash, ECKey.ECDSASignature.decodeFromDER(signature));
    }

    public static QueryToken createQueryToken(String owner, int streamId, byte[] nonce, byte[] chunkKey, ECKey key) {
        QueryToken token = new QueryToken();
        token.owner = owner;
        token.streamId = streamId;
        token.nonce = nonce;
        token.chunkKey = chunkKey;
        token.signature = signMessage(key, getBytesSignature(owner, streamId, nonce, chunkKey));
        token.pubkeyHex = key.getPublicKeyAsHex();
        return token;
    }

    public static QueryToken fromJson(String jsonToken) throws JSONException {
        QueryToken result = new QueryToken();
        JSONObject obj = new JSONObject(jsonToken);
        result.owner = obj.getString(JSON_OWNER);
        result.streamId = obj.getInt(JSON_STREAM_ID);
        result.nonce = Base64.decode(obj.getString(JSON_NONCE));
        result.chunkKey = Base64.decode(obj.getString(JSON_CHUNK_IDENT));
        result.signature = Base64.decode(obj.getString(JSON_SIGNATURE));
        result.pubkeyHex = obj.getString(JSON_PUB_KEY);
        return result;
    }

    public String toJSON() throws JSONException {
        JSONObject obj = new JSONObject();
        obj.put(JSON_OWNER, owner);
        obj.put(JSON_STREAM_ID, streamId);
        obj.put(JSON_NONCE, Base64.toBase64String(nonce));
        obj.put(JSON_CHUNK_IDENT, Base64.toBase64String(chunkKey));
        obj.put(JSON_PUB_KEY, pubkeyHex);
        obj.put(JSON_SIGNATURE,  Base64.toBase64String(signature));
        return obj.toString();
    }


}
