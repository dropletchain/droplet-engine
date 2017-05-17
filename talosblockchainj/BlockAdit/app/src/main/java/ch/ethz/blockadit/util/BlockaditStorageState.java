package ch.ethz.blockadit.util;

import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Semaphore;

import ch.ethz.blokcaditapi.BlockAditStorage;

/**
 * Created by lukas on 17.05.17.
 */

public class BlockaditStorageState {

    private static Map<String,BlockAditStorage> storages = new HashMap<>();

    private static Semaphore lock = new Semaphore(1);

    public BlockAditStorage getStorageForUser(DemoUser user) throws UnknownHostException, BlockStoreException, InterruptedException {
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
