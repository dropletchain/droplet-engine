package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.Base58;
import org.bitcoinj.core.DumpedPrivateKey;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.wallet.Wallet;

import java.math.BigInteger;

/**
 * Created by lukas on 09.05.17.
 */

public class PolicyManipulationClient {

    private Wallet wallet;

    public PolicyManipulationClient(NetworkParameters params, String privKey) {
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
        Address destination = Address.fromBase58(params, args[1]);

        // Import the private key to a fresh wallet.
        Wallet wallet = new Wallet(params);
        wallet.importKey(key);
    }
}
