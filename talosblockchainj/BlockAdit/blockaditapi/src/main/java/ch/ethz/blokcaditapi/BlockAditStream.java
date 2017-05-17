package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;

import java.io.File;
import java.io.IOException;
import java.security.InvalidKeyException;
import java.util.ArrayList;
import java.util.List;

import ch.ethz.blokcaditapi.policy.Policy;
import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.policy.StreamKey;
import ch.ethz.blokcaditapi.storage.BlockAditStorageAPI;
import ch.ethz.blokcaditapi.storage.BlockAditStorageAPIException;
import ch.ethz.blokcaditapi.storage.ChunkData;
import ch.ethz.blokcaditapi.storage.CloudChunk;
import ch.ethz.blokcaditapi.storage.StreamIdentifier;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;

/**
 * Created by lukas on 12.05.17.
 */

public class BlockAditStream implements IBlockAditStream {

    private static final int MAX_NUM_THREADS = 4;

    private static class ChunkJobStoreJob {
        int blockId;
        ChunkData data;

        public ChunkJobStoreJob(int blockId, ChunkData data) {
            this.blockId = blockId;
            this.data = data;
        }
    }

    private StreamKey streamKey;
    private StreamIdentifier identifier;

    private boolean isWriteable = false;

    private IBlockAditStreamPolicy policyForStream;
    private List<ChunkJobStoreJob> toSend = new ArrayList<>();
    private  ChunkData curWriteChunk;
    private int currentBlockID = -1;
    private BlockAditStorageAPI storageAPI;

    private long startTimestamp;
    private long interval;

    public BlockAditStream(BlockAditStorageAPI storageAPI, StreamKey streamKey, IBlockAditStreamPolicy policyForStream) throws BlockAditStreamException {
        this.storageAPI = storageAPI;
        this.streamKey = streamKey;
        this.policyForStream = policyForStream;
        Policy policy = policyForStream.getLocalPolicy();
        if(policy == null)
            throw new BlockAditStreamException("No local Policy for the stream");
        //hack
        Policy.IndexEntry entry = policy.getTimes().get(policy.getTimes().size() - 1);
        startTimestamp = entry.timestampStart;
        interval = entry.timestampInterval;
        curWriteChunk = new ChunkData();
        identifier = policyForStream.getLocalPolicy().getStreamidentifier();
        isWriteable = identifier.getOwner().equals(streamKey.getSignAddress().toString());
    }

    private long calulateBlockId(long timestamp) {
        return (timestamp - startTimestamp) / interval;
    }

    private void pushChunksToCloud() throws PolicyClientException, InvalidKeyException, IOException {
        Policy curPolicy = policyForStream.getActualPolicy();
        for (ChunkJobStoreJob job: toSend) {
            CloudChunk chunk = CloudChunk.createCloudChunk(curPolicy.getStreamidentifier(), job.blockId,
                    streamKey.getSignKey(), streamKey.getCurVersion(),
                    streamKey.getCurSymKey(), job.data, true);
            this.storageAPI.storeChunk(chunk);
        }
    }

    @Override
    public Address getOwner() {
        return this.streamKey.getSignAddress();
    }

    @Override
    public int getStreamId() {
        return this.identifier.getStreamId();
    }

    @Override
    public List<Address> getShares() throws PolicyClientException {
        Policy curPolicy = policyForStream.getActualPolicy();
        List<Address> addresses = new ArrayList<>();
        for (Policy.PolicyShare share : curPolicy.getShares()) {
            addresses.add(Address.fromBase58(policyForStream.getNeworkParams(), share.address));
        }
        return addresses;
    }

    @Override
    public boolean storeChunk(int id, ChunkData data) throws BlockAditStreamException {
        this.toSend.add(new ChunkJobStoreJob(id, data));
        try {
            pushChunksToCloud();
        } catch (PolicyClientException | InvalidKeyException | IOException e) {
            throw new BlockAditStreamException(e.getCause());
        }
        return true;
    }

    @Override
    public boolean appendToStream(Entry entry) throws BlockAditStreamException {
        if (!isWriteable)
            throw new BlockAditStreamException("Stream is not writable");
        int entryId = (int) calulateBlockId(entry.getTimestamp());
        if(currentBlockID == -1) {
            currentBlockID = entryId;
            curWriteChunk.addEntry(entry);
        } else if (currentBlockID == entryId)  {
            curWriteChunk.addEntry(entry);
        } else if (currentBlockID + 1 == entryId) {
            toSend.add(new ChunkJobStoreJob(currentBlockID, curWriteChunk));
            curWriteChunk = new ChunkData();
            currentBlockID ++;
            curWriteChunk.addEntry(entry);

            try {
                pushChunksToCloud();
            } catch (PolicyClientException | InvalidKeyException | IOException e) {
                throw new BlockAditStreamException(e.getCause());
            }
        } else {
            throw new BlockAditStreamException("Entry is not append");
        }
        return true;
    }

