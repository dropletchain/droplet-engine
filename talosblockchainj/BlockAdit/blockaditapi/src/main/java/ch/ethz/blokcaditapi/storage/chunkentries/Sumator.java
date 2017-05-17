package ch.ethz.blokcaditapi.storage.chunkentries;

/**
 * Created by lubums on 17.05.17.
 */

public class Sumator implements EntryProcessor {
    private double[] tempResult;

    public Sumator(int numResults) {
        assert numResults>0;
        tempResult = new double[numResults];
    }


    @Override
    public double[] getResult() {
        double[] result = new double[tempResult.length];
        for (int iter=0; iter<result.length; iter++) {
            result[iter] = tempResult[iter];
        }
        return result;
    }

    @Override
    public void process(DoubleEntry doubleEntry) {
        tempResult[0] += doubleEntry.getDataValue();
    }

    @Override
    public void process(MultiDoubleEntry doubleEntry) {
        double[] values = doubleEntry.getDataValues();
        for (int i=0; i<tempResult.length && i<values.length; i++) {
            tempResult[i] += values[i];
        }
    }

    @Override
    public void process(IntegerEntry intEEntry) {
        tempResult[0] += intEEntry.getDataValue();
    }
}
