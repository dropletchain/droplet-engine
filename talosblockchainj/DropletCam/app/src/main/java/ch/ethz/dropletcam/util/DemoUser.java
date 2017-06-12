package ch.ethz.dropletcam.util;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.Base58;
import org.bitcoinj.core.DumpedPrivateKey;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.params.RegTestParams;
import org.bitcoinj.store.BlockStoreException;

import java.math.BigInteger;
import java.net.UnknownHostException;

import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.KeyManager;
import ch.ethz.blokcaditapi.storage.Util;

/**
 * Created by lukas on 16.05.17.
 * Plaintext keys for demo
 */

public class DemoUser {

    public static final NetworkParameters params = RegTestParams.get();

    private String name;

    private String ownerKey;

    private String shareKey;

    private Address ownerAddrCache = null;
    private Address shareAddrCache = null;

    public DemoUser(String name, String ownerKey, String shareKey) {
        this.name = name;
        this.ownerKey = ownerKey;
        this.shareKey = shareKey;
    }

    public BlockAditStorage createStorage() throws BlockStoreException, UnknownHostException {
        DemoKeyFactory factory = new DemoKeyFactory();
        KeyManager manager = DemoKeyManager.getNew(RegTestParams.get(), factory);
        ECKey owner = Util.wifToKey(ownerKey, true);
        ECKey share = Util.wifToKey(shareKey, true);
        manager.addKey(owner);
        manager.addShareKey(share);
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

    public Address getOwnerAddress() {
        if (ownerAddrCache != null)
            return ownerAddrCache;

        ECKey key;
        String privKey = this.ownerKey;
        if (privKey.length() == 51 || privKey.length() == 52) {
            DumpedPrivateKey dumpedPrivateKey = DumpedPrivateKey.fromBase58(params, privKey);
            key = dumpedPrivateKey.getKey();
        } else {
            BigInteger privKeyNum = Base58.decodeToBigInteger(privKey);
            key = ECKey.fromPrivate(privKeyNum);
        }
        ownerAddrCache = key.toAddress(params);
        return ownerAddrCache;
    }

    public Address getShareAddress() {
        if (shareAddrCache != null)
            return shareAddrCache;

        ECKey key;
        String privKey = this.shareKey;
        if (privKey.length() == 51 || privKey.length() == 52) {
            DumpedPrivateKey dumpedPrivateKey = DumpedPrivateKey.fromBase58(params, privKey);
            key = dumpedPrivateKey.getKey();
        } else {
            BigInteger privKeyNum = Base58.decodeToBigInteger(privKey);
            key = ECKey.fromPrivate(privKeyNum);
        }
        shareAddrCache = key.toAddress(params);
        return shareAddrCache;
    }

    public String toString() {
        return String.format("%s,%s,%s", name, ownerKey, shareKey);
    }

    public static DemoUser fromString(String user) {
        String[] splits = user.split(",");
        return new DemoUser(splits[0], splits[1], splits[2]);
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof DemoUser))
            return false;
        DemoUser user = (DemoUser) o;
        return this.name.equals(user.name);
    }

    @Override
    public int hashCode() {
        return this.name.hashCode();
    }
}
