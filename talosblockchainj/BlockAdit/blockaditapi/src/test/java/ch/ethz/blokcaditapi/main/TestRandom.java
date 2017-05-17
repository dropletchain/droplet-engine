package ch.ethz.blokcaditapi.main;

import org.junit.Test;

import java.text.ParseException;
import java.text.SimpleDateFormat;

/**
 * Created by lukas on 17.05.17.
 */

public class TestRandom {

    private java.util.Date transformDates(java.sql.Date date, java.sql.Time time) throws ParseException {
        SimpleDateFormat combinedformat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd");
        SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm:ss");
        return combinedformat.parse(dateFormat.format(date) + " " + timeFormat.format(time));
    }

    @Test
    public void testDates() throws ParseException {
        SimpleDateFormat forma = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm:ss");
        java.util.Date dateUtil = forma.parse("2014-09-05 00:04:00");
        java.sql.Date dateLocal = java.sql.Date.valueOf("2014-09-05");
        java.sql.Date dateLocal2 = java.sql.Date.valueOf("2014-09-06");
        java.sql.Time  date =  java.sql.Time.valueOf("00:04:00");
        java.util.Date temp =  timeFormat.parse("00:04:00");
        java.sql.Time  date2 =  new java.sql.Time(temp.getTime());
        java.sql.Time date3 =  java.sql.Time.valueOf("00:19:00");
        System.out.println(dateUtil.getTime());
        System.out.println(transformDates(dateLocal, date).getTime());

        System.out.println(dateLocal.getTime() / 86400000);
        System.out.println(dateLocal2.getTime() / 86400000);

    }

}
