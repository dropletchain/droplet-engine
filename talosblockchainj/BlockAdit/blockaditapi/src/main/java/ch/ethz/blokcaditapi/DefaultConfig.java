package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Coin;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.params.RegTestParams;

/**
 * Default dummy configuration for the system.
 */

public class DefaultConfig implements BlockAditStorageConfig {

    protected Coin fee = Coin.parseCoin("0.0001");
    protected String vcAddr = "127.0.0.1";
    protected int vcPort = 5000;
    protected int vcCacheTime = 1;
    protected String bcAddr = "127.0.0.1";
    protected String storeAddr = "127.0.0.1";
    protected int storePort = 14000;
    protected NetworkParameters parameters = RegTestParams.get();

    protected DefaultConfig() {
    }

    public static BlockAditStorageConfig get() {
        return new DefaultConfig();
    }

    @Override
    public Coin getTransactionFee() {
        return fee;
    }

    @Override
    public String getVirtualchainAddress() {
        return vcAddr;
    }

    @Override
    public int getVirtualchainPort() {
        return vcPort;
    }

    @Override
    public int getPolicyCacheTime() {
        return vcCacheTime;
    }

    @Override
    public String getBitcoinAddress() {
        return bcAddr;
    }

    @Override
    public String getStorageApiAddress() {
        return storeAddr;
    }

    @Override
    public int getStorageApiPort() {
        return storePort;
    }

    @Override
    public NetworkParameters getNetworkParameters() {
        return parameters;
    }
}
