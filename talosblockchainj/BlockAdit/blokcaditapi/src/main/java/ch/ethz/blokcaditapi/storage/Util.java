package ch.ethz.blokcaditapi.storage;

import java.math.BigInteger;

/**
 * Created by lukas on 08.05.17.
 */

public class Util {

    public static byte[] hexStringToByteArray(String s) {
        return new BigInteger(s,16).toByteArray();
    }

    private final static char[] hexArray = "0123456789abcdef".toCharArray();

    public static String bytesToHexString(byte[] bytes) {
        char[] hexChars = new char[bytes.length * 2];
        for ( int j = 0; j < bytes.length; j++ ) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = hexArray[v >>> 4];
            hexChars[j * 2 + 1] = hexArray[v & 0x0F];
        }
        return new String(hexChars);
    }
}