    @Override
    public boolean appendToStream(List<Entry> entries) throws BlockAditStreamException {
        for (Entry entry : entries)
            this.appendToStream(entry);
        return true;
    }

    @Override
    public void flushWriteChunk() throws BlockAditStreamException {
        if(!curWriteChunk.getEntries().isEmpty()) {
            toSend.add(new ChunkJobStoreJob(currentBlockID, curWriteChunk));
            curWriteChunk = new ChunkData();
            currentBlockID++;

            try {
                pushChunksToCloud();
            } catch (PolicyClientException | InvalidKeyException | IOException e) {
                throw new BlockAditStreamException(e.getCause());
            }
        }
    }

    private ChunkData dataFromChunk(CloudChunk chunk) {
        try {
            return chunk.retriveData(this.streamKey.getSymKey(chunk.getKeyVersion()), true);
        } catch (InvalidKeyException e) {
            e.printStackTrace();
        }
        return new ChunkData();
    }

    private ChunkData[] dataFromChunks(CloudChunk[] chunks) {
        ChunkData[] data = new ChunkData[chunks.length];
        for (int idx=0; idx<chunks.length; idx ++)
            data[idx] = dataFromChunk(chunks[idx]);
        return data;
    }

    private CloudChunk[] fetchRange(long from, long to) throws BlockAditStreamException {
        int blockIdForm, blockIdTo, len;
        try {
            blockIdForm = (int) calulateBlockId(from);
            blockIdTo = (int) calulateBlockId(to);
            CloudChunk[] chunks;
            if (blockIdForm == blockIdTo) {
                chunks = new CloudChunk[1];
                chunks[0] = this.storageAPI.getChunk(streamKey.getSignKey(), blockIdForm, identifier);
            } else {
                len = blockIdTo - blockIdForm;
                chunks = this.storageAPI.getRangeChunks(streamKey.getSignKey(), blockIdForm,
                        blockIdTo, identifier, len < MAX_NUM_THREADS ? len : MAX_NUM_THREADS);
            }
            return chunks;
        } catch (PolicyClientException | IOException | BlockAditStorageAPIException e) {
            throw new BlockAditStreamException(e.getCause());
        }
    }

    @Override
    public List<Entry> getRange(long from, long to) throws BlockAditStreamException {
        List<Entry> result = new ArrayList<>();
        CloudChunk[] chunks = fetchRange(from, to);
        for (ChunkData data: dataFromChunks(chunks)) {
            for (Entry entry : data) {
                if (entry.getTimestamp() >= from && entry.getTimestamp()< to)
                    result.add(entry);
            }
        }
        return result;
    }

    @Override
    public List<List<Entry>> getRangeChunked(long from, long to) throws BlockAditStreamException {
        List<List<Entry>> result = new ArrayList<>();
        CloudChunk[] chunks = fetchRange(from, to);
        for (ChunkData data: dataFromChunks(chunks)) {
            result.add(data.getEntries());
        }
        return result;
    }

    @Override
    public List<Entry> getEntriesForBlock(int blockId) throws BlockAditStreamException {
        ChunkData data = null;
        try {
            CloudChunk chunk = this.storageAPI.getChunk(streamKey.getSignKey(), blockId, identifier);
            data = dataFromChunk(chunk);
        } catch (IOException | BlockAditStorageAPIException | PolicyClientException e) {
            e.printStackTrace();
            return new ArrayList<>();
        }
        return data.getEntries();
    }

    @Override
    public Entry getEntry(long timestamp, String metadata) throws BlockAditStreamException {
        try {
            int blockId = (int) calulateBlockId(timestamp);
            CloudChunk chunk = this.storageAPI.getChunk(this.streamKey.getSignKey(), blockId, identifier);
        } catch (PolicyClientException | IOException | BlockAditStorageAPIException e) {
            throw new BlockAditStreamException(e.getCause());
        }
        return null;
    }

    @Override
    public void presistToFile(File file) {

    }

    @Override
    public boolean isApproved() throws PolicyClientException {
        return policyForStream.getActualPolicy() != null;
    }

    @Override
    public IBlockAditStreamPolicy getPolicyManipulator() {
        return this.policyForStream;
    }

    @Override
    public byte[] getSerializedKey() {
        return this.streamKey.serialize();
    }

    public long getStartTimestamp() {
        return startTimestamp;
    }

    public long getInterval() {
        return interval;
    }

    public static BlockAditStream fromFile(File file, KeyManager manager) {
        return null;
    }
}
