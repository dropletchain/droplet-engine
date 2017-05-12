package ch.ethz.blokcaditapi.storage;

import com.google.common.base.Charsets;
import com.google.common.io.CharStreams;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

import ch.ethz.blokcaditapi.policy.PolicyClientException;

/**
 * Created by lukas on 12.05.17.
 */

public class BlockAditDHTStorageClient {

    private String ip;
    private int port;

    private static class ResultObject {
        public ResultObject(int code, String message) {
            this.code = code;
            this.message = message;
        }
        public int code;
        public String message;
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

    public static ResultObject getRequest(String urlStr) throws IOException, PolicyClientException {
        URL url = new URL(urlStr);
        HttpURLConnection c = (HttpURLConnection) url.openConnection();
        c.setRequestMethod("GET");
        String result = null;
        int code = -1;
        try (InputStreamReader reader = new InputStreamReader(new BufferedInputStream(c.getInputStream()), Charsets.UTF_8)) {
            code = c.getResponseCode();
            result = CharStreams.toString(reader);
        } finally {
            c.disconnect();
        }
        return new ResultObject(code, result);

    }

    protected ResultObject fetchAddress(String chunkKeyHex) throws IOException, PolicyClientException {
        String url = String.format("http://%s:%d/chunk_address/%s", ip, port, chunkKeyHex);
        return getRequest(url);
    }

    protected ResultObject getNoncePeer(String ip, int port) throws IOException, PolicyClientException {
        String url = String.format("http://%s:%d/get_chunk", ip, port);
        return getRequest(url);
    }

    public boolean storeChunk(CloudChunk chunk) throws IOException, PolicyClientException {
        String url = String.format("http://%s:%d/store_chunk", ip, port);
        ResultObject obj =  performStoreRequest(url, chunk.encode());
        if (obj.code == 200)
            return true;
        else
            throw new ChunkExcpetion("Error: " + obj.message);
    }

}
