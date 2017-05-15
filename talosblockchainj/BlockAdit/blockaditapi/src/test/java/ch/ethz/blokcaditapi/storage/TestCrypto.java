package ch.ethz.blokcaditapi.storage;

import android.annotation.TargetApi;
import android.os.Build;

import org.bitcoinj.core.Base58;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.params.RegTestParams;
import org.junit.Test;

import java.util.Random;

import javax.crypto.AEADBadTagException;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertTrue;

/**
 * Created by lukas on 08.05.17.
 */

public class TestCrypto {

    @Test
    public void testcompression() throws Exception {
        Random rand = new Random();
        byte[] data = new byte[345];
        rand.nextBytes(data);

        byte[] compressed = StorageCrypto.compressData(data);
        byte[] decomp = StorageCrypto.decompressData(compressed);

        assertArrayEquals(data, decomp);
    }

    @TargetApi(Build.VERSION_CODES.KITKAT)
    @Test
    public void testGCM() throws Exception {
        Random rand = new Random();
        byte[] key = new byte[16];
        byte[] plain = new byte[10];
        byte[] data = new byte[345];
        rand.nextBytes(key);
        rand.nextBytes(plain);
        rand.nextBytes(data);

        byte[] enncrypted = StorageCrypto.encryptAESGcm(key, data, plain);
        byte[] dec = StorageCrypto.decryptAESGcm(key, enncrypted, plain);
        assertArrayEquals(data, dec);

        boolean catched = false;
        plain[1] = 1;
        plain[2] = 1;
        try {
            StorageCrypto.decryptAESGcm(key, enncrypted, plain);
        } catch (AEADBadTagException e) {
            catched = true;
        }
        assertTrue(catched);
    }

    private ECKey wifToKey(String priv, boolean isTestnet) {
        byte[] data = Base58.decodeChecked(priv);
        char first = priv.charAt(0);
        byte[] real = null;
        if ((isTestnet && first =='c') ||
                (!isTestnet && (first=='K' || first=='L'))) {
            real = new byte[data.length - 2];
            System.arraycopy(data, 1, real, 0, data.length - 2);
        } else {
            real = new byte[data.length - 1];
            System.arraycopy(data, 1, real, 0, data.length - 1);
        }
        return ECKey.fromPrivate(real);
    }

    @Test
    public void testToken() throws Exception {
        String priv = "cPuiZfHTkWAPhPvMSPetvP1jRarkQ8BRtPrEVuP5PhDsTGrrcm2f";
        ECKey key = wifToKey(priv, true);
        String owner = "dfasdfasfasdfdsf";
        int streamId = 2;
        byte[] chunkKey = new byte[16];
        byte[] nonce = new byte[16];

        QueryToken token = QueryToken.createQueryToken(owner,streamId, nonce, chunkKey, key);
        byte[] signData = QueryToken.getBytesSignature(owner, streamId, nonce, chunkKey);

        System.out.println(key.getPrivateKeyAsHex());
        System.out.println(key.getPublicKeyAsHex());
        System.out.println(key.getPrivateKeyAsWiF(RegTestParams.get()));

        System.out.println(Util.bytesToHexString(signData));
        String tokenJs = token.toJSON();
        System.out.print(tokenJs);
    }


}
