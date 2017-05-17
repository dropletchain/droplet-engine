package ch.ethz.blokcaditapi.storage.chunkentries;

/**
 * Created by lubums on 17.05.17.
 */

public interface EntryProcessor {

    public double[] getResult();

    public void process(DoubleEntry doubleEntry);

    public void process(MultiDoubleEntry doubleEntry);

    public void process(IntegerEntry doubleEntry);

}
