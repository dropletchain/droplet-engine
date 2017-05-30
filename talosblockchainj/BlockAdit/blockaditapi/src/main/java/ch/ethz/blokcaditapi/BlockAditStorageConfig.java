package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Coin;
import org.bitcoinj.core.NetworkParameters;

/**
 * Interface for a system configuration
 */

public interface BlockAditStorageConfig {

    public Coin getTransactionFee();

    public String getVirtualchainAddress();

    public int getVirtualchainPort();

    public int getPolicyCacheTime();

    public String getBitcoinAddress();

    public String getStorageApiAddress();

    public int getStorageApiPort();

    public NetworkParameters getNetworkParameters();

}
