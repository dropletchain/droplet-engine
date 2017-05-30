package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;

import java.io.File;
import java.util.List;

import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.storage.ChunkData;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;

/**
 * Represents a data stream in the system.
 */

public interface IBlockAditStream {

    /**
     * Returns the owner of this stream
     * @return the owner address
     */
    Address getOwner();

    /**
     * Returns the stream identifier of this stream.
     * @return the stream id
     */
    int getStreamId();

    /**
     * Returns the address of the users that this stream is shared with.
     * @return a list of shared addresses
     * @throws PolicyClientException
     */
    List<Address> getShares() throws PolicyClientException;

    /**
     * Returns the address of the users that this stream is shared with using the local
     * copy of the policy (may differ from the actual valid policy)
     * @return a list of shared addresses
     * @throws PolicyClientException
     */
    public List<Address> getSharesLocal() throws PolicyClientException;

    /**
     * Stores a chunk on this stream. (lowlevel method)
     * @param id the counter of this chunk
     * @param data the chunk data
     * @return true if ok else false
     * @throws BlockAditStreamException
     */
    boolean storeChunk(int id, ChunkData data) throws BlockAditStreamException;

    /**
     * Append a value to this stream.
     * @param entry the value
     * @return true if ok else false
     * @throws BlockAditStreamException
     */
    boolean appendToStream(Entry entry) throws BlockAditStreamException;

    /**
     * Append multiple values to this stream.
     * @param entries a list of values
     * @return  true if ok else false
     * @throws BlockAditStreamException
     */
    boolean appendToStream(List<Entry> entries) throws BlockAditStreamException;

    /**
     * Flush the current appending chunk to the storage layer.
     * @throws BlockAditStreamException
     */
    void flushWriteChunk() throws BlockAditStreamException;

    /**
     * Given a range interval, returns the stream values in this interval.
     * @param from unix time stamp start interval (inclusive)
     * @param to unix time stamp end interval (exclusive)
     * @return a list of values
     * @throws BlockAditStreamException
     */
    List<Entry> getRange(long from, long to) throws BlockAditStreamException;

    /**
     * Given a range interval, returns the stream values in this interval partitioned per chunk.
     * @param from unix time stamp start interval (inclusive)
     * @param to unix time stamp end interval (exclusive)
     * @return A list partitioned list of values per chunk
     * @throws BlockAditStreamException
     */
    List<List<Entry>> getRangeChunked(long from, long to) throws BlockAditStreamException;

    /**
     * Given a block counter, returns the values of this block.
     * @param blockId the chunk counter
     * @return list of entries.
     * @throws BlockAditStreamException
     */
    List<Entry> getEntriesForBlock(int blockId) throws BlockAditStreamException;

    /**
     * Fetches the value with the given timestamp and the given metadata.
     * (slow full chunk has to be fetched)
     * @param timestamp the timestamo
     * @param metadata the metadata
     * @return the value else null
     * @throws BlockAditStreamException
     */
    Entry getEntry(long timestamp, String metadata) throws BlockAditStreamException;

    /**
     * Store relevat stream information to file.
     * @param file
     */
    void presistToFile(File file);

    /**
     * Check if this stream is approved in the blockain (i.e. creation transaction is in the chain)
     * @return true if this stream is approved else false
     * @throws PolicyClientException
     */
    boolean isApproved() throws PolicyClientException;

    /**
     * Check if this stream was created but not approved yet.
     * @return true if temporary else false
     */
    boolean isTemporary();

    /**
     * Returns a policy manipulator for the policy of this stream.
     * @return a policy manipulator.
     */
    IBlockAditStreamPolicy getPolicyManipulator();

    /**
     * Returns the serialized symmetric key of this stream.
     * @return
     */
    byte[] getSerializedKey();

    /**
     * Returns the start unix timestamp of this stream,
     * @return the start unix timestamp
     */
    public long getStartTimestamp();

    /**
     * Returns the chunk interval (in seconds) of this stream.
     * @return the chunk interval in seconds
     */
    public long getInterval();


}
