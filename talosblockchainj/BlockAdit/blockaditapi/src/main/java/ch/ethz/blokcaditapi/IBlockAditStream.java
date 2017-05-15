package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Address;

import java.io.File;
import java.util.List;

import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;

/**
 * Created by lukas on 12.05.17.
 */

interface IBlockAditStream {

    Address getOwner();

    int getStreamId();

    List<Address> getShares() throws PolicyClientException;

    boolean appendToStream(Entry entry) throws BlockAditStreamException;

    void flushWriteChunk() throws BlockAditStreamException;

    List<Entry> getRange(long from, long to) throws BlockAditStreamException;

    Entry getEntry(long timestamp, String metadata) throws BlockAditStreamException;

    void presistToFile(File file);

    boolean isApproved() throws PolicyClientException;

    IBlockAditStreamPolicy getPolicyManipulator();


}
