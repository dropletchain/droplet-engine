package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.Coin;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.core.Transaction;
import org.bitcoinj.store.BlockStoreException;

import java.io.File;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

import ch.ethz.blokcaditapi.policy.Policy;
import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.policy.PolicyManipulationClient;
import ch.ethz.blokcaditapi.policy.PolicyVcApiClient;
import ch.ethz.blokcaditapi.policy.StreamKey;
import ch.ethz.blokcaditapi.storage.BlockAditDHTStorageClient;
import ch.ethz.blokcaditapi.storage.BlockAditStorageAPI;

/**
 * High level API for interacting with the system.
 */
public class BlockAditStorage {
    /**
     * Key Manager for managing the keys.
     */
    private KeyManager keyManager;

    /**
     * Virtualchain interaction client.
     */
    private PolicyVcApiClient policyVcApiClient;

    /**
     * Blockchain interaction client.
     */
    private PolicyManipulationClient policyManipulationClient = null;

    /**
     * The configuration of the system
     */
    private BlockAditStorageConfig config;

    private Random rand = new Random();

    public BlockAditStorage(String password, File keyManagerFile, BlockAditStorageConfig config) throws UnknownHostException, BlockStoreException {
        //TODO
    }

    /**
     * Creates a new storage api.
     * @param keyManager a key manager containing the keys
     * @param config the configurations of the system.
     * @throws UnknownHostException
     * @throws BlockStoreException
     */
    public BlockAditStorage(KeyManager keyManager, BlockAditStorageConfig config) throws UnknownHostException, BlockStoreException {
        this.keyManager = keyManager;
        this.config = config;
        this.policyVcApiClient = new PolicyVcApiClient(config.getVirtualchainAddress(),
                config.getVirtualchainPort(), config.getPolicyCacheTime());
        this.policyManipulationClient = keyManager.createPolicyManipulator(config.getTransactionFee(),
                InetAddress.getByName(config.getBitcoinAddress()));
    }

    private IBlockAditStreamPolicy createStreamPolicy(Address owner, int streamId) throws PolicyClientException {
        return new BlockAditStreamPolicy(policyVcApiClient, policyManipulationClient, owner, streamId);
    }

    private IBlockAditStreamPolicy createStreamPolicy(Address owner, int streamId, Policy local) throws PolicyClientException {
        return new BlockAditStreamPolicy(policyVcApiClient, policyManipulationClient, owner, streamId, local);
    }

    private BlockAditStorageAPI createStorageApi() throws PolicyClientException {
        return new BlockAditDHTStorageClient(config.getStorageApiAddress(), config.getStorageApiPort());
    }

    /**
     * Add a owner identity key to the storage.
     * @param key
     */
    public void addKey(ECKey key) {
        keyManager.addKey(key);
    }

    /**
     * Create a new stream for storing data.
     * @param owner the owner address of the stream.
     * @param id the stream identifier.
     * @param startTime the start time of the stream (unix timestamp)
     * @param interval the chunk interval of the stream (in seconds)
     * @return a temporary stream object (not yet approved, blockchain is slow)
     * @throws InsufficientMoneyException
     * @throws PolicyClientException
     * @throws BlockAditStreamException
     */
    public IBlockAditStream createNewStream(Address owner, int id, long startTime, long interval)
            throws InsufficientMoneyException, PolicyClientException, BlockAditStreamException {
        StreamKey key = keyManager.createNewStreamKey(owner, id);
        Transaction transaction = policyManipulationClient.createPolicy(owner, id, startTime, interval);
        Policy temp = new Policy(owner.toString(), id, "", transaction.getHashAsString(), key.getSignKey().getPublicKeyAsHex());
        temp.addTimeIndex(new Policy.IndexEntry(startTime, interval, ""));
        temp.isTemporary = true;
        return new BlockAditStream(createStorageApi(), key, createStreamPolicy(owner, id, temp));
    }

    /**
     * Returns the main owner address of the storage if exists, else
     * creates a new one.
     * @return address of the owner.
     */
    private Address getOwner() {
        List<Address> owners = keyManager.getOwnerAddresses();
        if (owners.isEmpty())
            return keyManager.generateOwnerKey();
        else
            return owners.get(0);
    }

    private int getRandomStreamId(Address owner) throws PolicyClientException {
        List<Integer> ids = getStreamIdsForAddress(owner);
        int res = rand.nextInt();
        while (ids.contains(res))
            res = rand.nextInt();
        return res;
    }

    /**
     * Create a new stream for storing data.
     * The main owner address is used for the stream.
     * @param id id the stream identifier.
     * @param startTime the start time of the stream (unix timestamp)
     * @param interval a temporary stream object (not yet approved, blockchain is slow)
     * @return  a temporary stream object (not yet approved, blockchain is slow)
     * @throws PolicyClientException
     * @throws InsufficientMoneyException
     * @throws BlockAditStreamException
     */
    public IBlockAditStream createNewStream(int id, long startTime, long interval)
            throws PolicyClientException, InsufficientMoneyException, BlockAditStreamException {
        Address owner = getOwner();
        return createNewStream(owner, id, startTime, interval);
    }

