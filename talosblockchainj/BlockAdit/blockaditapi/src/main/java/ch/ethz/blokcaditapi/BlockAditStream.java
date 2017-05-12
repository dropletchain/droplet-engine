package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

import ch.ethz.blokcaditapi.policy.Policy;
import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.policy.StreamKey;
import ch.ethz.blokcaditapi.storage.ChunkData;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;

/**
 * Created by lukas on 12.05.17.
 */

public class BlockAditStream implements IBlockAditStream {

    private StreamKey streamKey;
    private IBlockAditStreamPolicy policyForStream;
    private List<ChunkData> toSend = new ArrayList<>();
    private  ChunkData curWriteChunk;
    private int currentBlockID = -1;

    private long startTimestamp;
    private long interval;

    public BlockAditStream(StreamKey streamKey, IBlockAditStreamPolicy policyForStream) throws BlockAditStreamException {
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
    }

    private long calulateBlockId(long timestamp) {
        return (timestamp - startTimestamp) / interval;
    }

    @Override
    public Address getOwner() {
        return this.streamKey.getSignAddress();
    }

    @Override
    public int getStreamId() {
        return this.streamKey.getStreamId();
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
    public boolean appendToStream(Entry entry) throws BlockAditStreamException {
        int entryId = (int) calulateBlockId(entry.getTimestamp());
        if(currentBlockID == -1) {
            currentBlockID = entryId;
        } else if (currentBlockID == entryId)  {
            curWriteChunk.addEntry(entry);
        } else if (currentBlockID + 1 == entryId) {
            toSend.add(curWriteChunk);
            curWriteChunk = new ChunkData();
            curWriteChunk.addEntry(entry);
            //TODO: Start send job
        } else {
            throw new BlockAditStreamException("Entry is not append");
        }
        return true;
    }

    @Override
    public void flushWriteChunk() {
        toSend.add(curWriteChunk);
        curWriteChunk = new ChunkData();
        //TODO: Start send job
    }

    @Override
    public List<Entry> getRange(long from, long to) {
        return null;
    }

    @Override
    public Entry getEntry(long timestamp, String metadata) {
        return null;
    }

    @Override
    public void presistToFile(File file) {

    }

    @Override
    public boolean isApproved() {
        return false;
    }

    @Override
    public IBlockAditStreamPolicy getPolicyManipulator() {
        return null;
    }

    public static BlockAditStream fromFile(File file, KeyManager manager) {
        return null;
    }
}
