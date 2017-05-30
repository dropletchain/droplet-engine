package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.core.Transaction;

import ch.ethz.blokcaditapi.policy.Policy;
import ch.ethz.blokcaditapi.policy.PolicyClientException;

/**
 * Interface for manipulating and accessing polices of a stream.
 */

public interface IBlockAditStreamPolicy {

    /**
     * Returns the local copy of the policy.
     * Note since blockchains are slow, the local policy may differ.
     * @return the local policy.
     */
    public Policy getLocalPolicy();

    /**
     * Fetch the actual policy from the virtualchain.
     * @return
     * @throws PolicyClientException
     */
    public Policy getActualPolicy() throws PolicyClientException;

    /**
     * Adds a share address to this policy, and transmits a add share address
     * transaction to the blockchain.
     * @param address the share address to add
     * @return the transaction object
     * @throws InsufficientMoneyException if not enough money
     * @throws PolicyClientException if a failure occurs in the network client
     */
    public Transaction addShare(Address address) throws InsufficientMoneyException, PolicyClientException;

    /**
     * Remove the given share from the policy and issues the corresponding transaction on
     * the blockchain
     * @param address the share address to remove
     * @return the transaction object
     * @throws InsufficientMoneyException  if not enough money
     * @throws PolicyClientException  if a failure occurs in the network client
     */
    public Transaction removeShare(Address address) throws InsufficientMoneyException, PolicyClientException;

    /**
     * Update the data interval on the policy and and issues the corresponding transaction on
     * the blockchain
     * @param start the starttime  of the new interval (unix timestamp)
     * @param interval the new interval (unix timestamp)
     * @return the transaction object
     * @throws InsufficientMoneyException  if not enough money
     * @throws PolicyClientException  if a failure occurs in the network client
     */
    public Transaction updateTimes(long start, long interval) throws InsufficientMoneyException, PolicyClientException;

    /**
     * Invalidate the policy and issue the invalidate transaction on the blockchain.
     * @return  the transaction object
     * @throws InsufficientMoneyException if not enough money
     * @throws PolicyClientException if a failure occurs in the network client
     */
    public Transaction invalidate() throws InsufficientMoneyException, PolicyClientException;

    /**
     * Checks if the local policy matches the actual policy
     * @return true if yes else false
     * @throws PolicyClientException
     */
    public boolean checkLocalMatchesActual() throws PolicyClientException;

    /**
     * Get the network parameters of the blockahin newwork
     * @return the network parameters.
     */
    public NetworkParameters getNeworkParams();

}
