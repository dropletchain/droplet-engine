package ch.ethz.blokcaditapi;

import org.bitcoinj.core.Coin;
import org.bitcoinj.core.NetworkParameters;

/**
 * Created by lukas on 12.05.17.
 */

public interface BlockAditStorageConfig {

    public Coin getTransactionFee();

    public String getVirtualchainAddress();

    public int getVirtualchainPort();

    public String getBicoinAddress();

    public NetworkParameters getNetworkParameters();

}
