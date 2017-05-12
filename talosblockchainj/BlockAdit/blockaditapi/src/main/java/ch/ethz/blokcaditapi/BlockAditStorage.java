package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.ECKey;

import java.io.File;
import java.util.List;
import java.util.Random;

import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.policy.PolicyManipulationClient;
import ch.ethz.blokcaditapi.policy.PolicyVcApiClient;

/**
 * Created by lukas on 12.05.17.
 */

public class BlockAditStorage {

    private KeyManager keyManager;
    private PolicyVcApiClient policyVcApiClient;
    private PolicyManipulationClient policyManipulationClient = null;

    private BlockAditStorageConfig config;

    public BlockAditStorage(String password, File keyManagerFile, BlockAditStorageConfig config) {
        this.keyManager = KeyManager.fromFile(password, keyManagerFile);

    }

    private IBlockAditStreamPolicy createStreampolicy(Address owner, int streamId) throws PolicyClientException {
        return new BlockAditStreamPolicy(policyVcApiClient, policyManipulationClient, owner, streamId);
    }

    public void addKey(ECKey key) {
        keyManager.addKey(key);
    }

    public IBlockAditStream createNewStream(Address owner, int id) {
        return null;
    }

    public IBlockAditStream createNewStream(int id) {
        return null;
    }

    public IBlockAditStream createNewStream(Address owner) {
        Random rand = new Random();
        List<Integer> ids = getStreamIdsForAddress(owner);
        int res = rand.nextInt();
        while (ids.contains(res))
            res = rand.nextInt();
        return createNewStream(owner, res);
    }

    public IBlockAditStream createNewStream() {
        return null;
    }

    public List<Address> getOwnerAddresses() {
        return keyManager.getOwnerAddresses();
    }

    public List<Integer> getStreamIdsForAddress(Address address) {
        return null;
    }

    public List<IBlockAditStream> getStreams() {
        return null;
    }

    public IBlockAditStream getStreamForID(Address owner, int streamId) {
        return null;
    }
}
