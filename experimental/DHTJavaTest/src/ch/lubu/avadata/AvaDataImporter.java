package ch.lubu.avadata;

import java.io.*;
import java.math.BigDecimal;
import java.util.Iterator;


/**
 * Created by lukas on 30.09.16.
 */

public class AvaDataImporter implements Iterator<AvaDataEntry>, Closeable {

    BufferedReader reader;

    String curLine = null;

    public AvaDataImporter(String path, int num) throws FileNotFoundException {
        File file = new File(path + "/" + "data" + num +".csv");
        reader = new BufferedReader(new FileReader(file));
        try {
            reader.readLine();
            curLine = reader.readLine();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static int computeAVGBpm(String line) {
        String filtered = line.replace("[", "");
        filtered = filtered.replace("]", "");
        filtered = filtered.replace(" ", "");
        String[] numsStr = filtered.split(",");
        int[] nums = new int[numsStr.length];
        for(int i=0; i<nums.length; i++) {
            nums[i] = Integer.valueOf(numsStr[i]);
        }

        BigDecimal a = BigDecimal.ZERO;
        for(int i=0; i<nums.length; i++) {
            a = a.add(BigDecimal.valueOf(nums[i]));
        }
        a = a.divide(BigDecimal.valueOf(nums.length), BigDecimal.ROUND_HALF_UP);
        a = BigDecimal.valueOf(10000).divide(a, BigDecimal.ROUND_HALF_UP);
        a = a.multiply(BigDecimal.valueOf(6));
        return a.intValue();

    }

    private static AvaDataEntry createDataEnryFromLine(String line) {
        String[] arraySplit = line.split("\\[|\\]");
        String[] left = arraySplit[0].replace("\"", "").split(",");
        String mid = arraySplit[1];
        String[] right = arraySplit[2].replace("\"", "").split(",");
        String[] splits = new String[left.length+right.length];
        System.arraycopy(left, 0, splits, 0, left.length);
        System.arraycopy(right, 1, splits, left.length+1, right.length-1);
        splits[left.length] = mid;
        if(!(splits.length==13 || splits.length==14))
            throw new RuntimeException("Wrong Line: " + line);
        AvaDataEntry entry = new AvaDataEntry();
        entry.accel_z = Integer.valueOf(splits[1]);
        entry.activity_index= Integer.valueOf(splits[2]);
        entry.app_frame_no = Integer.valueOf(splits[3]);
        entry.impedance_60kHz = (new BigDecimal(splits[4])).multiply(BigDecimal.valueOf(100)).intValue();
        entry.perfusion_index_green = Integer.valueOf(splits[5]);
        entry.perfusion_index_infrared = Integer.valueOf(splits[6]);
        entry.phase_60kHz = Integer.valueOf(splits[7].replace("\"",""));
        entry.avg_bpm = computeAVGBpm(splits[8]);
        int index = 9;
        if(splits.length==13) {
            entry.rr_quality = 0;
        } else {
            entry.rr_quality = Integer.valueOf(splits[index++]);
        }
        entry.sleep_state = Integer.valueOf(splits[index++]);
        entry.temp_amb = Integer.valueOf(splits[index++]);
        entry.temp_skin = Integer.valueOf(splits[index++]);
        entry.time_stamp = Integer.valueOf(splits[index]);
        return entry;
    }

    @Override
    public boolean hasNext() {
        return curLine!=null;
    }

    @Override
    public AvaDataEntry next() {
        if(curLine == null)
            return null;
        AvaDataEntry res = createDataEnryFromLine(curLine);
        try {
            curLine = reader.readLine();
        } catch (IOException e) {
           curLine = null;
        }
        return res;
    }

    @Override
    public void remove() {

    }

    @Override
    public void close() throws IOException {
        reader.close();
    }
}
