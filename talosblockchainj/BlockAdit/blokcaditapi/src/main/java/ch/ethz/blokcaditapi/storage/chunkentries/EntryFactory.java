package ch.ethz.blokcaditapi.storage.chunkentries;

import java.util.HashMap;
import java.util.Map;

/**
 * Created by lukas on 09.05.17.
 */

public class EntryFactory {

    public static final int TYPE_DOUBLE_ENTRY = 0;

    public static Map<Integer, EntryDecoder> decodersMap = new HashMap<>();

    static {
        decodersMap.put(TYPE_DOUBLE_ENTRY, new DoubleEntry.DoubleEntryDecoder());
    }

    public static EntryDecoder getDecoderForType(int type) {
        return decodersMap.get(type);
    }



}
