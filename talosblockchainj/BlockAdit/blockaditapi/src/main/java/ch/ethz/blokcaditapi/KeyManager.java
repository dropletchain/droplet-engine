package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.Coin;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.store.BlockStoreException;

import java.io.File;
import java.net.InetAddress;
import java.util.ArrayList;
import java.util.List;

import ch.ethz.blokcaditapi.policy.PolicyManipulationClient;
import ch.ethz.blokcaditapi.policy.PolicyWallet;
import ch.ethz.blokcaditapi.policy.StreamKey;
import ch.ethz.blokcaditapi.policy.StreamKeyFactory;

/**
 * Created by lukas on 11.05.17.
 */

public class KeyManager {

    private List<StreamKey> myStreamKeys = new ArrayList<>();
    private List<StreamKey> shareStreamKeys = new ArrayList<>();
    private List<ECKey> shareKeys = new ArrayList<>();
    private PolicyWallet wallet;
    private StreamKeyFactory streamKeyFactory;

    private KeyManager() {}

    public static KeyManager fromFile(String password, File file) {
        return null;
    }

    public static KeyManager getNew(NetworkParameters params, StreamKeyFactory factory) {
        KeyManager manager = new KeyManager();
        manager.wallet = new PolicyWallet(params);
        manager.streamKeyFactory = factory;
        return manager;
    }

    public PolicyManipulationClient createPolicyManipulator(Coin fee, InetAddress address) throws BlockStoreException {
        return new PolicyManipulationClient(this.wallet, fee, address);
    }

    public void presistToFile(String password, File fileToPresist) {

    }

    public void addKey(ECKey key) {
        wallet.importKey(key);
    }

    public void addShareKey(ECKey key) {
        shareKeys.add(key);
    }

    public Address generateOwnerKey() {
        return wallet.getAddressForKey(wallet.createNewPolicyKey());
    }

    public Address generateShareKey() {
        ECKey key = new ECKey();
        shareKeys.add(key);
        return wallet.getAddressForKey(key);
    }

    public List<Address> getOwnerAddresses() {
        return this.wallet.getOwnerAddresses();
    }

    public List<Address> getShareAddresses() {
        List<Address> addresses = new ArrayList<>();
        for(ECKey key: shareKeys) {
            addresses.add(wallet.getAddressForKey(key));
        }
        return addresses;
    }

    public StreamKey createNewStreamKey(Address owner) throws BlockAditStreamException {
        ECKey ownerKey = this.wallet.getKeyForAddress(owner);
        if (ownerKey == null)
            throw new BlockAditStreamException("No key for address");
        StreamKey key = this.streamKeyFactory.createStreamKey(ownerKey);
        myStreamKeys.add(key);
        return key;
    }

    private ECKey getKeyForShareAddress(Address shareAddress) {
        for (ECKey key : shareKeys) {
            Address temp = this.wallet.getAddressForKey(key);
            if(temp.equals(shareAddress))
                return key;
        }
        return null;
    }

    public StreamKey createNewStreamKey() {
        ECKey owner = this.wallet.createNewPolicyKey();
        StreamKey key = this.streamKeyFactory.createStreamKey(owner);
        myStreamKeys.add(key);
        return key;
    }

    public StreamKey createNewShareStreamKey(Address shareAddress, byte[] keyData) throws BlockAditStreamException {
        ECKey shareKey = getKeyForShareAddress(shareAddress);
        if (shareKey == null)
            throw new BlockAditStreamException("No key for share address");
        StreamKey key = this.streamKeyFactory.createShareStreamKey(shareKey, keyData);
        shareStreamKeys.add(key);
        return key;
    }

    public StreamKey getStreamKey(Address owner, int streamId) {
        for (StreamKey key : myStreamKeys)
            if (key.getSignAddress().equals(owner) && key.getStreamId()==streamId)
                return key;
        return null;
    }

    public StreamKey getShareStreamKey(Address owner, int streamId) {
        for (StreamKey key : shareStreamKeys)
            if (key.getSignAddress().equals(owner) && key.getStreamId()==streamId)
                return key;
        return null;
    }

}
