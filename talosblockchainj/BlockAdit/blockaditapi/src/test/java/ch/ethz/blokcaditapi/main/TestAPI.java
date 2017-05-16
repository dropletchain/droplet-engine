package ch.ethz.blokcaditapi.main;

import org.bitcoinj.core.ECKey;
import org.junit.Test;

import java.util.List;

import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStorageConfig;
import ch.ethz.blokcaditapi.DefaultConfig;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.KeyManager;
import ch.ethz.blokcaditapi.policy.BasicStreamKeyFactory;
import ch.ethz.blokcaditapi.storage.Util;
import ch.ethz.blokcaditapi.storage.chunkentries.DoubleEntry;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;

import static org.junit.Assert.assertEquals;

/**
 * Created by lukas on 16.05.17.
 */

public class TestAPI {

    private static String TEST_KEY = "cQ1HBRRvJ9DaV2UZsEf5w1uLAoXjSVpLYVH5dB5hZUWk5jeJ8KCL";


    @Test
    public void testBasic() throws Exception {
        BlockAditStorageConfig config = DefaultConfig.get();
        KeyManager manager = KeyManager.getNew(config.getNetworkParameters(), new BasicStreamKeyFactory());
        ECKey key = Util.wifToKey(TEST_KEY, true);
        manager.addKey(key);
        BlockAditStorage storage = new BlockAditStorage(manager, config);
        IBlockAditStream stream = storage.createNewStream(775, 0, 10);

    }

    @Test
    public void testBasic2() throws Exception {
        byte[] symKey = new byte[16];

        BlockAditStorageConfig config = DefaultConfig.get();
        KeyManager manager = KeyManager.getNew(config.getNetworkParameters(), new BasicStreamKeyFactory());
        ECKey key = Util.wifToKey(TEST_KEY, true);
        manager.addKey(key);
        BasicStreamKeyFactory factory = new BasicStreamKeyFactory();
        manager.addStreamKey(factory.createStreamKey(config.getNetworkParameters(), key, symKey, 775));
        BlockAditStorage storage = new BlockAditStorage(manager, config);
        IBlockAditStream stream = storage.getStreamForID(key.toAddress(config.getNetworkParameters()), 775);
        assertEquals(stream.getOwner(), key.toAddress(config.getNetworkParameters()));
        //stream.getPolicyManipulator().addShare(Address.fromBase58(config.getNetworkParameters(), "mhJ7QEzyZhPA9D2f9Vaab1saKgBAUMQ9qx"));
        //stream.getPolicyManipulator().addShare(Address.fromBase58(config.getNetworkParameters(), "mtuVSpDMrtZi5GfZgEJbdR5dSD3ULsQ81y"));

        for (int i=0; i<100; i++) {
            stream.appendToStream(new DoubleEntry(i, "temp", i*1.2));
        }
        stream.flushWriteChunk();

        List<Entry> entries = stream.getRange(0, 100);

        assertEquals(entries.size(), 100);
    }

}
