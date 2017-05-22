package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.BlockChain;
import org.bitcoinj.core.Coin;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.core.PeerGroup;
import org.bitcoinj.core.Transaction;
import org.bitcoinj.store.BlockStoreException;
import org.bitcoinj.store.MemoryBlockStore;
import org.bitcoinj.wallet.Wallet;

import java.net.InetAddress;
import java.security.SecureRandom;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Created by lukas on 09.05.17.
 */
public class PolicyManipulationClient {

    private PolicyWallet wallet;
    private BlockChain chain;
    private PeerGroup peerGroup = null;
    private SecureRandom rand = new SecureRandom();
    private Coin fee;

    private InetAddress address;

    private static int TIMEOUT = 10;

    private boolean running = false;

    private Lock lock = new ReentrantLock();

    public PolicyManipulationClient(PolicyWallet wallet,  Coin fee, InetAddress address) throws BlockStoreException {
        MemoryBlockStore store = new MemoryBlockStore(wallet.getNetworkParameters());
        this.chain = new BlockChain(wallet.getNetworkParameters(), wallet, store);
        this.wallet = wallet;
        this.fee = fee;
        this.address = address;
    }

    public Coin getBalance() {
        return wallet.getBalance();
    }

    public void start() {
        this.peerGroup = new PeerGroup(wallet.getNetworkParameters(), this.chain);
        this.peerGroup.addAddress(this.address);
        this.peerGroup.startAsync();
        running = true;
        this.peerGroup.downloadBlockChain();
    }

    public void terminate() {
        this.peerGroup.stopAsync();
        running = false;
    }

    private void checkRunning() {
        if (!running)
            this.start();
    }

    private Transaction sendCommand(byte[] cmd, Address owner)
            throws InsufficientMoneyException, PolicyClientException {
        Wallet.SendResult result = wallet.sendOPReturnTransaction(owner, this.peerGroup, cmd, this.fee);
        try {
            return result.broadcastComplete.get(TIMEOUT, TimeUnit.SECONDS);
        } catch (InterruptedException | ExecutionException e) {
            throw new PolicyClientException(e.getCause());
        } catch (TimeoutException e) {
            throw new PolicyClientException("Broadcast failed");
        }
    }

    public Transaction createPolicy(Address owner, int streamId, long timestampStart, long interval)
            throws InsufficientMoneyException, PolicyClientException {
        this.checkRunning();
        byte[] nonce = new byte[16];
        this.rand.nextBytes(nonce);
        byte[] cmd = PolicyOPReturn.createPolicyCMD(streamId, timestampStart, interval, nonce);
        return sendCommand(cmd, owner);
    }

    public Transaction addShares(Address owner, int streamId, Address[] shares)
            throws InsufficientMoneyException, PolicyClientException {
        this.checkRunning();
        byte[] cmd = PolicyOPReturn.addShareToPolicyCMD(streamId, shares);
        return sendCommand(cmd, owner);
    }

    public Transaction removeShares(Address owner, int streamId, Address[] shares)
            throws InsufficientMoneyException, PolicyClientException {
        this.checkRunning();
        byte[] cmd = PolicyOPReturn.removeShareFromPolicyCMD(streamId, shares);
        return sendCommand(cmd, owner);
    }

    public Transaction updateTimeIndex(Address owner, int streamId, long timestampStart, long interval)
            throws InsufficientMoneyException, PolicyClientException {
        this.checkRunning();
        byte[] cmd = PolicyOPReturn.changeIntervalCMD(streamId, timestampStart, interval);
        return sendCommand(cmd, owner);
    }

    public Transaction invalidatePolicy(Address owner, int streamId)
            throws InsufficientMoneyException, PolicyClientException {
        this.checkRunning();
        byte[] cmd = PolicyOPReturn.invalidatePolicyCMD(streamId);
        return sendCommand(cmd, owner);
    }

    public NetworkParameters getNetwrokParameters() {
        return wallet.getNetworkParameters();
    }
}
