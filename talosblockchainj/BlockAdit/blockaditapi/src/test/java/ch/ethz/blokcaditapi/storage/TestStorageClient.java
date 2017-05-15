package ch.ethz.blokcaditapi.storage;

import org.bitcoinj.core.ECKey;
import org.bitcoinj.params.RegTestParams;
import org.junit.Test;
import org.spongycastle.util.encoders.Base64;

import ch.ethz.blokcaditapi.storage.chunkentries.DoubleEntry;

import static org.junit.Assert.assertArrayEquals;

/**
 * Created by lukas on 15.05.17.
 */

public class TestStorageClient {

    private static String PRIVATE_KEY = "cQ1HBRRvJ9DaV2UZsEf5w1uLAoXjSVpLYVH5dB5hZUWk5jeJ8KCL";
    private static String NONCE = "5GdyXBXN4rLJDhHDr7/0hg==";
    private static int STREAMID = 1;
    private static String TXID = "4ad439ed0fbc7f861e05dd7b7e171192838191418cf7467ee5c0d6290ca178a3";

    @Test
    public void testStore() throws Exception {
        BlockAditDHTStorageClient client = new BlockAditDHTStorageClient("127.0.0.1", 14000);
        ECKey key = Util.wifToKey(PRIVATE_KEY, true);
        byte[] nonce = Base64.decode(NONCE);
        byte[] symKey = new byte[16];

        ChunkData data = new ChunkData();
        for (int i=0; i<1000; i++) {
            data.addEntry(new  DoubleEntry(System.currentTimeMillis(), "a", (double) i));
        }

        StreamIdentifier ident = new StreamIdentifier(key.toAddress(RegTestParams.get()).toString(), STREAMID, nonce, TXID);

        CloudChunk chunk = CloudChunk.createCloudChunk(ident, 0, key, 0, symKey, data, true);


        client.storeChunk(chunk);
        CloudChunk chukAfter = client.getChunk(key, 0, ident);
        assertArrayEquals(chunk.encode(), chukAfter.encode());
    }

}
