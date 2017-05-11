package ch.ethz.blokcaditapi.policy;

import com.google.common.base.Charsets;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import com.google.common.io.CharStreams;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;

/**
 * Created by lukas on 09.05.17.
 */

public class PolicyVcApiClient {

    public static final String NO_RESULT_FOUND = "NO RESULT FOUND";
    public static final String GENERAL_ERROR = "ERROR";

    private String ip;
    private int port;
    private int numMinutesCache = 1;

    private LoadingCache<String, Policy> policies = CacheBuilder.newBuilder()
            .expireAfterAccess(numMinutesCache, TimeUnit.MINUTES)
            .build(
                    new CacheLoader<String, Policy>() {
                        public Policy load(String key) throws IOException, JSONException, PolicyClientException { // no checked exception
                            String response = performRequest(key);
                            return Policy.createFromJsonString(response);
                        }
                    });

    public PolicyVcApiClient(String ip, int port) {
        this.ip = ip;
        this.port = port;
    }

    public PolicyVcApiClient(String ip, int port, int numMinutesCache) {
        this.ip = ip;
        this.port = port;
        this.numMinutesCache = numMinutesCache;
    }

    private static String performRequest(String urlStr) throws IOException, PolicyClientException {
        URL url = new URL(urlStr);
        HttpURLConnection c = (HttpURLConnection) url.openConnection();
        c.setRequestMethod("GET");
        String result = null;
        try (InputStreamReader reader = new InputStreamReader(new BufferedInputStream(c.getInputStream()), Charsets.UTF_8)){
            result = CharStreams.toString(reader);
        }
        if (containsError(result))
            throw new PolicyClientException(result);
        return result;
    }

    private static boolean containsError(String msg) {
        return msg.contains(NO_RESULT_FOUND) || msg.contains(GENERAL_ERROR);
    }

    private String getUrl(String args) {
        return String.format("http://%s:%d/%s", this.ip, this.port, args);
    }

    public Policy getPolicy(String owner, int streamId) throws PolicyClientException {
        String args = String.format("policy?owner=%s&stream-id=%d", owner, streamId);
        try {
            return policies.get(this.getUrl(args));
        } catch (ExecutionException e) {
            throw new PolicyClientException(e.getCause());
        }
    }

    public Policy getPolicy(String txid) throws PolicyClientException {
        String args = String.format("policy?txid=%s", txid);
        try {
            return policies.get(this.getUrl(args));
        } catch (ExecutionException e) {
            throw new PolicyClientException(e.getCause());
        }
    }

    public List<String> getPolicyOwners(int limit, int offset) throws PolicyClientException {
        String args = String.format("owners?limit=%d&offset=%d", limit, offset);
        try {
            String result = performRequest(this.getUrl(args));
            JSONObject obj = new JSONObject(result);
            List<String> owners = new ArrayList<>();
            JSONArray array = obj.getJSONArray("owners");
            for (int idx=0; idx<array.length(); idx++) {
                owners.add(array.getString(idx));
            }
            return owners;
        } catch (IOException e) {
            throw new PolicyClientException(e.getCause());
        } catch (JSONException e) {
            throw new PolicyClientException(e.getCause());
        }
    }

    public List<Integer> getStreamIdsForOwner(String owner) throws PolicyClientException {
        String args = String.format("streamids?owner=%s", owner);
        try {
            String result = performRequest(this.getUrl(args));
            JSONObject obj = new JSONObject(result);
            List<Integer> streamIds = new ArrayList<>();
            JSONArray array = obj.getJSONArray("stream-ids");
            for (int idx=0; idx<array.length(); idx++) {
                streamIds.add(array.getInt(idx));
            }
            return streamIds;
        } catch (IOException e) {
            throw new PolicyClientException(e.getCause());
        } catch (JSONException e) {
            throw new PolicyClientException(e.getCause());
        }
    }

}
