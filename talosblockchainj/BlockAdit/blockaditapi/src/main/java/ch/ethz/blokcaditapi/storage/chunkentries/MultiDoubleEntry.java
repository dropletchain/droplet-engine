package ch.ethz.blokcaditapi.storage.chunkentries;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import static ch.ethz.blokcaditapi.storage.chunkentries.EntryFactory.TYPE_MULTI_DOUBLE_ENTRY;

/**
 * Created by lukas on 09.05.17.
 */

public class MultiDoubleEntry implements Entry {

    private final long timestamp;
    private final String metadata;
    private final double[] dataValues;

    public MultiDoubleEntry(long timestamp, String metadata, double[] dataValues) {
        this.timestamp = timestamp;
        this.metadata = metadata;
        this.dataValues = dataValues;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public String getMetadata() {
        return metadata;
    }

    public double[] getDataValues() {
        return dataValues;
    }

    @Override
    public byte[] encode() {
        int len = this.getEncodedSize();
        ByteBuffer buffer = ByteBuffer.allocate(len);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        byte[] metaBytes = this.metadata.getBytes();
        buffer.putInt(len)
                .put((byte) this.getType())
                .putLong(this.timestamp)
                .putInt(metaBytes.length)
                .put(metaBytes);
        for (double value : this.dataValues) {
            buffer.putDouble(value);
        }
        return buffer.array();
    }

    @Override
    public int getEncodedSize() {
        return Long.SIZE/8 + (Integer.SIZE/8) * 2 + metadata.getBytes().length +
                (Double.SIZE/8) * dataValues.length + 1;
    }

    @Override
    public int getType() {
        return TYPE_MULTI_DOUBLE_ENTRY;
    }

    public static class MultiDoubleEntryDecoder implements EntryDecoder {

        private Entry decodeLocal(ByteBuffer buffer) {
            int lenMeta;
            buffer.order(ByteOrder.LITTLE_ENDIAN);
            int len = buffer.getInt();
            buffer.get();
            long timestamp = buffer.getLong();
            lenMeta = buffer.getInt();
            byte[] metaDataBytes = new byte[lenMeta];
            buffer.get(metaDataBytes);
            int lenDoubles = len - (Long.SIZE/8 + (Integer.SIZE/8) * 2 + lenMeta + 1);
            int numDoubles = lenDoubles / (Double.SIZE/8);
            double[] dataValues = new double[numDoubles];
            for (int i=0; i < numDoubles; i++) {
                dataValues[i] = buffer.getDouble();
            }
            return new MultiDoubleEntry(timestamp, new String(metaDataBytes), dataValues);
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
