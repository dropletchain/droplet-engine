package ch.ethz.blokcaditapi.storage.chunkentries;

/**
 * Created by lukas on 09.05.17.
 */

public interface Entry {

    public byte[] encode();

    public int getEncodedSize();

    public int getType();

}
