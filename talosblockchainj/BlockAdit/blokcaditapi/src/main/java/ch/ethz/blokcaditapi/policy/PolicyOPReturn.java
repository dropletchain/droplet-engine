package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Created by lukas on 11.05.17.
 */

public class PolicyOPReturn {

    public static byte DEFAULT_POLICY_TYPE = 1;
    public static int MAX_BITCOIN_BYTES = 80;

    public static String MAGIC_BYTES = "ta";

    public static char CREATE_POLICY = '+';
    public static char GRANT_ACCESS = '>';
    public static char REVOKE_ACCESS = '<';
    public static char CHANGE_INTERVAL = ':';
    public static char INVALIDATE_POLICY = '-';

    public static byte[] createPolicyCMD(int streamId, long timestampStart, long interval, byte[] nonce) {
        int lenData = MAGIC_BYTES.length() + 1  + 1 + 4 + 8 + 8 + nonce.length;
        ByteBuffer data = ByteBuffer.allocate(lenData);
        data.order(ByteOrder.LITTLE_ENDIAN);
        data.put(MAGIC_BYTES.getBytes())
                .put((byte) CREATE_POLICY)
                .put(DEFAULT_POLICY_TYPE)
                .putInt(streamId)
                .putLong(timestampStart)
                .putLong(interval)
                .put(nonce);
        return data.array();
    }

    public static byte[] addShareToPolicyCMD(int streamId, Address[] shares) {
        assert shares.length <= 2;
        int lenData = MAGIC_BYTES.length() + 1 + 4 + 1;
        for (Address share : shares)
            lenData += 1 + share.getHash160().length;
        ByteBuffer data = ByteBuffer.allocate(lenData);
        data.order(ByteOrder.LITTLE_ENDIAN);
        data.put(MAGIC_BYTES.getBytes())
                .put((byte) GRANT_ACCESS)
                .putInt(streamId)
                .put((byte) shares.length);
        for (Address share : shares) {
            byte[] hash = share.getHash160();
            data.put((byte) hash.length).put(hash);
        }
        return data.array();
    }

    public static byte[] removeShareFromPolicyCMD(int streamId, Address[] shares) {
        assert shares.length <= 2;
        int lenData = MAGIC_BYTES.length() + 1 + 4 + 1;
        for (Address share : shares)
            lenData += 1 + share.getHash160().length;
        ByteBuffer data = ByteBuffer.allocate(lenData);
        data.order(ByteOrder.LITTLE_ENDIAN);
        data.put(MAGIC_BYTES.getBytes())
                .put((byte) REVOKE_ACCESS)
                .putInt(streamId)
                .put((byte) shares.length);
        for (Address share : shares) {
            byte[] hash = share.getHash160();
            data.put((byte) hash.length).put(hash);
        }
        return data.array();
    }

    public static byte[] changeIntervalCMD(int streamId, long timestampStart, long interval) {
        int lenData = MAGIC_BYTES.length() + 1 + 4 + 8 + 8;
        ByteBuffer data = ByteBuffer.allocate(lenData);
        data.order(ByteOrder.LITTLE_ENDIAN);
        data.put(MAGIC_BYTES.getBytes())
                .put((byte) CHANGE_INTERVAL)
                .putInt(streamId)
                .putLong(timestampStart)
                .putLong(interval);
        return data.array();
    }

    public static byte[] invalidatePolicyCMD(int streamId) {
        int lenData = MAGIC_BYTES.length() + 1 + 4;
        ByteBuffer data = ByteBuffer.allocate(lenData);
        data.order(ByteOrder.LITTLE_ENDIAN);
        data.put(MAGIC_BYTES.getBytes())
                .put((byte) INVALIDATE_POLICY)
                .putInt(streamId);
        return data.array();
    }

}
