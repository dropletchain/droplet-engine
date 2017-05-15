package ch.ethz.blokcaditapi.storage;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import ch.ethz.blokcaditapi.storage.chunkentries.Entry;
import ch.ethz.blokcaditapi.storage.chunkentries.EntryDecoder;
import ch.ethz.blokcaditapi.storage.chunkentries.EntryFactory;

/**
 * Created by lukas on 08.05.17.
 */

public class ChunkData implements Iterable<Entry> {

    private List<Entry> entries = new ArrayList<>();
    private int maxEntries;

    public ChunkData() {
        this.maxEntries = Integer.MAX_VALUE;
    }

    public ChunkData(List<Entry> entries) {
        this.entries = entries;
        this.maxEntries = Integer.MAX_VALUE;
    }

    public ChunkData(List<Entry> entries, int maxEntries) {
        this.entries = entries;
        this.maxEntries = maxEntries;
    }

    public ChunkData(int maxEntries) {
        this.maxEntries = maxEntries;
    }

    public boolean addEntry(Entry entry) {
        if (maxEntries <= entries.size())
            return false;
        this.entries.add(entry);
        return true;
    }

    public List<Entry> getEntries() {
        return entries;
    }

    public int remainingSpace() {
        return this.maxEntries - entries.size();
    }

    public static ChunkData decodeFromByteString(byte[] chunkData) {
        //Assumes: |len_entry (4 byte)| type | encoded entry|
        List<Entry> entries = new ArrayList<>();
        int curPosition = 0;
        while (curPosition < chunkData.length) {
            ByteBuffer buff = ByteBuffer.wrap(chunkData, curPosition, 5);
            buff.order(ByteOrder.LITTLE_ENDIAN);
            int totalLen = buff.getInt();
            int type = (int) buff.get();

            EntryDecoder decoder = EntryFactory.getDecoderForType(type);
            entries.add(decoder.decode(chunkData, curPosition, totalLen));
            curPosition += totalLen;
        }
        return new ChunkData(entries, entries.size());
    }

    public byte[] encode() {
        int numbytes = entries.size() * 32;
        if (!entries.isEmpty()) {
            numbytes = entries.get(0).encode().length * entries.size();
        }
        ByteArrayOutputStream bufferStream = new ByteArrayOutputStream(numbytes);
        for (Entry entry : this.entries) {
            byte[] encoded = entry.encode();
            bufferStream.write(encoded, 0, encoded.length);
        }
        return bufferStream.toByteArray();
    }

    @Override
    public Iterator iterator() {
        return entries.iterator();
    }
}
