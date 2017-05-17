package ch.ethz.blokcaditapi.storage.chunkentries;

/**
 * Created by lukas on 09.05.17.
 */

public interface Entry {

    public long getTimestamp();

    public String getMetadata();

    public byte[] encode();

    public int getEncodedSize();

    public int getType();

    public void accept(EntryProcessor processor);
}
