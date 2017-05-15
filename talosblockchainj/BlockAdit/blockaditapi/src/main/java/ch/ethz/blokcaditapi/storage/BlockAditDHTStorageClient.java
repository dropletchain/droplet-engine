package ch.ethz.blokcaditapi.storage;

import com.google.common.base.Charsets;
import com.google.common.io.ByteStreams;
import com.google.common.io.CharStreams;

import org.bitcoinj.core.ECKey;
import org.json.JSONException;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;

import ch.ethz.blokcaditapi.policy.PolicyClientException;

/**
 * Created by lukas on 12.05.17.
 */

public class BlockAditDHTStorageClient {

    private String ip;
    private int port;

    public BlockAditDHTStorageClient(String ip, int port) {
        this.ip = ip;
        this.port = port;
    }

    private static class ResultObject {
        public ResultObject(int code, String message) {
            this.code = code;
            this.message = message;
        }
        public int code;
        public String message;
    }

    private static class ByteResultObject {
        public ByteResultObject(int code, byte[] message) {
            this.code = code;
            this.message = message;
        }
        public int code;
        public byte[] message;
    }

    private static ResultObject performStoreRequest(String urlStr, byte[] data) throws IOException, PolicyClientException {
        URL url = new URL(urlStr);
        String result = null;
        HttpURLConnection urlConnection = (HttpURLConnection) url.openConnection();
        int ok = -1;
        try {
            urlConnection.setRequestMethod("POST");
            urlConnection.setDoInput(true);
            urlConnection.setDoOutput(true);
            urlConnection.setChunkedStreamingMode(0);
            urlConnection.setConnectTimeout(5000);

            OutputStream out = new BufferedOutputStream(urlConnection.getOutputStream());
            out.write(data);
            out.flush();
            out.close();

            ok = urlConnection.getResponseCode();
            try (InputStreamReader reader = new InputStreamReader(new BufferedInputStream(urlConnection.getInputStream()), Charsets.UTF_8)){
                result = CharStreams.toString(reader);

            }
        } finally {
            urlConnection.disconnect();
        }
        return new ResultObject(ok, result);
    }

    private static ByteResultObject performChunkRequest(String urlStr, byte[] token) throws IOException, PolicyClientException {
        URL url = new URL(urlStr);
        byte[] result = null;
        HttpURLConnection urlConnection = (HttpURLConnection) url.openConnection();
        int ok = -1;
        try {
            urlConnection.setRequestMethod("POST");
            urlConnection.setDoInput(true);
            urlConnection.setDoOutput(true);
            urlConnection.setChunkedStreamingMode(0);
            urlConnection.setConnectTimeout(5000);


            OutputStream out = new BufferedOutputStream(urlConnection.getOutputStream());
            out.write(token);
            out.flush();
            out.close();

            ok = urlConnection.getResponseCode();
            try (BufferedInputStream reader = new BufferedInputStream(urlConnection.getInputStream())){
                result = ByteStreams.toByteArray(reader);

            }
        } finally {
            urlConnection.disconnect();
        }
        return new ByteResultObject(ok, result);
    }

    public static ByteResultObject getRequest(String urlStr) throws IOException, PolicyClientException {
        URL url = new URL(urlStr);
        HttpURLConnection c = (HttpURLConnection) url.openConnection();
        c.setRequestMethod("GET");
        c.setConnectTimeout(5000);
        byte[] result = null;
        int code = -1;
        try (BufferedInputStream reader = new BufferedInputStream(c.getInputStream())) {
            code = c.getResponseCode();
            result = ByteStreams.toByteArray(reader);
        } finally {
            c.disconnect();
        }
        return new ByteResultObject(code, result);

    }

    protected ByteResultObject fetchAddress(String chunkKeyHex) throws IOException, PolicyClientException {
        String url = String.format("http://%s:%d/chunk_address/%s", ip, port, chunkKeyHex);
        return getRequest(url);
    }

    protected ByteResultObject getNoncePeer(String ip, int port) throws IOException, PolicyClientException {
        String url = String.format("http://%s:%d/get_chunk", ip, port);
        return getRequest(url);
    }

