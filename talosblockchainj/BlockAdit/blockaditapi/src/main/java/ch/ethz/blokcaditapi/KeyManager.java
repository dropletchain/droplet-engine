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
 * Implements a basic KeyManager,
 * Note: keys are stored in memory not save.
 */

public class KeyManager {

    /**
     * The keys that the user owns of it's own data
     */
    protected List<StreamKey> myStreamKeys = new ArrayList<>();

    /**
     * The keys that the user possesses of other user's data.
     */
    protected List<StreamKey> shareStreamKeys = new ArrayList<>();

    /**
     * The sign keys for sharing
     */
    protected List<ECKey> shareKeys = new ArrayList<>();

    /**
     * A bitcoin wallet for manipulating policies in the Blockchain
     * Contains the owner identity keys.
     */
    protected PolicyWallet wallet;

    /**
     * A factory for creating new stream Keys
     */
    protected StreamKeyFactory streamKeyFactory;

    protected KeyManager() {
    }

    /**
     * TODO
     * @param password
     * @param file
     * @return
     */
    public static KeyManager fromFile(String password, File file) {
        return null;
    }


    /**
     * Creates a new KeyManager
     * @param params the network parameters of the Blockchain (Bitcoin)
     * @param factory a factory for creating stream keys.
     * @return a new KeyManager
     */
    public static KeyManager getNew(NetworkParameters params, StreamKeyFactory factory) {
        KeyManager manager = new KeyManager();
        manager.wallet = new PolicyWallet(params);
        manager.streamKeyFactory = factory;
        return manager;
    }

    /**
     * Creates a Policy manipulation client, for manipulating the Policies in the blockchain.
     * @param fee the fee to pay per OP_RETURN transcation
     * @param address the owner address of the polcies, which sould be manipulated.
     * @return a new Policy client
     * @throws BlockStoreException
     */
    public PolicyManipulationClient createPolicyManipulator(Coin fee, InetAddress address) throws BlockStoreException {
        return new PolicyManipulationClient(this.wallet, fee, address);
    }

    /**
     * TODO
     * @param password
     * @param fileToPresist
     */
    public void presistToFile(String password, File fileToPresist) {

    }

    /**
     * Add a new owner identity key to this key manager.
     * @param key an owner identity key
     */
    public void addKey(ECKey key) {
        wallet.importKey(key);
    }

    /**
     * Add a Stream Key to this Key Manager.
     * @param key a Stream Key.
     */
    public void addStreamKey(StreamKey key) {
        myStreamKeys.add(key);
    }

    /**
     * Add a shared Stream Key to this Key Manager
     * @param key a stream key from a other user to access it's data.
     */
    public void addShareKey(StreamKey key) {
        shareStreamKeys.add(key);
    }

    /**
     * Add a share identity Key to this Key Manager, which is used for identifying this
     * user in a other policy.
     * @param key
     */
    public void addShareKey(ECKey key) {
        shareKeys.add(key);
    }

    /**
     * Genertes and adds a new owner key to this Key Manager.
     * @return the address of the given user.
     */
    public Address generateOwnerKey() {
        return wallet.getAddressForKey(wallet.createNewPolicyKey());
    }

    /**
     * Generates and adds a new share identity key to this Key Manager.
     * @return the address of the new share identity.
     */
    public Address generateShareKey() {
        ECKey key = new ECKey();
        shareKeys.add(key);
        return wallet.getAddressForKey(key);
    }

    /**
     * Get all owner addresses in this Key Manager.
     * @return a list of owner addresses.
     */
    public List<Address> getOwnerAddresses() {
        return this.wallet.getOwnerAddresses();
    }

    public List<Address> getShareAddresses() {
        List<Address> addresses = new ArrayList<>();
        for (ECKey key : shareKeys) {
            addresses.add(wallet.getAddressForKey(key));
        }
        return addresses;
    }

    /**
     * Given a share identity address, returns the corresponding share identity key.
     * @param shareAddress the share identitity address.
     * @return the corresponding identitiy key
     */
    private ECKey getKeyForShareAddress(Address shareAddress) {
        for (ECKey key : shareKeys) {
            Address temp = this.wallet.getAddressForKey(key);
            if (temp.equals(shareAddress))
                return key;
        }
        return null;
    }

    /**
     * Generates and add a new stream key to this Key Manager.
     * @param owner the owner address the key belongs to.
     * @param streamId the stream identifier of the stream the key belongs to.
     * @return the generated stream key.
     * @throws BlockAditStreamException
     */
    public StreamKey createNewStreamKey(Address owner, int streamId) throws BlockAditStreamException {
        ECKey ownerKey = this.wallet.getKeyForAddress(owner);
        if (ownerKey == null)
            throw new BlockAditStreamException("No key for address");
        StreamKey key = this.streamKeyFactory.createStreamKey(wallet.getNetworkParameters(), ownerKey, streamId);
        myStreamKeys.add(key);
        return key;
    }

    /**
     * Generates and adds a new share stream key.
     * @param owner the owner of the shared stream.
     * @param streamid the stream identitfier of the shared stream
     * @param shareAddress the share address of this user
     * @param keyData the received key data from the the shared stream
     * @return a new share stream key
     * @throws BlockAditStreamException
     */
    public StreamKey createNewShareStreamKey(Address owner, int streamid, Address shareAddress, byte[] keyData) throws BlockAditStreamException {
        ECKey shareKey = getKeyForShareAddress(shareAddress);
        if (shareKey == null)
            throw new BlockAditStreamException("No key for share address");
        StreamKey key = this.streamKeyFactory.createShareStreamKey(owner, shareKey, keyData, streamid);
        shareStreamKeys.add(key);
        return key;
    }

    /**
     * Given a owner address and the stream identifier, returns the corresponding
     * stream key if it exists else null.
     * @param owner the owner address
     * @param streamId the stream identifier
     * @return stream key if it exists else null
     */
    public StreamKey getStreamKey(Address owner, int streamId) {
        for (StreamKey key : myStreamKeys)
            if (key.getOwnerAddress().equals(owner) && key.getStreamId() == streamId)
                return key;
        return null;
    }

    /**
     * Given a share address and the stream identifier, returns the corresponding
     * shared stream key.
     * @param owner the share address
     * @param streamId the stream identifier
     * @return share stream key if it exists else null
     */
    public StreamKey getShareStreamKey(Address owner, int streamId) {
        for (StreamKey key : shareStreamKeys)
            if (key.getOwnerAddress().equals(owner) && key.getStreamId() == streamId)
                return key;
        return null;
    }

}
