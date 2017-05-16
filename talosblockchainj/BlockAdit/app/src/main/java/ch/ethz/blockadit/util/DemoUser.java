package ch.ethz.blockadit.util;

import org.bitcoinj.params.RegTestParams;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;

import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.KeyManager;
import ch.ethz.blokcaditapi.policy.BasicStreamKeyFactory;
import ch.ethz.blokcaditapi.storage.Util;

/**
 * Created by lukas on 16.05.17.
 */

public class DemoUser {

    private String name;

    private String ownerKey;

    private String shareKey;

    public DemoUser(String name, String ownerKey, String shareKey) {
        this.name = name;
        this.ownerKey = ownerKey;
        this.shareKey = shareKey;
    }

    public BlockAditStorage createStorage() throws BlockStoreException, UnknownHostException {
        KeyManager manager = KeyManager.getNew(RegTestParams.get(), new BasicStreamKeyFactory());
        manager.addKey(Util.wifToKey(ownerKey, true));
        manager.addShareKey(Util.wifToKey(shareKey, true));
        return new BlockAditStorage(manager, new DemoBlockAditConfig());
    }

    public String getName() {
        return name;
    }

    public String getOwnerKey() {
        return ownerKey;
    }

    public String getShareKey() {
        return shareKey;
    }
}