    /**
     * Create a new stream for storing data.
     * A random stream identifier is generated.
     * @param owner the owner address of the stream.
     * @param startTime the start time of the stream (unix timestamp)
     * @param interval the chunk interval of the stream (in seconds)
     * @return  a temporary stream object (not yet approved, blockchain is slow)
     * @throws PolicyClientException
     * @throws InsufficientMoneyException
     * @throws BlockAditStreamException
     */
    public IBlockAditStream createNewStream(Address owner, long startTime, long interval)
            throws PolicyClientException, InsufficientMoneyException, BlockAditStreamException {
        return createNewStream(owner, getRandomStreamId(owner), startTime, interval);
    }

    /**
     * Create a new stream for storing data.
     * The main owner address is used for the stream.
     * A random stream identifier is generated.
     * @param startTime the start time of the stream (unix timestamp)
     * @param interval the chunk interval of the stream (in seconds)
     * @return  a temporary stream object (not yet approved, blockchain is slow)
     * @throws PolicyClientException
     * @throws InsufficientMoneyException
     * @throws BlockAditStreamException
     */
    public IBlockAditStream createNewStream(long startTime, long interval)
            throws PolicyClientException, InsufficientMoneyException, BlockAditStreamException {
        Address owner = getOwner();
        int id = getRandomStreamId(owner);
        return createNewStream(owner, id, startTime, interval);
    }

    /**
     * Returns a list of all owner addresses of this storage.
     * @return a list of owner addresses.
     */
    public List<Address> getOwnerAddresses() {
        return keyManager.getOwnerAddresses();
    }

    /**
     * Given a owner address, returns the associated stream identifiers.
     * @param address the owner address
     * @return a list of stream identifiers.
     * @throws PolicyClientException
     */
    public List<Integer> getStreamIdsForAddress(Address address) throws PolicyClientException {
        return this.policyVcApiClient.getStreamIdsForOwner(address.toString());
    }

    /**
     * Returns all streams owned by this storage.
     * @return a list of stream objects.
     * @throws PolicyClientException
     * @throws BlockAditStreamException
     */
    public List<IBlockAditStream> getStreams() throws PolicyClientException, BlockAditStreamException {
        List<IBlockAditStream> streams = new ArrayList<>();
        for (Address owner : keyManager.getOwnerAddresses()) {
            for (Integer streamId : policyVcApiClient.getStreamIdsForOwner(owner.toString())) {
                streams.add(getStreamForID(owner, streamId));
            }
        }
        return streams;
    }

    /**
     * Fetches the blockchain currency balance of this storage.
     * @return the balance.
     */
    public Coin getBalance() {
        return this.policyManipulationClient.getBalance();
    }

    /**
     * Returns all streams that are shared with this storage (only readable)
     * @return a list of shared streams.
     * @throws PolicyClientException
     * @throws BlockAditStreamException
     */
    public List<IBlockAditStream> getAccessableStreams() throws PolicyClientException, BlockAditStreamException {
        List<IBlockAditStream> streams = new ArrayList<>();
        for (Address owner : keyManager.getShareAddresses()) {
            for (PolicyVcApiClient.AccessableStream temp : policyVcApiClient.getAccessesForAddress(owner.toString())) {
                streams.add(getAccessStreamForID(Address.fromBase58(policyManipulationClient.getNetwrokParameters(),
                        temp.ownerAddress), temp.streamId));
            }
        }
        return streams;
    }

    /**
     * Given a owner address and the corresponding stream identifier, returns the corresponding
     * stream if it exists.
     * @param owner the owner address
     * @param streamId the stream identifier.
     * @return the stream if exists else an exception is thrown.
     * @throws PolicyClientException
     * @throws BlockAditStreamException
     */
    public IBlockAditStream getStreamForID(Address owner, int streamId) throws PolicyClientException,
            BlockAditStreamException {
        StreamKey key = keyManager.getStreamKey(owner, streamId);
        Policy temp = policyVcApiClient.getPolicy(owner.toString(), streamId);
        return new BlockAditStream(createStorageApi(), key, createStreamPolicy(owner, streamId, temp));
    }

    /**
     * Given a owner address and the corresponding stream identifier of a shared stream,
     * returns the corresponding shared stream if it exists.
     * @param owner the owner address
     * @param streamId the stream identifier.
     * @return the stream if exists else an exception is thrown.
     * @throws PolicyClientException
     * @throws BlockAditStreamException
     */
    public IBlockAditStream getAccessStreamForID(Address owner, int streamId) throws PolicyClientException,
            BlockAditStreamException {
        StreamKey key = keyManager.getShareStreamKey(owner, streamId);
        Policy temp = policyVcApiClient.getPolicy(owner.toString(), streamId);
        return new BlockAditStream(createStorageApi(), key, createStreamPolicy(owner, streamId, temp));
    }

    /**
     * Preloads the blockchain state.
     */
    public void preLoadBlockchainState() {
        this.policyManipulationClient.start();
    }
}
