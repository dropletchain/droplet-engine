package ch.ethz.blokcaditapi.storage.chunkentries;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import static ch.ethz.blokcaditapi.storage.chunkentries.EntryFactory.TYPE_INT_ENTRY;

/**
 * Created by lubums on 17.05.17.
 */

public class IntegerEntry implements Entry {
    private final long timestamp;
    private final String metadata;
    private final int dataValue;

    public IntegerEntry(long timestamp, String metadata, int dataValue) {
        this.timestamp = timestamp;
        this.metadata = metadata;
        this.dataValue = dataValue;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public String getMetadata() {
        return metadata;
    }

    public int getDataValue() {
        return dataValue;
    }

    @Override
    public byte[] encode() {
        int len = this.getEncodedSize();
        ByteBuffer buffer = ByteBuffer.allocate(len);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        buffer.putInt(len)
                .put((byte) this.getType())
                .putLong(this.timestamp)
                .put(this.metadata.getBytes())
                .putInt(this.dataValue);
        return buffer.array();
    }

    @Override
    public int getEncodedSize() {
        return Long.SIZE/8 + Integer.SIZE/8 + metadata.getBytes().length + Integer.SIZE/8 + 1;
    }

    @Override
    public int getType() {
        return TYPE_INT_ENTRY;
    }

    @Override
    public void accept(EntryProcessor processor) {
        processor.process(this);
    }

    public static class IntegerEntryDecoder implements EntryDecoder {

        private Entry decodeLocal(ByteBuffer buffer) {
            int lenMeta;
            buffer.order(ByteOrder.LITTLE_ENDIAN);
            int len = buffer.getInt();
            buffer.get();
            long timestamp = buffer.getLong();
            lenMeta = len - Long.SIZE / 8 - Integer.SIZE / 8 - Integer.SIZE / 8 - 1;
            byte[] metaDataBytes = new byte[lenMeta];
            buffer.get(metaDataBytes);
            int value = buffer.getInt();
            return new IntegerEntry(timestamp, new String(metaDataBytes), value);
        }

        @Override
        public Entry decode(byte[] entryBytes) {
            ByteBuffer buffer = ByteBuffer.wrap(entryBytes);
            return decodeLocal(buffer);
        }

        @Override
        public Entry decode(byte[] entryBytes, int offset, int len) {
            ByteBuffer buffer = ByteBuffer.wrap(entryBytes, offset, len);
            return decodeLocal(buffer);
        }
    }
}
