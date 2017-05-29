package ch.ethz.blockadit.blockadit;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import ch.ethz.blokcaditapi.storage.chunkentries.Entry;
import ch.ethz.blokcaditapi.storage.chunkentries.EntryProcessor;

/**
 * Created by lubums on 17.05.17.
 */

public class Aggregator {

    public static double[] aggregateDataForType(List<Entry> entries, Datatype datatype) {
        EntryProcessor processor = Datatype.getEntryProcessorForType(datatype);
        for (Entry entry : entries) {
            if (Datatype.filterPerType(datatype, entry.getMetadata())) {
                entry.accept(processor);
            }
        }
        return processor.getResult();
    }

    private static Date getDateFromTimestamp(long timestamp) {
        Date temp = new Date((long) ((int) timestamp) * 1000L);
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        try {
            return sdf.parse(sdf.format(temp));
        } catch (ParseException e) {
            e.printStackTrace();
            return new Date();
        }
    }

    public static class DateSummary {
        public java.sql.Date date;
        public List<Entry> entries;

        public DateSummary(java.sql.Date date, List<Entry> entries) {
            this.date = date;
            this.entries = entries;
        }
    }

    public static List<DateSummary> splitByDate(List<Entry> entries, Datatype datatype) {
        List<DateSummary> result = new ArrayList<>();
        Date cur = null;
        List<Entry> temp = new ArrayList<>();
        for (Entry entry : entries) {
            if (Datatype.filterPerType(datatype, entry.getMetadata())) {
                Date entryDate = getDateFromTimestamp(entry.getTimestamp());
                if (cur == null) {
                    cur = entryDate;
                } else if (!(cur.compareTo(entryDate) == 0)) {
                    result.add(new DateSummary(new java.sql.Date(cur.getTime()), temp));
                    cur = entryDate;
                    temp = new ArrayList<>();
                }
                temp.add(entry);
            }
        }
        if (!temp.isEmpty()) {
            result.add(new DateSummary(new java.sql.Date(cur.getTime()), temp));
        }
        return result;
    }

    public static class DateTimeSummary {
        public java.sql.Time time;
        public List<Entry> entries;

        public DateTimeSummary(java.sql.Time date, List<Entry> entries) {
            this.time = date;
            this.entries = entries;
        }
    }


    public static List<DateTimeSummary> splitByGranularity(List<Entry> entries, java.sql.Date date, long granularity, Datatype type) {
        List<DateTimeSummary> result = new ArrayList<>();
        long start = date.getTime() / 1000;
        long cur = start;
        int idx = 0;
        List<Entry> temp = new ArrayList<>();
        for (Entry entry : entries) {
            if (Datatype.filterPerType(type, entry.getMetadata())) {
                int curIdx = (int) ((entry.getTimestamp() - start) / granularity);
                if (curIdx != idx) {
                    result.add(new DateTimeSummary(new java.sql.Time(cur * 1000), temp));
                    cur = entry.getTimestamp() - (entry.getTimestamp() % granularity);
                    idx = curIdx;
                    temp = new ArrayList<>();
                }
                temp.add(entry);
            }
        }
        if (!temp.isEmpty()) {
            result.add(new DateTimeSummary(new java.sql.Time(cur * 1000), temp));
        }
        return result;
    }

    public static Map<Datatype, List<Entry>> splitByDatype(List<Entry> entries) {
        HashMap<Datatype, List<Entry>> dataMap = new HashMap<>();
        for (Entry entry : entries) {
            Datatype type = Datatype.valueOf(entry.getMetadata());
            if (!dataMap.containsKey(type))
                dataMap.put(type, new ArrayList<Entry>());
            dataMap.get(type).add(entry);
        }
        return dataMap;
    }


}
