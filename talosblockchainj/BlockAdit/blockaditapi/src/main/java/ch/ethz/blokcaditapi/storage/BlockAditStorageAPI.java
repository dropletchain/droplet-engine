package ch.ethz.blokcaditapi.storage;

import org.bitcoinj.core.ECKey;

import java.io.IOException;

import ch.ethz.blokcaditapi.policy.PolicyClientException;

/**
 * Created by lukas on 15.05.17.
 */

public interface BlockAditStorageAPI {
    boolean storeChunk(CloudChunk chunk) throws IOException, PolicyClientException;

    CloudChunk getChunk(ECKey identityKey, int blockId, StreamIdentifier identifier)
            throws IOException, PolicyClientException, BlockAditStorageAPIException;

    CloudChunk[] getRangeChunks(ECKey identityKey, int[] blockIds, StreamIdentifier identifier, int numThreads);

    CloudChunk[] getRangeChunks(ECKey identityKey, int fromId, int toId,
                                StreamIdentifier identifier, int numThreads);
}
