package ch.lubu.test;

import ch.lubu.Chunk;
import ch.lubu.Entry;
import ch.lubu.avadata.AvaDataEntry;
import ch.lubu.avadata.AvaDataImporter;
import ch.lubu.fitbitdata.FitbitCSVDataImporter;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.List;
import java.io.File;

/**
 * Created by lukas on 27.02.17.
 */
public class FitbitData {
    int counter = 0;

    public List<Chunk> transferData(int maxBlocksize) throws IOException {
        ArrayList<Chunk> chunks = new ArrayList<>();
        Chunk curChunk = Chunk.getNewBlock(maxBlocksize);
        File dir = new File("./../../raw-data/FitBit/");
        File[] directoryListing = dir.listFiles();
        for(File f: directoryListing) {
            List<Entry> entries = FitbitCSVDataImporter.importCSVData(f);
            for (Entry entry : entries) {
                if (curChunk.getRemainingSpace() <= 0) {
                    chunks.add(curChunk);
                    curChunk = Chunk.getNewBlock(maxBlocksize);
                }
                curChunk.putIotData(entry);
                counter++;
            }
        }
        if (curChunk.getNumEntries() > 0) {
            chunks.add(curChunk);
        }
        return chunks;
    }



    public static void main(String[] args) {
        FitbitData fitbitData = new FitbitData();
        int maxBlocksize = 1000;
        if(args.length > 1)
            maxBlocksize = Integer.valueOf(args[1]);

        try {
            KeyGenerator keyGen = KeyGenerator.getInstance("AES");
            keyGen.init(128); // for example
            SecretKey secretKey = keyGen.generateKey();

            SecureRandom random = new SecureRandom();
            KeyPairGenerator keyGenEC = KeyPairGenerator.getInstance("EC");
            keyGenEC.initialize(256, random);
            KeyPair pair = keyGenEC.generateKeyPair();

            List<Chunk> chunks = fitbitData.transferData(maxBlocksize);
            System.out.format("--- Max Chunksize: %d,  Num Chunks: %d, Num Entries: %d ---\n", maxBlocksize, chunks.size(), fitbitData.counter);

            System.out.println(".::Normal Data::.");
            int totalSizeBase = 0;
            for(Chunk chunk : chunks) {
                byte[] data = chunk.getData();
                totalSizeBase += data.length;
                //Block.getBlockFromData(data);
            }
            BigDecimal avg = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(chunks.size()), RoundingMode.HALF_UP);
            System.out.format("Total Size: %d, Average Chunk Size: %s\n", totalSizeBase, avg.toString());

            System.out.println(".::Compressed Data::.");
            int totalSize = 0;
            for(Chunk block : chunks) {
                byte[] data = block.getCompressedData();
                totalSize += data.length;
                //Block.getBlockFromCompressed(data);
            }
            avg = BigDecimal.valueOf(totalSize).divide(BigDecimal.valueOf(chunks.size()), RoundingMode.HALF_UP);
            BigDecimal improvent = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(totalSize),2, RoundingMode.HALF_UP);
            System.out.format("Total Size: %d, Average Chunk Size: %s, Improvement to Basecase: %s\n", totalSize, avg.toString(), improvent.toString());

            System.out.println(".::Compressed and Encrypted Data::.");
            totalSize = 0;
            for(Chunk chunk : chunks) {
                byte[] data = chunk.getCompressedAndEncryptedData(secretKey.getEncoded());
                totalSize += data.length;
                //Block.getBlockFromCompressedEncrypted(data, secretKey.getEncoded());
            }
            avg = BigDecimal.valueOf(totalSize).divide(BigDecimal.valueOf(chunks.size()), RoundingMode.HALF_UP);
            improvent = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(totalSize),2 , RoundingMode.HALF_UP);
            System.out.format("Total Size: %d, Average Chunk Size: %s, Improvement to Basecase: %s\n", totalSize, avg.toString(), improvent.toString());

            System.out.println(".::Compressed, Encrypted and Signed Data::.");
            totalSize = 0;
            for(Chunk chunk : chunks) {
                byte[] data = chunk.getCompressedEncryptedSignedData(secretKey.getEncoded(), pair.getPrivate());
                totalSize += data.length;
                //Block.getBlockFromCompressedEncryptedSignedBlock(data, secretKey.getEncoded(), pair.getPublic());
            }
            avg = BigDecimal.valueOf(totalSize).divide(BigDecimal.valueOf(chunks.size()), RoundingMode.HALF_UP);
            improvent = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(totalSize),2, RoundingMode.HALF_UP);
            System.out.format("Total Size: %d, Average Chunk Size: %s, Improvement to Basecase: %s\n", totalSize, avg.toString(), improvent.toString());
        } catch (IOException e) {
            e.printStackTrace();
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
