package ch.lubu;

import kademlia.dht.KadContent;

import javax.crypto.*;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.security.*;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.zip.DataFormatException;
import java.util.zip.Deflater;
import java.util.zip.Inflater;

/**
 * Represents a data block containing data
 */
public class Block implements Iterator<Entry>, Iterable<Entry>{

    private int maxEntries;

    private List<Entry> entries = new ArrayList<>();

    private Block(int maxEntries) {
        this.maxEntries = maxEntries;
    }

    public static Block getNewBlock(int maxEntries) {
        return new Block(maxEntries);
    }

    /**
     * Decodes an encoded block
     * @param data
     * @return
     */
    public static Block getBlockFromData(byte[] data) {
        ByteBuffer buffer = ByteBuffer.wrap(data);
        Block block = new Block(1000);
        while (buffer.hasRemaining()) {
            long timestamp = buffer.getLong();
            int meta_len = buffer.getInt();
            char[] metaByte = new char[meta_len];
            for (int i = 0; i < meta_len; i++) {
                metaByte[i] = buffer.getChar();
            }
            String meta = new String(metaByte);
            double value = buffer.getDouble();
            block.entries.add(new Entry(timestamp, meta, value));
        }
        block.maxEntries = block.entries.size();
        return block;
    }

    private static byte[] getDecompressedData(byte[] compressedBlock) throws DataFormatException {
        Inflater decompresser = new Inflater();
        decompresser.setInput(compressedBlock, 0, compressedBlock.length);
        //Hack maybe dynamic buffer?
        byte[] output_buffer = new byte[compressedBlock.length * 100];
        int resultLength = decompresser.inflate(output_buffer);
        decompresser.end();
        byte[] result = new byte[resultLength];
        System.arraycopy(output_buffer, 0, result, 0, resultLength);
        return result;
    }

    /**
     * Decodes an encode compressed block
     * @param compressedBlock
     * @return
     * @throws DataFormatException
     */
    public static Block getBlockFromCompressed(byte[] compressedBlock) throws DataFormatException {
        return getBlockFromData(getDecompressedData(compressedBlock));
    }

