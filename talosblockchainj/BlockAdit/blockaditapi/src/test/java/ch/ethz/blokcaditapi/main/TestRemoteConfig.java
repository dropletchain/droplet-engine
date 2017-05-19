package ch.ethz.blokcaditapi.main;

import ch.ethz.blokcaditapi.DefaultConfig;

/**
 * Created by lukas on 19.05.17.
 */

public class TestRemoteConfig extends DefaultConfig {

    public TestRemoteConfig() {
        super();
        this.bcAddr = "46.101.113.112";
        this.vcAddr = "46.101.113.112";
        this.storeAddr = "46.101.113.112";
    }

}
