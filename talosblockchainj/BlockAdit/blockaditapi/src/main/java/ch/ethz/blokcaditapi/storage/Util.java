package ch.ethz.blokcaditapi.storage;

import org.bitcoinj.core.Base58;
import org.bitcoinj.core.ECKey;

/**
 * Created by lukas on 08.05.17.
 */

public class Util {

    public static byte[] hexStringToByteArray(String s) {
        int len = s.length();
        byte[] data = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            data[i / 2] = (byte) ((Character.digit(s.charAt(i), 16) << 4)
                    + Character.digit(s.charAt(i + 1), 16));
        }
        return data;
    }

    private final static char[] hexArray = "0123456789abcdef".toCharArray();

    public static String bytesToHexString(byte[] bytes) {
        char[] hexChars = new char[bytes.length * 2];
        for (int j = 0; j < bytes.length; j++) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = hexArray[v >>> 4];
            hexChars[j * 2 + 1] = hexArray[v & 0x0F];
        }
        return new String(hexChars);
    }

    public static ECKey wifToKey(String priv, boolean isTestnet) {
        byte[] data = Base58.decodeChecked(priv);
        char first = priv.charAt(0);
        byte[] real;
        if ((isTestnet && first == 'c') ||
                (!isTestnet && (first == 'K' || first == 'L'))) {
            real = new byte[data.length - 2];
            System.arraycopy(data, 1, real, 0, data.length - 2);
        } else {
            real = new byte[data.length - 1];
            System.arraycopy(data, 1, real, 0, data.length - 1);
        }
        return ECKey.fromPrivate(real);
    }
}
