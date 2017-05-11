package ch.ethz.blokcaditapi.policy;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.spongycastle.util.encoders.Base64;

import java.util.ArrayList;
import java.util.List;

/**
 * Created by lukas on 09.05.17.
 */

public class Policy {

    public static final String OPCODE_FIELD_STREAM_ID = "streamid";
    public static final String OPCODE_FIELD_TIMESTAMP_START = "ts_start";
    public static final String OPCODE_FIELD_INTERVAL = "ts_interval";
    public static final String OPCODE_FIELD_NONCE = "nonce";
    public static final String OPCODE_FIELD_OWNER = "owner";
    public static final String OPCODE_FIELD_OWNER_PK = "owner_pk";
    public static final String OPCODE_FIELD_TXTID = "txid";
    public static final String OPCODE_FIELD_SHARE_ADDR = "pk_addr";


    private String owner;
    private int streamId;
    private String nonce;
    private String createTxid;
    private String ownerPk;
    private List<IndexEntry> times = new ArrayList<>();
    private List<PolicyShare> shares = new ArrayList<>();

    Policy(String owner, int streamId, String nonce, String createTxid, String ownerPk, List<IndexEntry> times, List<PolicyShare> shares) {
        this.owner = owner;
        this.streamId = streamId;
        this.nonce = nonce;
        this.createTxid = createTxid;
        this.ownerPk = ownerPk;
        this.times = times;
        this.shares = shares;
    }

    Policy(String owner, int streamId, String nonce, String createTxid, String ownerPk) {
        this.owner = owner;
        this.streamId = streamId;
        this.nonce = nonce;
        this.createTxid = createTxid;
        this.ownerPk = ownerPk;
    }

    public void addShare(PolicyShare share) {
        this.shares.add(share);
    }

    public void addTimeIndex(IndexEntry entry) {
        this.times.add(entry);
    }

    public String getOwner() {
        return owner;
    }

    public int getStreamId() {
        return streamId;
    }

    public String getNonce() {
        return nonce;
    }

    public byte[] getNonceBin() {
        return Base64.decode(this.getNonce());
    }

    public String getCreateTxid() {
        return createTxid;
    }

    public String getOwnerPk() {
        return ownerPk;
    }

    public List<IndexEntry> getTimes() {
        return times;
    }

    public List<PolicyShare> getShares() {
        return shares;
    }

    public String toJson() {
        JSONObject object = new JSONObject();
        try {
            object.put(OPCODE_FIELD_OWNER, this.owner);
            object.put(OPCODE_FIELD_STREAM_ID, this.streamId);
            object.put(OPCODE_FIELD_NONCE, this.nonce);
            object.put(OPCODE_FIELD_TXTID, this.createTxid);
            object.put(OPCODE_FIELD_OWNER_PK, this.ownerPk);

            JSONArray sharesJSON = new JSONArray();
            for (PolicyShare share : this.shares) {
                sharesJSON.put(share.toJSON());
            }
            object.put("shares", sharesJSON);

            JSONArray timesJSON = new JSONArray();
            for (IndexEntry share : this.times) {
                timesJSON.put(share.toJSON());
            }
            object.put("times", timesJSON);

        } catch (JSONException e) {
            e.printStackTrace();
        }
        return object.toString();
    }

    public static Policy createFromJsonString(String policyString) throws JSONException {
        JSONObject object = new JSONObject(policyString);
        String owner = object.getString(OPCODE_FIELD_OWNER);
        int streamId = object.getInt(OPCODE_FIELD_STREAM_ID);
        String nonce = object.getString(OPCODE_FIELD_NONCE);
        String txid = object.getString(OPCODE_FIELD_TXTID);
        String ownerPk = object.getString(OPCODE_FIELD_OWNER_PK);

        ArrayList<PolicyShare> shares = new ArrayList<>();
        JSONArray sharesArr = object.getJSONArray("shares");
        for (int idx=0; idx < sharesArr.length(); idx ++) {
            shares.add(PolicyShare.fromJSON(sharesArr.getJSONObject(idx)));
        }

        ArrayList<IndexEntry> times = new ArrayList<>();
        JSONArray indexArr = object.getJSONArray("times");
        for (int idx=0; idx < indexArr.length(); idx ++) {
            times.add(IndexEntry.fromJSON(indexArr.getJSONObject(idx)));
        }

        return new Policy(owner, streamId, nonce, txid, ownerPk, times, shares);
    }

    public static class IndexEntry {
        public long timestampStart;
        public long timestampInterval;
        public String txid;

        public IndexEntry(long timestampStart, long timestampInterval, String txid) {
            this.timestampStart = timestampStart;
            this.timestampInterval = timestampInterval;
            this.txid = txid;
        }

        public JSONObject toJSON() {
            JSONObject object = new JSONObject();
            try {
                object.put(OPCODE_FIELD_TIMESTAMP_START, this.timestampStart);
                object.put(OPCODE_FIELD_INTERVAL, this.timestampInterval);
                object.put(OPCODE_FIELD_TXTID, this.txid);
            } catch (JSONException e) {
                e.printStackTrace();
            }
            return object;
        }

        public static IndexEntry fromJSON(JSONObject obj) throws JSONException {
            return new IndexEntry(obj.getLong(OPCODE_FIELD_TIMESTAMP_START),
                    obj.getLong(OPCODE_FIELD_INTERVAL),
                    obj.getString(OPCODE_FIELD_TXTID));
        }
    }

    public static class PolicyShare {
        public String address;
        public String txid;

        public PolicyShare(String address, String txid) {
            this.address = address;
            this.txid = txid;
        }

        public JSONObject toJSON() {
            JSONObject object = new JSONObject();
            try {
                object.put(OPCODE_FIELD_SHARE_ADDR, this.address);
                object.put(OPCODE_FIELD_TXTID, this.txid);
            } catch (JSONException e) {
                e.printStackTrace();
            }
            return object;
        }

        public static PolicyShare fromJSON(JSONObject obj) throws JSONException {
            return new PolicyShare(obj.getString(OPCODE_FIELD_SHARE_ADDR),
                    obj.getString(OPCODE_FIELD_TXTID));
        }
    }
}
