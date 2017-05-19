package ch.ethz.blokcaditapi;

import android.content.Context;
import android.support.test.InstrumentationRegistry;
import android.support.test.runner.AndroidJUnit4;

import org.bitcoinj.core.ECKey;
import org.junit.Test;
import org.junit.runner.RunWith;

import ch.ethz.blokcaditapi.policy.BasicStreamKeyFactory;
import ch.ethz.blokcaditapi.storage.Util;

import static org.junit.Assert.assertEquals;

/**
 * Instrumentation test, which will execute on an Android device.
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */
@RunWith(AndroidJUnit4.class)
public class ExampleInstrumentedTest {
    @Test
    public void useAppContext() throws Exception {
        // Context of the app under test.
        Context appContext = InstrumentationRegistry.getTargetContext();

        assertEquals("ch.ethz.blokcaditapi.test", appContext.getPackageName());
    }

    private static String TEST_KEY = "cQ1HBRRvJ9DaV2UZsEf5w1uLAoXjSVpLYVH5dB5hZUWk5jeJ8KCL";


    @Test
    public void testBasic() throws Exception {
        BlockAditStorageConfig config = DefaultConfig.get();
        KeyManager manager = KeyManager.getNew(config.getNetworkParameters(), new BasicStreamKeyFactory());
        ECKey key = Util.wifToKey(TEST_KEY, true);
        manager.addKey(key);
        BlockAditStorage storage = new BlockAditStorage(manager, config);
        IBlockAditStream stream = storage.createNewStream(776, 0, 10);

    }
}
