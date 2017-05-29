package ch.ethz.blokcaditapi.storage.chunkentries;

/**
 * Created by lubums on 17.05.17.
 */

public class Averagor implements EntryProcessor {

    private int count = 0;
    private double[] tempResult;

    public Averagor(int numResults) {
        assert numResults > 0;
        tempResult = new double[numResults];
    }

    @Override
    public double[] getResult() {
        double[] result = new double[tempResult.length];
        for (int iter = 0; iter < result.length; iter++) {
            result[iter] = tempResult[iter] / count;
        }
        return result;
    }

    @Override
    public void process(DoubleEntry doubleEntry) {
        count++;
        tempResult[0] += doubleEntry.getDataValue();
    }

    @Override
    public void process(MultiDoubleEntry doubleEntry) {
        count++;
        double[] values = doubleEntry.getDataValues();
        for (int i = 0; i < tempResult.length && i < values.length; i++) {
            tempResult[i] += values[i];
        }
    }

    @Override
    public void process(IntegerEntry intEEntry) {
        count++;
        tempResult[0] += intEEntry.getDataValue();
    }
}
