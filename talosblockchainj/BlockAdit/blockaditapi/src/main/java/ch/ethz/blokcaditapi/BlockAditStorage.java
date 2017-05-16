package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;
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
 * Created by lukas on 12.05.17.
 */

public class BlockAditStorage {

    private KeyManager keyManager;
    private PolicyVcApiClient policyVcApiClient;
    private PolicyManipulationClient policyManipulationClient = null;

    private BlockAditStorageConfig config;

    private  Random rand = new Random();

    public BlockAditStorage(String password, File keyManagerFile, BlockAditStorageConfig config) throws UnknownHostException, BlockStoreException {
        //TODO
    }

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

    public void addKey(ECKey key) {
        keyManager.addKey(key);
    }

    public IBlockAditStream createNewStream(Address owner, int id, long startTime, long interval)
            throws InsufficientMoneyException, PolicyClientException, BlockAditStreamException {
        StreamKey key = keyManager.createNewStreamKey(owner, id);
        Transaction transaction = policyManipulationClient.createPolicy(owner, id, startTime, interval);
        Policy temp = new Policy(owner.toString(), id, "", transaction.getHashAsString(), key.getSignKey().getPublicKeyAsHex());
        return new BlockAditStream(createStorageApi(), key, createStreamPolicy(owner, id, temp));
    }

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

    public IBlockAditStream createNewStream(int id, long startTime, long interval)
            throws PolicyClientException, InsufficientMoneyException, BlockAditStreamException {
        Address owner =  getOwner();
        return createNewStream(owner, id, startTime, interval);
    }

    public IBlockAditStream createNewStream(Address owner, long startTime, long interval)
            throws PolicyClientException, InsufficientMoneyException, BlockAditStreamException {
        return createNewStream(owner, getRandomStreamId(owner), startTime, interval);
    }

    public IBlockAditStream createNewStream(long startTime, long interval)
            throws PolicyClientException, InsufficientMoneyException, BlockAditStreamException {
        Address owner = getOwner();
        int id = getRandomStreamId(owner);
        return createNewStream(owner, id, startTime, interval);
    }

    public List<Address> getOwnerAddresses() {
        return keyManager.getOwnerAddresses();
    }

    public List<Integer> getStreamIdsForAddress(Address address) throws PolicyClientException {
        return this.policyVcApiClient.getStreamIdsForOwner(address.toString());
    }

    public List<IBlockAditStream> getStreams() throws PolicyClientException, BlockAditStreamException {
        List<IBlockAditStream> streams = new ArrayList<>();
        for (Address owner : keyManager.getOwnerAddresses()) {
            for (Integer streamId : policyVcApiClient.getStreamIdsForOwner(owner.toString())) {
                streams.add(getStreamForID(owner, streamId));
            }
        }
        return streams;
    }

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

    public IBlockAditStream getStreamForID(Address owner, int streamId) throws PolicyClientException,
            BlockAditStreamException {
        StreamKey key = keyManager.getStreamKey(owner, streamId);
        Policy temp = policyVcApiClient.getPolicy(owner.toString(), streamId);
        return new BlockAditStream(createStorageApi(), key, createStreamPolicy(owner, streamId, temp));
    }

    public IBlockAditStream getAccessStreamForID(Address owner, int streamId) throws PolicyClientException,
            BlockAditStreamException {
        StreamKey key = keyManager.getShareStreamKey(owner, streamId);
        Policy temp = policyVcApiClient.getPolicy(owner.toString(), streamId);
        return new BlockAditStream(createStorageApi(), key, createStreamPolicy(owner, streamId, temp));
    }
}
