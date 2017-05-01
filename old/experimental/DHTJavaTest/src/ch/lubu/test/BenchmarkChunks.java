package ch.lubu.test;

import ch.lubu.Chunk;
import ch.lubu.Entry;
import ch.lubu.avadata.AvaDataEntry;
import ch.lubu.avadata.AvaDataImporter;
import ch.lubu.fitbitdata.FitbitCSVDataImporter;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintStream;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Created by lukas on 10.03.17.
 */
public class BenchmarkChunks {

    private static Random randomness = new Random();

    public static List<Entry> importDataAva(String location) throws FileNotFoundException {
        ArrayList<Entry> chunks = new ArrayList<>();
        AvaDataImporter importer = null;
        for(int item=1; item<=10; item ++) {
            try {
                importer = new AvaDataImporter(location, item);
                while (importer.hasNext()) {
                    AvaDataEntry entry = importer.next();
                    chunks.add(new Entry(entry.time_stamp, "temp_amp", entry.temp_amb));
                    chunks.add(new Entry(entry.time_stamp, "temp_skin", entry.temp_skin));
                    chunks.add(new Entry(entry.time_stamp, "sleep_state", entry.sleep_state));
                    chunks.add(new Entry(entry.time_stamp, "avg_bpm", entry.avg_bpm));
                    chunks.add(new Entry(entry.time_stamp, "activity_index", entry.activity_index));
                    chunks.add(new Entry(entry.time_stamp, "accel_z", entry.accel_z));
                    chunks.add(new Entry(entry.time_stamp, "perfusion_index_green", entry.perfusion_index_green));
                    chunks.add(new Entry(entry.time_stamp, "perfusion_index_infrared", entry.perfusion_index_infrared));
                    chunks.add(new Entry(entry.time_stamp, "phase_60kHz", entry.phase_60kHz));
                    chunks.add(new Entry(entry.time_stamp, "impedance_60kHz", entry.impedance_60kHz));
                }

            } finally {
                if (importer != null)
                    try {
                        importer.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
            }
        }
        return chunks;
    }

    public static List<Entry> importDataFitBit(String location) {
        ArrayList<Entry> chunks = new ArrayList<>();
        File dir = new File(location);
        File[] directoryListing = dir.listFiles();
        for(File f: directoryListing) {
            List<Entry> entries = FitbitCSVDataImporter.importCSVData(f);
            for (Entry entry : entries) {
                chunks.add(entry);
            }
        }
        return chunks;
    }

    public static List<Chunk> getChunks(List<Entry> dataBase, int numEntries, int chunkSize) {
        ArrayList<Chunk> chunks = new ArrayList<>();
        int dataBaseSize = dataBase.size();
        Chunk curChunk = Chunk.getNewBlock(chunkSize);
        for(int entryCounter=0; entryCounter<numEntries; entryCounter++) {
            if (curChunk.getRemainingSpace() <= 0) {
                chunks.add(curChunk);
                curChunk = Chunk.getNewBlock(chunkSize);
            }
            curChunk.putIotData(dataBase.get(randomness.nextInt(dataBaseSize)));
        }
        return chunks;
    }

    private static int gloablIndex = 0;

    public static Chunk getChunk(List<Entry> dataBase, int numEntries, int maxEntries) {
        assert (numEntries<=maxEntries);
        int dataBaseSize = dataBase.size();
        Chunk curChunk = Chunk.getNewBlock(maxEntries);
        for (int index=0; index<numEntries; index++) {
            curChunk.putIotData(dataBase.get(gloablIndex % dataBaseSize));
            gloablIndex++;
        }
        return curChunk;
    }

    public static void runBenchmark(PrintStream out, int[] chunkSizes, List<Entry> dataBase, int numEntries, boolean useGCM) {
        out.format("%s,%s,%s\n", "Chunk Size", "CF Plain", "CF Encrypted");
        try {
            for (int chunkSize : chunkSizes) {
                KeyGenerator keyGen = KeyGenerator.getInstance("AES");
                keyGen.init(128); // for example
                SecretKey secretKey = keyGen.generateKey();

                SecureRandom random = new SecureRandom();
                KeyPairGenerator keyGenEC = KeyPairGenerator.getInstance("EC");
                keyGenEC.initialize(256, random);
                KeyPair pair = keyGenEC.generateKeyPair();

                List<Chunk> chunks = getChunks(dataBase, numEntries, chunkSize);
                int totalSizeBase = 0;
                for (Chunk chunk : chunks) {
                    byte[] data = chunk.getData();
                    totalSizeBase += data.length;
                    //Block.getBlockFromData(data);
                }
                //BigDecimal avg = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(chunks.size()), RoundingMode.HALF_UP);
                //System.out.format("Total Size: %d, Average Chunk Size: %s\n", totalSizeBase, avg.toString());

                int totalSize = 0;
                for (Chunk block : chunks) {
                    byte[] data = block.getCompressedData();
                    totalSize += data.length;
                    //Block.getBlockFromCompressed(data);
                }
                BigDecimal improventPlain = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(totalSize), 2, RoundingMode.HALF_UP);
                //System.out.format("Total Size: %d, Average Chunk Size: %s, Improvement to Basecase: %s\n", totalSize, avg.toString(), improvent.toString());

                totalSize = 0;
                for (Chunk chunk : chunks) {
                    byte[] data = chunk.getCompressedEncryptedSignedData(secretKey.getEncoded(), pair.getPrivate(), useGCM);
                    totalSize += data.length;
                }
                BigDecimal improventEnc = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(totalSize), 2, RoundingMode.HALF_UP);
                out.format("%d,%s,%s\n", chunkSize, improventPlain.toString(), improventEnc.toString());
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void runBenchmarkEfficient(PrintStream out, int[] chunkSizes, List<Entry> dataBase, int numEntries, boolean useGCM) {
        out.format("%s,%s,%s\n", "Chunk Size", "CF Plain", "CF Encrypted");
        try {
            KeyGenerator keyGen = KeyGenerator.getInstance("AES");
            keyGen.init(128); // for example
            SecretKey secretKey = keyGen.generateKey();

            SecureRandom random = new SecureRandom();
            KeyPairGenerator keyGenEC = KeyPairGenerator.getInstance("EC");
            keyGenEC.initialize(256, random);
            KeyPair pair = keyGenEC.generateKeyPair();

            for (int chunkSize : chunkSizes) {
                randomness = new Random(123456L);
                int numBlocks = numEntries/chunkSize;

                int totalSizeBase = 0;
                int totalSizePlain = 0;
                int totalSizeEnc = 0;

                gloablIndex = 0;

                for(int blockCounter=0; blockCounter<numBlocks; blockCounter++) {
                    Chunk chunk = getChunk(dataBase, chunkSize, chunkSize);
                    byte[] data = chunk.getData();
                    totalSizeBase += data.length;

                    //plain compressed
                    data = chunk.getCompressedData();
                    totalSizePlain += data.length;

                    //compressed + encrypted + signed
                    data = chunk.getCompressedEncryptedSignedData(secretKey.getEncoded(), pair.getPrivate(), useGCM);
                    totalSizeEnc += data.length;
                }

                int mod = numEntries % chunkSize;
                if(mod != 0) {
                    Chunk chunk = getChunk(dataBase, mod, chunkSize);
                    byte[] data = chunk.getData();
                    totalSizeBase += data.length;

                    //plain compressed
                    data = chunk.getCompressedData();
                    totalSizePlain += data.length;

                    //compressed + encrypted + signed
                    data = chunk.getCompressedEncryptedSignedData(secretKey.getEncoded(), pair.getPrivate(), useGCM);
                    totalSizeEnc += data.length;
                }

                BigDecimal improventPlain = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(totalSizePlain), 2, RoundingMode.HALF_UP);
                BigDecimal improventEnc = BigDecimal.valueOf(totalSizeBase).divide(BigDecimal.valueOf(totalSizeEnc), 2, RoundingMode.HALF_UP);
                out.format("%d,%s,%s\n", chunkSize, improventPlain.toString(), improventEnc.toString());
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        boolean useFitbit = true;
        int numEntries = 10000;
        int numChunksizes = 16;
        int from = 0;
        if (args.length >= 3) {
            useFitbit = Integer.valueOf(args[0]) == 1;
            numEntries = Integer.valueOf(args[1]);
            numChunksizes = Integer.valueOf(args[2]);
            if(args.length >= 4) {
                from =  Integer.valueOf(args[4]);
            }
        }
        String locationAva = "./DATA";
        String locationFitbit = "./../../raw-data/FitBit/";
        int[] chunkSizes = null;

        chunkSizes = new int[numChunksizes - from];
        for (int i = 0; i < numChunksizes - from; i++) {
            chunkSizes[i] = 1 << (i + 1 + from);
        }

        List<Entry> entries = null;
        if(useFitbit) {
            entries = importDataFitBit(locationFitbit);
        } else {
            try {
                entries = importDataAva(locationAva);
            } catch (FileNotFoundException e) {
                e.printStackTrace();
            }
        }
        runBenchmarkEfficient(System.out, chunkSizes, entries, numEntries, true);

    }
}
