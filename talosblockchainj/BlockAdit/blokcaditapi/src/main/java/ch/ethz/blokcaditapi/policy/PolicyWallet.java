package ch.ethz.blokcaditapi.policy;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.Coin;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.core.Transaction;
import org.bitcoinj.core.TransactionBroadcaster;
import org.bitcoinj.core.TransactionOutput;
import org.bitcoinj.script.ScriptBuilder;
import org.bitcoinj.wallet.SendRequest;
import org.bitcoinj.wallet.Wallet;

import java.util.ArrayList;
import java.util.List;

/**
 * Created by lukas on 11.05.17.
 */

public class PolicyWallet extends Wallet {

    private List<ECKey> policyKeys = new ArrayList<>();

    public PolicyWallet(NetworkParameters params) {
        super(params);
    }

    @Override
    public boolean importKey(ECKey key) {
        policyKeys.add(key);
        return super.importKey(key);

    }

    @Override
    public int importKeys(List<ECKey> keys) {
        policyKeys.addAll(keys);
        return super.importKeys(keys);
    }

    private ECKey getKeyForAddress(Address owner) {
        for (ECKey key : policyKeys)
            if (getOwnerForKey(key).equals(owner))
                return key;
        return null;
    }


    public ECKey createNewPolicyKey() {
        ECKey key = new ECKey();
        this.importKey(key);
        return key;
    }


    public Address getOwnerForKey(ECKey key) {
        return new Address(params, key.getPubKeyHash());
    }

    /*
    public static byte[] hashPassword(final char[] password, final byte[] salt, final int iterations, final int keyLength) {

        try {
            SecretKeyFactory skf = SecretKeyFactory.getInstance( "PBKDF2WithHmacSHA512" );
            PBEKeySpec spec = new PBEKeySpec(password, salt, iterations, keyLength);
            SecretKey key = skf.generateSecret(spec);
            byte[] res = key.getEncoded();
            return res;
        } catch( NoSuchAlgorithmException | InvalidKeySpecException e ) {
            throw new RuntimeException( e );
        }
    }

    public void presistToFile(String password, File file) {
        int saltbytes = 16;
        SecureRandom random = new SecureRandom();
        ByteBuffer buffer = ByteBuffer.allocate(policyKeys.size() *  32 + saltbytes);
        byte[] salt = new byte[saltbytes];
        random.nextBytes(salt);
        byte[] pwdkey = hashPassword(password.toCharArray(), salt, 10000, 128);
        buffer.put(salt);
        for (ECKey key : policyKeys) {
            buffer.put(key.getPrivKeyBytes());
        }


    }*/

    public SendResult sendOPReturnTransaction(Address owner, TransactionBroadcaster broadcaster, byte[] data, Coin fee) throws InsufficientMoneyException {
        Transaction tx = new Transaction(params);
        tx.addOutput(Coin.ZERO, ScriptBuilder.createOpReturnScript(data));
        List<TransactionOutput> candidates = calculateAllSpendCandidates(true, true);
        Coin amount = Coin.ZERO, amountOut;

        for (TransactionOutput cand : candidates) {
            Address outAddr =  cand.getAddressFromP2PKHScript(params);
            if (!(outAddr==null) && outAddr.equals(owner)) {
                tx.addInput(cand);
                amount =  amount.add(cand.getValue());
            }
            outAddr =  cand.getAddressFromP2SH(params);
            if (!(outAddr==null) && outAddr.equals(owner)) {
                tx.addInput(cand);
                amount = amount.add(cand.getValue());
            }
        }

        if (amount.isLessThan(fee)) {
            throw new InsufficientMoneyException(fee.subtract(amount));
        }
        amountOut = amount.subtract(fee);

        tx.addOutput(amountOut, owner);

        signTransaction(SendRequest.forTx(tx));

        final int size = tx.unsafeBitcoinSerialize().length;
        if (size > Transaction.MAX_STANDARD_TX_SIZE)
            throw new ExceededMaxTransactionSize();

        lock.lock();
        try {
            commitTx(tx);
        } finally {
            lock.unlock();
        }

        SendResult result = new SendResult();
        result.tx = tx;
        result.broadcast = broadcaster.broadcastTransaction(tx);
        result.broadcastComplete = result.broadcast.future();
        return result;
    }

}
