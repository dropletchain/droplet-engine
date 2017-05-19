package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.core.Transaction;

import ch.ethz.blokcaditapi.policy.Policy;
import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.policy.PolicyManipulationClient;
import ch.ethz.blokcaditapi.policy.PolicyVcApiClient;

/**
 * Created by lukas on 12.05.17.
 */
public class BlockAditStreamPolicy implements IBlockAditStreamPolicy {

    private Policy localPolicy;
    private PolicyVcApiClient client;
    private PolicyManipulationClient policyClient;

    private Address owner;
    private int streamId;

    BlockAditStreamPolicy(PolicyVcApiClient client, PolicyManipulationClient policyClient, Address owner, int streamId) throws PolicyClientException {
        this.client = client;
        this.policyClient = policyClient;
        this.owner = owner;
        this.streamId = streamId;
        localPolicy = getActualPolicy();
        if (localPolicy == null) {
            localPolicy = new Policy(owner.toString(), streamId, "", "", "");
        }
    }

    BlockAditStreamPolicy(PolicyVcApiClient client, PolicyManipulationClient policyClient, Address owner, int streamId, Policy localPolicy) throws PolicyClientException {
        this.client = client;
        this.policyClient = policyClient;
        this.owner = owner;
        this.streamId = streamId;
        this.localPolicy = localPolicy;
    }

    @Override
    public Policy getLocalPolicy() {
        return localPolicy;
    }

    @Override
    public Policy getActualPolicy() throws PolicyClientException {
        try {
            return client.getPolicy(owner.toString(), streamId);
        } catch (PolicyClientException e) {
            if (e.getMessage().equals(client.NO_RESULT_FOUND))
                return null;
            else
                throw e;
        }
    }

    @Override
    public Transaction addShare(Address address) throws InsufficientMoneyException, PolicyClientException {
        Transaction trans = policyClient.addShares(owner, streamId, new Address[] {address});
        localPolicy.addShare(new Policy.PolicyShare(address.toString(), trans.getHashAsString()));
        return trans;
    }

    @Override
    public Transaction removeShare(Address address) throws InsufficientMoneyException, PolicyClientException {
        //TODO: add check if remove is valid
        Transaction trans = policyClient.removeShares(owner, streamId, new Address[] {address});
        localPolicy.removeShare(address.toBase58());
        return trans;
    }

    @Override
    public Transaction updateTimes(long start, long interval) throws InsufficientMoneyException, PolicyClientException {
        Transaction trans = policyClient.updateTimeIndex(owner, streamId, start, interval);
        localPolicy.addTimeIndex(new Policy.IndexEntry(start, interval, trans.getHashAsString()));
        return trans;
    }

    @Override
    public Transaction invalidate() throws InsufficientMoneyException, PolicyClientException {
        Transaction trans = policyClient.invalidatePolicy(owner, streamId);
        localPolicy.invalidate();
        return trans;
    }

    @Override
    public boolean checkLocalMatchesActual() throws PolicyClientException {
        if (localPolicy == null)
            return false;
        return localPolicy.equals(this.getActualPolicy());
    }

    @Override
    public NetworkParameters getNeworkParams() {
        return policyClient.getNetwrokParameters();
    }
}
