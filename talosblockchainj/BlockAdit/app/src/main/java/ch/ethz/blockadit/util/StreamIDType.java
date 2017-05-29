package ch.ethz.blockadit.util;

import java.util.HashSet;
import java.util.Random;
import java.util.Set;

import ch.ethz.blockadit.blockadit.Datatype;

/**
 * Created by lukas on 19.05.17.
 */

public class StreamIDType {

    private int streamId;
    private boolean[] types = new boolean[5];

    public StreamIDType(int streamId) {
        this.streamId = streamId;
        parseTypes(streamId);
    }

    private static int getBit(int n, int k) {
        return (n >> k) & 1;
    }

    private void parseTypes(int id) {
        for (int i = 4; i >= 0; i--) {
            this.types[4 - i] = getBit(id, i) == 1;
        }
    }

    public boolean hasSteps() {
        return types[0];
    }

    public boolean hasFloor() {
        return types[1];
    }

    public boolean hasDist() {
        return types[2];
    }

    public boolean hasCalories() {
        return types[3];
    }

    public boolean hasHeart() {
        return types[4];
    }

    public static int createId(boolean[] types) {
        assert types.length == 5;
        Random random = new Random(System.currentTimeMillis());
        int res = random.nextInt();
        res = res < 0 ? -res : res;
        res = (res >> 5);
        res = (res << 1) | (types[0] ? 1 : 0);
        res = (res << 1) | (types[1] ? 1 : 0);
        res = (res << 1) | (types[2] ? 1 : 0);
        res = (res << 1) | (types[3] ? 1 : 0);
        res = (res << 1) | (types[4] ? 1 : 0);
        return res;
    }

    public Set<Datatype> getDatatypeSet() {
        Set<Datatype> res = new HashSet<>();
        if (this.hasSteps())
            res.add(Datatype.STEPS);
        if (this.hasFloor())
            res.add(Datatype.FLOORS);
        if (this.hasDist())
            res.add(Datatype.DISTANCE);
        if (this.hasHeart())
            res.add(Datatype.HEARTRATE);
        if (this.hasCalories())
            res.add(Datatype.CALORIES);
        return res;
    }
}
