package ch.ethz.blokcaditapi.storage;

import android.annotation.TargetApi;
import android.os.Build;

import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.Sha256Hash;

import java.io.ByteArrayOutputStream;
import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.spec.ECGenParameterSpec;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.DataFormatException;
import java.util.zip.Deflater;
import java.util.zip.Inflater;

import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/**
 * Created by lukas on 08.05.17.
 */

public class StorageCrypto {

    public static byte[] compressData(byte[] data) {
        Deflater compresser = new Deflater();
        compresser.setInput(data);
        compresser.finish();
        ByteArrayOutputStream bufferStream = new ByteArrayOutputStream(data.length);
        while (!compresser.finished()) {
            byte[] output_buffer = new byte[data.length];
            int numBytes = compresser.deflate(output_buffer);
            bufferStream.write(output_buffer, 0, numBytes);
        }
        return bufferStream.toByteArray();
    }

    public static byte[] decompressData(byte[] data) throws DataFormatException {
        Inflater decompresser = new Inflater();
        decompresser.setInput(data, 0, data.length);
        ByteArrayOutputStream bufferStream = new ByteArrayOutputStream(data.length * 2);
        while (decompresser.getRemaining() > 0) {
            byte[] temp = new byte[data.length];
            int len = decompresser.inflate(temp);
            bufferStream.write(temp, 0, len);
        }
        return bufferStream.toByteArray();
    }

    @TargetApi(Build.VERSION_CODES.KITKAT)
    public static byte[] encryptAESGcm(byte[] key, byte[] data, byte[] plainData) throws InvalidKeyException {
        try {
            SecretKeySpec skeySpec = new SecretKeySpec(key, "AES");
            int nonceSize = 12;

            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            SecureRandom randomSecureRandom = new SecureRandom();
            byte[] ivBytes = new byte[nonceSize];
            randomSecureRandom.nextBytes(ivBytes);

            GCMParameterSpec gcm = new GCMParameterSpec(cipher.getBlockSize() * 8, ivBytes);

            cipher.init(Cipher.ENCRYPT_MODE, skeySpec, gcm);

            cipher.updateAAD(plainData);
            byte[] encrypted = cipher.doFinal(data);
            byte[] finalResult = new byte[ivBytes.length + encrypted.length];
            System.arraycopy(ivBytes, 0, finalResult, 0, ivBytes.length);
            System.arraycopy(encrypted, 0, finalResult, ivBytes.length, encrypted.length);
            return finalResult;
        } catch (NoSuchPaddingException e) {
            e.printStackTrace();
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
        } catch (IllegalBlockSizeException e) {
            e.printStackTrace();
        } catch (BadPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static List<byte[]> splitGCMCiphertext(byte[] ciphertext) {
        int sizeTag = 0;
        ArrayList<byte[]> result = new ArrayList<>(2);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            sizeTag = cipher.getBlockSize() * 8;
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (NoSuchPaddingException e) {
            e.printStackTrace();
        }
        byte[] tag = new byte[sizeTag];
        byte[] data = new byte[ciphertext.length - sizeTag];
        System.arraycopy(ciphertext, ciphertext.length - sizeTag, tag, 0, sizeTag);
        System.arraycopy(ciphertext, 0, data, 0, ciphertext.length - sizeTag);
        result.add(data);
        result.add(tag);
        return result;
    }

    @TargetApi(Build.VERSION_CODES.KITKAT)
    public static byte[] decryptAESGcm(byte[] key, byte[] encData, byte[] plainData) throws InvalidKeyException, BadPaddingException {
        SecretKeySpec skeySpec = new SecretKeySpec(key, "AES");
        Cipher cipher = null;
        int nonceSize = 12;
        try {
            cipher = Cipher.getInstance("AES/GCM/NoPadding");
            byte[] ivByte = new byte[nonceSize];
            System.arraycopy(encData, 0, ivByte, 0, ivByte.length);

            GCMParameterSpec gcmParams = new GCMParameterSpec(cipher.getBlockSize() * 8, ivByte);
            cipher.init(Cipher.DECRYPT_MODE, skeySpec, gcmParams);
            cipher.updateAAD(plainData);
            return cipher.doFinal(encData, ivByte.length, encData.length - ivByte.length);
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (NoSuchPaddingException e) {
            e.printStackTrace();
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
        } catch (IllegalBlockSizeException e) {
            e.printStackTrace();
        }
        return null;
    }

    private static byte[] signMessage(ECKey key, byte[] data) {
        Sha256Hash hash = Sha256Hash.of(data);
        return key.sign(hash).encodeToDER();
    }

    private static boolean verifyMessage(ECKey key, byte[] data, byte[] signature) {
        Sha256Hash hash = Sha256Hash.of(data);
        return key.verify(hash, ECKey.ECDSASignature.decodeFromDER(signature));
    }

    public static byte[] signECDSA(ECKey key, byte[] toSign) throws InvalidKeyException {
        return signMessage(key, toSign);
    }

    public static boolean checkECDSASig(ECKey key, byte[] data, byte[] signature) throws InvalidKeyException {
        return verifyMessage(key, data, signature);
    }

    public static KeyPair generateECDSAKeys() {
        KeyPairGenerator g = null;
        try {
            g = KeyPairGenerator.getInstance("EC");
            ECGenParameterSpec kpgparams = new ECGenParameterSpec("secp256k1");
            g.initialize(kpgparams);
            return g.generateKeyPair();
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
        }
        return null;
    }


}
