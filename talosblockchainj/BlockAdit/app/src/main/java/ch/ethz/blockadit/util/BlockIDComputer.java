package ch.ethz.blockadit.util;

import java.sql.Date;

/**
 * Created by lukas on 16.05.17.
 */

public class BlockIDComputer {

    private long from;
    private long interval;

    public BlockIDComputer() {
    }

    public BlockIDComputer(long from, long interval) {
        this.from = from;
        this.interval = interval;
    }

    private int computeBlockID(long time) {
        return (int) ((time - from) / interval);
    }

    public long dateToUnix(java.util.Date date) {
        return date.getTime() / 1000;
    }

    public int getIdForDate(Date date) {
        long time = dateToUnix(date);
        return computeBlockID(time);
    }

    public int getIdForDate(java.util.Date date) {
        long time = dateToUnix(date);
        return computeBlockID(time);
    }



}
