package ch.ethz.blokcaditapi.storage.chunkentries;

/**
 * Created by lukas on 09.05.17.
 */

public interface EntryDecoder {

    public Entry decode(byte[] entryBytes);


}
