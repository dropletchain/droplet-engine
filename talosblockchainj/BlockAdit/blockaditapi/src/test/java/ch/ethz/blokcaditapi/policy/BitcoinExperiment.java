package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.Base58;
import org.bitcoinj.core.BlockChain;
import org.bitcoinj.core.Coin;
import org.bitcoinj.core.DumpedPrivateKey;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.PeerAddress;
import org.bitcoinj.core.PeerGroup;
import org.bitcoinj.core.Transaction;
import org.bitcoinj.params.RegTestParams;
import org.bitcoinj.store.MemoryBlockStore;
import org.bitcoinj.wallet.Wallet;
import org.junit.Test;

import java.math.BigInteger;
import java.net.InetAddress;
import java.util.ArrayList;

/**
 * Created by lukas on 11.05.17.
 */

public class BitcoinExperiment {

    @Test
    public void runExperimentSend() throws Exception {
        String privKey = "cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1";
        String toAddr = "mknD6xvdogYEHffyG1WSzkQ7FdbSu43Gs6";
        RegTestParams params = RegTestParams.get();

        ECKey key;
        if (privKey.length() == 51 || privKey.length() == 52) {
            DumpedPrivateKey dumpedPrivateKey = DumpedPrivateKey.fromBase58(params, privKey);
            key = dumpedPrivateKey.getKey();
        } else {
            BigInteger privKeyNum= Base58.decodeToBigInteger(privKey);
            key = ECKey.fromPrivate(privKeyNum);
        }
        System.out.println("Address from private key is: " + key.toAddress(params).toString());
        // And the address ...
        Address destination = Address.fromBase58(params, toAddr);
        ArrayList<ECKey> keys = new ArrayList<>();
        keys.add(key);
        // Import the private key to a fresh wallet.

        Wallet wallet = Wallet.fromKeys(params, keys);
        System.out.println(wallet.getIssuedReceiveAddresses());
        System.out.println(wallet.currentChangeAddress().toString());


        // Find the transactions that involve those coins.
        final MemoryBlockStore blockStore = new MemoryBlockStore(params);
        BlockChain chain = new BlockChain(params, wallet, blockStore);


        final PeerGroup peerGroup = new PeerGroup(params, chain);
        peerGroup.addAddress(new PeerAddress(params, InetAddress.getByName("127.0.0.1")));
        peerGroup.addAddress(new PeerAddress(params, InetAddress.getByName("46.101.113.112")));
        peerGroup.startAsync();
        peerGroup.downloadBlockChain();


        // And take them!
        System.out.println("CurrBalance " + wallet.getBalance().toFriendlyString());
        System.out.format("Num Peers: %d\n", peerGroup.numConnectedPeers());

        Wallet.SendResult result = wallet.sendCoins(peerGroup, destination, Coin.COIN);
        // Wait a few seconds to let the packets flush out to the network (ugly).

        System.out.println("Claiming " + wallet.getBalance().toFriendlyString());

        System.out.println(result.tx.getHashAsString());
        Transaction trans = result.broadcastComplete.get();
        System.out.println(trans.getHashAsString());
        peerGroup.stopAsync();
    }

    @Test
    public void runExperimentOPReturn() throws Exception {
        String privKey = "cQ1HBRRvJ9DaV2UZsEf5w1uLAoXjSVpLYVH5dB5hZUWk5jeJ8KCL";
        String owner = "mgpg7bC41zb13PEdmmbgHhZNaKzX8nfRr2";
        RegTestParams params = RegTestParams.get();

        ECKey key;
        if (privKey.length() == 51 || privKey.length() == 52) {
            DumpedPrivateKey dumpedPrivateKey = DumpedPrivateKey.fromBase58(params, privKey);
            key = dumpedPrivateKey.getKey();
        } else {
            BigInteger privKeyNum= Base58.decodeToBigInteger(privKey);
            key = ECKey.fromPrivate(privKeyNum);
        }
        System.out.println("Address from private key is: " + key.toAddress(params).toString());
        // And the address ...
        Address destination = Address.fromBase58(params, owner);
        ArrayList<ECKey> keys = new ArrayList<>();
        keys.add(key);
        // Import the private key to a fresh wallet.

        PolicyWallet wallet = new PolicyWallet(params);
        wallet.importKey(key);



        // Find the transactions that involve those coins.
        final MemoryBlockStore blockStore = new MemoryBlockStore(params);
        BlockChain chain = new BlockChain(params, wallet, blockStore);


        final PeerGroup peerGroup = new PeerGroup(params, chain);
        peerGroup.addAddress(new PeerAddress(params, InetAddress.getByName("127.0.0.1")));
        peerGroup.addAddress(new PeerAddress(params, InetAddress.getByName("46.101.113.112")));
        peerGroup.startAsync();
        peerGroup.downloadBlockChain();


        // And take them!
        System.out.println("CurrBalance " + wallet.getBalance().toFriendlyString());
        System.out.format("Num Peers: %d\n", peerGroup.numConnectedPeers());

        Wallet.SendResult result = wallet.sendOPReturnTransaction(destination, peerGroup, "Test".getBytes(), Coin.CENT);
        // Wait a few seconds to let the packets flush out to the network (ugly).

        System.out.println("Claiming " + wallet.getBalance().toFriendlyString());

        System.out.println(result.tx.getHashAsString());
        Transaction trans = result.broadcastComplete.get();
        System.out.println(trans.getHashAsString());
        peerGroup.stopAsync();
    }



}
