package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;

import java.io.File;
import java.util.List;

import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.storage.ChunkData;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;

/**
 * Created by lukas on 12.05.17.
 */

public interface IBlockAditStream {

    Address getOwner();

    int getStreamId();

    List<Address> getShares() throws PolicyClientException;

    public List<Address> getSharesLocal() throws PolicyClientException;

    boolean storeChunk(int id, ChunkData data) throws BlockAditStreamException;

    boolean appendToStream(Entry entry) throws BlockAditStreamException;

    boolean appendToStream(List<Entry> entries) throws BlockAditStreamException;

    void flushWriteChunk() throws BlockAditStreamException;

    List<Entry> getRange(long from, long to) throws BlockAditStreamException;

    List<List<Entry>> getRangeChunked(long from, long to) throws BlockAditStreamException;

    List<Entry> getEntriesForBlock(int blockId) throws BlockAditStreamException;

    Entry getEntry(long timestamp, String metadata) throws BlockAditStreamException;

    void presistToFile(File file);

    boolean isApproved() throws PolicyClientException;

    boolean isTemporary();

    IBlockAditStreamPolicy getPolicyManipulator();

    byte[] getSerializedKey();

    public long getStartTimestamp();

    public long getInterval();


}
