package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.core.Transaction;

import ch.ethz.blokcaditapi.policy.Policy;
import ch.ethz.blokcaditapi.policy.PolicyClientException;

/**
 * Created by lukas on 12.05.17.
 */

public interface IBlockAditStreamPolicy {

    public Policy getLocalPolicy();

    public Policy getActualPolicy() throws PolicyClientException;

    public Transaction addShare(Address address) throws InsufficientMoneyException, PolicyClientException;

    public Transaction removeShare(Address address) throws InsufficientMoneyException, PolicyClientException;

    public Transaction updateTimes(long start, long interval) throws InsufficientMoneyException, PolicyClientException;

    public Transaction invalidate() throws InsufficientMoneyException, PolicyClientException;

    public boolean checkLocalMatchesActual() throws PolicyClientException;

    public NetworkParameters getNeworkParams();

}