    protected ByteResultObject getChunkPeer(String ip, int port, QueryToken token)
            throws IOException, PolicyClientException {
        String url = String.format("http://%s:%d/get_chunk", ip, port);
        try {
            return performChunkRequest(url, token.toJSON().getBytes());
        } catch (JSONException e) {
            throw new IOException(e.getCause());
        }
    }

    public boolean storeChunk(CloudChunk chunk) throws IOException, PolicyClientException {
        String url = String.format("http://%s:%d/store_chunk", ip, port);
        ResultObject obj =  performStoreRequest(url, chunk.encode());
        if (obj.code == 200)
            return true;
        else
            throw new ChunkExcpetion("Error: " + obj.message);
    }


    public CloudChunk getChunk(ECKey identityKey, int blockId, StreamIdentifier identifier)
            throws IOException, PolicyClientException, BlockAditStorageAPIException {
        ByteResultObject result;

        result = fetchAddress(Util.bytesToHexString(identifier.getKeyForBlockId(blockId)));

        String addresses = new String(result.message, "UTF-8");

        if (result.code != 200)
            throw new BlockAditStorageAPIException("Fetch address failed");

        String[] tragetNode = addresses.split(":");
        if (tragetNode.length != 2)
            throw new BlockAditStorageAPIException("Received invalid address " + addresses);

        String targetIp = tragetNode[0];
        int targetPort = Integer.valueOf(tragetNode[1]);

        result = getNoncePeer(targetIp, targetPort);

        if (result.code != 200)
            throw new BlockAditStorageAPIException("Fetch nonce peer failed");

        byte[] nonce = result.message;
        QueryToken token = QueryToken.createQueryToken(identifier.getOwner(),
                identifier.getStreamId(), nonce, identifier.getKeyForBlockId(blockId), identityKey);

        ByteResultObject resultChunk = getChunkPeer(targetIp, targetPort, token);

        if (result.code != 200)
            throw new BlockAditStorageAPIException("Fetch chunk peer failed");

        return CloudChunk.createCloudChunkFromByteString(resultChunk.message);
    }

    private static class FetchTask implements Runnable {

        BlockAditDHTStorageClient client;
        int myID;
        CloudChunk[] results;
        ECKey identityKey;
        int blockId;
        StreamIdentifier identifier;
        Semaphore terminator;

        FetchTask(BlockAditDHTStorageClient client, int myID, CloudChunk[] results, Semaphore terminator, ECKey identityKey, int blockId, StreamIdentifier identifier) {
            this.myID = myID;
            this.results = results;
            this.identityKey = identityKey;
            this.blockId = blockId;
            this.identifier = identifier;
            this.terminator = terminator;
            this.client = client;
        }

        @Override
        public void run() {
            try {
                results[myID] = client.getChunk(identityKey, blockId, identifier);
            } catch (Exception e) {
                e.printStackTrace();
                results[myID] = null;
            } finally {
                terminator.release();
            }
        }
    }

    public CloudChunk[] getRangeChunks(ECKey identityKey, int[] blockIds, StreamIdentifier identifier, int numThreads) {
        CloudChunk[] results = new CloudChunk[blockIds.length];
        Semaphore sem = new Semaphore(-blockIds.length + 1);
        ExecutorService pool = Executors.newFixedThreadPool(numThreads);
        try {
            int idx = 0;
            for (int blockId : blockIds) {
                pool.execute(new FetchTask(this, idx, results, sem, identityKey, blockId, identifier));
                idx ++;
            }
            sem.acquire();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            pool.shutdown();
        }
        return results;
    }

    public CloudChunk[] getRangeChunks(ECKey identityKey, int fromId, int toId,
                                       StreamIdentifier identifier, int numThreads) {
        int[] listIdx = new int[toId-fromId];
        for(int i=fromId; i<toId; i++) {
            listIdx[i-fromId] = i;
        }
        return getRangeChunks(identityKey, listIdx, identifier, numThreads);
    }

}
