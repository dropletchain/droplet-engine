package ch.lubu;

import com.google.common.base.Stopwatch;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.ByteBuffer;
import java.security.*;
import java.security.spec.ECGenParameterSpec;
import java.util.HashMap;
import java.util.Random;
import java.util.concurrent.TimeUnit;

public class Cryptobench {

    static class TimeLogger {

        public HashMap<String, Long> times = new HashMap<>();

        public void logTime(String tag, long value) {
            times.put(tag, value);
        }

    }

    private static Stopwatch stopwatch = Stopwatch.createUnstarted();


    public static byte[] encryptGcm(byte[] key, byte[] data, TimeLogger logger) throws Exception {
        SecretKeySpec skeySpec = new SecretKeySpec(key, "AES");
        int nonceSize = 12;

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        SecureRandom randomSecureRandom = new SecureRandom();
        byte[] ivBytes = new byte[nonceSize];
        randomSecureRandom.nextBytes(ivBytes);

        GCMParameterSpec gcm = new GCMParameterSpec(cipher.getBlockSize() * 8, ivBytes);

        cipher.init(Cipher.ENCRYPT_MODE, skeySpec, gcm);

        stopwatch.reset();
        stopwatch.start();
        byte[] encrypted = cipher.doFinal(data);
        stopwatch.stop();
        logger.logTime("gcm_encrypt", stopwatch.elapsed(TimeUnit.NANOSECONDS));

        byte[] finalResult = new byte[ivBytes.length + encrypted.length];
        System.arraycopy(ivBytes, 0, finalResult, 0, ivBytes.length);
        System.arraycopy(encrypted,0, finalResult, ivBytes.length, encrypted.length);
        return finalResult;
    }

    public static byte[] signData(PrivateKey privECDSA, byte[] data, TimeLogger logger) throws Exception {
        Signature sig = Signature.getInstance("SHA256withECDSA");
        sig.initSign(privECDSA);

        stopwatch.reset();
        stopwatch.start();
        sig.update(data);
        byte[] signature = sig.sign();
        stopwatch.stop();
        logger.logTime("ecdsa_sign", stopwatch.elapsed(TimeUnit.NANOSECONDS));

        ByteBuffer buff = ByteBuffer.allocate(data.length + signature.length + Integer.BYTES);
        buff.putInt(signature.length);
        buff.put(signature);
        buff.put(data);
        return buff.array();
    }


    public static byte[] hashData(byte[] data, TimeLogger logger) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");

        stopwatch.reset();
        stopwatch.start();
        md.update(data); // Change this to "UTF-16" if needed
        byte[] digest = md.digest();
        stopwatch.stop();
        logger.logTime("hash_data", stopwatch.elapsed(TimeUnit.NANOSECONDS));
        return digest;
    }



    public static void main(String[] args) {
        int numIterations = 10000;

        if(args.length>0) {
            numIterations = Integer.valueOf(args[0]);
        }

        KeyPairGenerator g = null;
        Random rand = new Random();
        BigDecimal time_hash = BigDecimal.ZERO;
        BigDecimal time_sign = BigDecimal.ZERO;
        BigDecimal time_gcm = BigDecimal.ZERO;

        try {
            g = KeyPairGenerator.getInstance("EC");
            ECGenParameterSpec kpgparams = new ECGenParameterSpec("secp256r1");
            g.initialize(kpgparams);

            for (int round=0; round < numIterations; round++) {
                TimeLogger logger = new TimeLogger();

                KeyPair pair = g.generateKeyPair();
                byte[] data = new byte[32];
                rand.nextBytes(data);
                signData(pair.getPrivate(), data, logger);

                hashData(data, logger);

                byte[] key = new byte[16];
                rand.nextBytes(key);
                data = new byte[16];
                rand.nextBytes(data);
                encryptGcm(key,data, logger);

                long time_hash_cur = logger.times.get("hash_data");
                long time_sign_cur = logger.times.get("ecdsa_sign");
                long time_gcm_cur = logger.times.get("gcm_encrypt");

                System.out.format("Hash: %d, Sign: %d, AesGcm: %d\n", time_hash_cur, time_sign_cur, time_gcm_cur);

                time_hash = time_hash.add(BigDecimal.valueOf(time_hash_cur));
                time_sign = time_sign.add(BigDecimal.valueOf(time_sign_cur));
                time_gcm = time_gcm.add(BigDecimal.valueOf(time_gcm_cur));
            }
            time_hash = time_hash.divide(BigDecimal.valueOf(numIterations), RoundingMode.HALF_UP);
            time_sign = time_sign.divide(BigDecimal.valueOf(numIterations), RoundingMode.HALF_UP);
            time_gcm = time_gcm.divide(BigDecimal.valueOf(numIterations), RoundingMode.HALF_UP);

            System.out.format("Avg Hash: %s, Avg Sign: %s, Avg AesGcm: %s\n", time_hash.toString(),
                    time_sign.toString(), time_gcm.toString());
        } catch (Exception e) {
            e.printStackTrace();
        }

    }
}
