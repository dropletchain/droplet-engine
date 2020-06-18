//© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

package ch.ethz.dropletcam;

import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Semaphore;

import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.dropletcam.util.DemoUser;


public class BlockaditStorageState {

    private static Map<String, BlockAditStorage> storages = new HashMap<>();

    private static Semaphore lock = new Semaphore(1);

    public static BlockAditStorage getStorageForUser(DemoUser user) throws UnknownHostException, BlockStoreException, InterruptedException {
        lock.acquire();
        try {
            if (storages.containsKey(user.getName()))
                return storages.get(user.getName());
            storages.put(user.getName(), user.createStorage());
            return storages.get(user.getName());
        } finally {
            lock.release();
        }
    }
}
