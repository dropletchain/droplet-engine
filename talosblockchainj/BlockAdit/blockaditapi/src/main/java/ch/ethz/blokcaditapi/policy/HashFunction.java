package ch.ethz.blokcaditapi.policy;

/**
 * Created by lukas on 30.05.17.
 */

public interface HashFunction {

    byte[] hashBytes(byte[] bytes);

}