    /**
     * Decodes an encrypted compressed block
     * @param compressedEncryptedBlock
     * @param key
     * @return
     * @throws InvalidKeyException
     */
    public static Block getBlockFromCompressedEncrypted(byte[] compressedEncryptedBlock, byte[] key) throws InvalidKeyException {
        SecretKeySpec skeySpec = new SecretKeySpec(key, "AES");
        Cipher cipher = null;
        try {
            cipher = Cipher.getInstance("AES/CBC/PKCS5PADDING");
            byte[] ivByte = new byte[cipher.getBlockSize()];
            System.arraycopy(compressedEncryptedBlock, 0, ivByte, 0, ivByte.length);

            IvParameterSpec iv = new IvParameterSpec(ivByte);
            cipher.init(Cipher.DECRYPT_MODE, skeySpec, iv);
            byte[] compressedData = cipher.doFinal(compressedEncryptedBlock, ivByte.length, compressedEncryptedBlock.length - ivByte.length);
            return getBlockFromData(getDecompressedData(compressedData));
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (NoSuchPaddingException e) {
            e.printStackTrace();
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
        } catch (IllegalBlockSizeException e) {
            e.printStackTrace();
        } catch (BadPaddingException e) {
            e.printStackTrace();
        } catch (DataFormatException e) {
            e.printStackTrace();
        }
        return null;
    }

    /**
     * Decdoes a compressed, encoded and signed block
     * @param compressedEncryptedBlock
     * @param key
     * @param pubKey
     * @return
     * @throws InvalidKeyException
     * @throws BlockVerficationFailure
     */
    public static Block getBlockFromCompressedEncryptedSignedBlock(byte[] compressedEncryptedBlock, byte[] key, PublicKey pubKey) throws InvalidKeyException, BlockVerficationFailure {
        try {
            Signature ver = Signature.getInstance("SHA256withECDSA");
            ByteBuffer buff = ByteBuffer.wrap(compressedEncryptedBlock);
            int lenSig = buff.getInt();
            byte[] sig = new byte[lenSig];
            byte[] data = new byte[compressedEncryptedBlock.length - Integer.BYTES - lenSig];
            buff.get(sig);
            buff.get(data);
            ver.initVerify(pubKey);
            ver.update(data);
            if(!ver.verify(sig)) {
                throw new BlockVerficationFailure("Invalid signature!", compressedEncryptedBlock);
            } else {
                return getBlockFromCompressedEncrypted(data, key);
            }

        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (SignatureException e) {
            e.printStackTrace();
        }
        return null;
    }

    private int getSizeEntry(Entry entry) {
        return 8 + 4 + entry.getMetadata().length() * 2 + 8;
    }

    private byte[] entryToByte(Entry entry) {
        int len = entry.getMetadata().length();
        int lenTot = getSizeEntry(entry);
        ByteBuffer data = ByteBuffer.allocate(lenTot);
        data.putLong(entry.getTimestamp());
        data.putInt(len);
        for (char v : entry.getMetadata().toCharArray())
            data.putChar(v);
        data.putDouble(entry.getValue());
        return data.array();
    }

    /**
     * Adds Iot data to a block
     * @param entry
     * @return
     */
    public boolean putIotData(Entry entry) {
        if (this.entries.size() >= maxEntries)
            return false;
        this.entries.add(entry);
        return true;
    }

    public byte[] getData() {
        int len_tot = 0;
        for (Entry item : entries)
            len_tot += getSizeEntry(item);
        int cur_index = 0;
        byte[] tot = new byte[len_tot];
        for (Entry item : entries) {
            byte[] tmp = entryToByte(item);
            System.arraycopy(tmp, 0, tot, cur_index, tmp.length);
            cur_index += tmp.length;
        }
        return tot;
    }


    public byte[] getCompressedData() {
        Deflater compresser = new Deflater();
        byte[] input = getData();
        byte[] output_buffer = new byte[input.length];
        compresser.setInput(input);
        compresser.finish();
        int numBytes = compresser.deflate(output_buffer);
        byte[] result = new byte[numBytes];
        System.arraycopy(output_buffer, 0, result, 0, numBytes);
        return result;
    }

    public byte[] getCompressedAndEncryptedData(byte[] key) throws Exception {
        SecretKeySpec skeySpec = new SecretKeySpec(key, "AES");

        Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5PADDING");
        SecureRandom randomSecureRandom = new SecureRandom();
        byte[] ivBytes = new byte[cipher.getBlockSize()];
        randomSecureRandom.nextBytes(ivBytes);

        IvParameterSpec iv = new IvParameterSpec(ivBytes);

        cipher.init(Cipher.ENCRYPT_MODE, skeySpec, iv);

        byte[] compressedData = getCompressedData();
        byte[] encrypted = cipher.doFinal(compressedData);
        byte[] finalResult = new byte[ivBytes.length + encrypted.length];
        System.arraycopy(ivBytes, 0, finalResult, 0, ivBytes.length);
        System.arraycopy(encrypted,0, finalResult, ivBytes.length, encrypted.length);
        return finalResult;
    }

    public byte[] getCompressedEncryptedSignedData(byte[] key, PrivateKey privECDSA) throws Exception {
        Signature sig = Signature.getInstance("SHA256withECDSA");
        sig.initSign(privECDSA);
        byte[] data = getCompressedAndEncryptedData(key);
        sig.update(data);
        byte[] signature = sig.sign();
        ByteBuffer buff = ByteBuffer.allocate(data.length + signature.length + Integer.BYTES);
        buff.putInt(signature.length);
        buff.put(signature);
        buff.put(data);
        return buff.array();
    }

    private int curID = -1;

    @Override
    public boolean hasNext() {
        return curID + 1 < entries.size();
    }

    @Override
    public Entry next() {
        if(hasNext()) {
            curID ++;
            return entries.get(curID);
        } else {
            return null;
        }
    }

    @Override
    public Iterator<Entry> iterator() {
        return this;
    }

    public int getRemainingSpace() {
        return this.maxEntries - entries.size();
    }

    public int getNumEntries() {
        return entries.size();
    }
}
