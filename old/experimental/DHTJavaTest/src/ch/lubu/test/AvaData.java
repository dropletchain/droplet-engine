package ch.lubu.test;

import ch.lubu.Chunk;
import ch.lubu.Entry;
import ch.lubu.avadata.AvaDataEntry;
import ch.lubu.avadata.AvaDataImporter;

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

/**
 * Created by lukas on 27.02.17.
 */
public class AvaData {

    int counter = 0;

    public List<Chunk> transferData(int maxBlocksize) throws IOException {
        ArrayList<Chunk> chunks = new ArrayList<>();
        Chunk curChunk = Chunk.getNewBlock(maxBlocksize);
        AvaDataImporter importer = null;
        for(int item=1; item<=10; item ++) {
            try {
                importer = new AvaDataImporter("./DATA", item);
                while (importer.hasNext()) {
                    AvaDataEntry entry = importer.next();
                    if (curChunk.getRemainingSpace() < 10) {
                        chunks.add(curChunk);
                        curChunk = Chunk.getNewBlock(maxBlocksize);
                    }
                    curChunk.putIotData(new Entry(entry.time_stamp, "temp_amp", entry.temp_amb));
                    curChunk.putIotData(new Entry(entry.time_stamp, "temp_skin", entry.temp_skin));
                    curChunk.putIotData(new Entry(entry.time_stamp, "sleep_state", entry.sleep_state));
                    curChunk.putIotData(new Entry(entry.time_stamp, "avg_bpm", entry.avg_bpm));
                    curChunk.putIotData(new Entry(entry.time_stamp, "activity_index", entry.activity_index));
                    curChunk.putIotData(new Entry(entry.time_stamp, "accel_z", entry.accel_z));
                    curChunk.putIotData(new Entry(entry.time_stamp, "perfusion_index_green", entry.perfusion_index_green));
                    curChunk.putIotData(new Entry(entry.time_stamp, "perfusion_index_infrared", entry.perfusion_index_infrared));
                    curChunk.putIotData(new Entry(entry.time_stamp, "phase_60kHz", entry.phase_60kHz));
                    curChunk.putIotData(new Entry(entry.time_stamp, "impedance_60kHz", entry.impedance_60kHz));

                    counter += 10;
                }

            } finally {
                if (importer != null)
                    importer.close();
            }
        }
        if(curChunk.getNumEntries() > 0) {
            chunks.add(curChunk);
        }
        return chunks;
    }



    public static void main(String[] args) {
        AvaData avaData = new AvaData();
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

            List<Chunk> chunks = avaData.transferData(maxBlocksize);
            System.out.format("--- Max Chunksize: %d,  Num Chunks: %d, Num Entries: %d ---\n", maxBlocksize, chunks.size(), avaData.counter);

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
                byte[] data = chunk.getCompressedEncryptedSignedData(secretKey.getEncoded(), pair.getPrivate(), true);
                totalSize += data.length;
                Chunk.getBlockFromCompressedEncryptedSignedBlock(data, secretKey.getEncoded(), pair.getPublic(), true);
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
