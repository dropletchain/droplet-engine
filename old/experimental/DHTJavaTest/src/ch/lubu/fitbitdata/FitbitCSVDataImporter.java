package ch.lubu.fitbitdata;

import ch.lubu.Entry;

import java.io.*;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;

/**
 * Created by lukas on 27.02.17.
 */
public class FitbitCSVDataImporter {


    static DateFormat dfm = new SimpleDateFormat("dd-mm-yyyy");

    public static List<Entry> importCSVData(File data) {
        ArrayList<Entry> result = new ArrayList<>();
        BufferedReader reader = null;
        try {
            reader = new BufferedReader(new FileReader(data));
            String line = reader.readLine();
            String title = null;
            String[] names = null;
            String[] values;
            int count = 0;
            while (line!=null) {
                if(count==0) {
                    title = line;
                } else if(count==1) {
                    names = line.split(",");
                } else {
                    values = line.split("\",\"");

                    if(values.length == 1 && !line.isEmpty()) {
                        title = line;
                        names = null;
                        line = reader.readLine();
                        count = 1;
                        continue;
                    }
                    if(line.isEmpty() || values.length < 2 || names == null || title == null) {
                        line = reader.readLine();
                        count++;
                        continue;
                    }
                    long utimestamp = dfm.parse(values[0].replace("\"","")).getTime() / 1000;
                    for(int idx=1; idx<values.length; idx++) {
                        double value = Double.valueOf(values[idx].replace("\"","").replace(",",""));
                        String meta = title + names[idx];
                        result.add(new Entry(utimestamp, meta,value));
                    }
                }
                line = reader.readLine();
                count++;
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (ParseException e) {
            e.printStackTrace();
        } finally {
            if(reader!=null)
                try {
                    reader.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
        }
        return result;
    }

}
