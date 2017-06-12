package ch.ethz.blokcaditapi.storage.chunkentries;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import static ch.ethz.blokcaditapi.storage.chunkentries.EntryFactory.TYPE_PICTURE_ENTRY;

/**
 * Created by lubums on 12.06.17.
 */

public class PictureEntry implements Entry {

    private final long timestamp;
    private final String metadata;
    private final byte[] pictureData;

    public PictureEntry(long timestamp, String metadata, byte[] pictureData) {
        this.timestamp = timestamp;
        this.metadata = metadata;
        this.pictureData = pictureData;
    }

    @Override
    public long getTimestamp() {
        return timestamp;
    }

    @Override
    public String getMetadata() {
        return metadata;
    }

    public byte[] getPictureData() {
        return this.pictureData;
    }

    @Override
    public byte[] encode() {
        int len = this.getEncodedSize();
        ByteBuffer buffer = ByteBuffer.allocate(len);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        buffer.putInt(len)
                .put((byte) this.getType())
                .putLong(this.timestamp)
                .putInt(this.metadata.getBytes().length)
                .put(this.metadata.getBytes())
                .put(this.getPictureData());
        return buffer.array();
    }

    @Override
    public int getEncodedSize() {
        return Long.SIZE / 8 + (Integer.SIZE / 8) * 2 + metadata.getBytes().length + pictureData.length + 1;
    }

    @Override
    public int getType() {
        return TYPE_PICTURE_ENTRY;
    }

    @Override
    public void accept(EntryProcessor processor) {
        processor.process(this);
    }

    public static class PictureEntryDecoder implements EntryDecoder {

        private Entry decodeLocal(ByteBuffer buffer) {
            int lenMeta, lenPicture;
            buffer.order(ByteOrder.LITTLE_ENDIAN);
            int len = buffer.getInt();
            buffer.get();
            long timestamp = buffer.getLong();
            lenMeta = buffer.getInt();
            byte[] metaDataBytes = new byte[lenMeta];
            buffer.get(metaDataBytes);
            lenPicture = len - (Long.SIZE / 8 + (Integer.SIZE / 8) * 2 + metaDataBytes.length + 1);
            byte[] pictureData = new byte[lenPicture];
            buffer.get(pictureData);
            return new PictureEntry(timestamp, new String(metaDataBytes), pictureData);
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
