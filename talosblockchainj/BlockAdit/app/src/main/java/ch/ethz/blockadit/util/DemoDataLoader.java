package ch.ethz.blockadit.util;

import android.content.Context;
import android.content.res.Resources;

import org.bitcoinj.core.Base58;
import org.bitcoinj.core.DumpedPrivateKey;
import org.bitcoinj.core.ECKey;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.params.RegTestParams;

import java.math.BigInteger;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

import ch.ethz.blockadit.R;

/**
 * Created by lukas on 18.05.17.
 */
public class DemoDataLoader {

    private Context context;
    private NetworkParameters parameters = RegTestParams.get();

    public DemoDataLoader(Context context) {
        this.context = context;
    }

    public ArrayList<DemoUser> loadDemoUsers() {
        ArrayList<DemoUser> users = new ArrayList<>();
        Resources res = context.getResources();
        String[] userNames = res.getStringArray(R.array.user_names);
        String[] userKeys = res.getStringArray(R.array.user_keys);
        String[] shareKeys = res.getStringArray(R.array.user_share_keys);
        for (int i=0; i< userNames.length; i++)
            users.add(new DemoUser(userNames[i], userKeys[i], shareKeys[i]));
        return users;
    }

    public int getImgResourceForUser(DemoUser user) {
        return context.getResources().getIdentifier(user.getName().toLowerCase(), "drawable", context.getPackageName());
    }

    public String getAddressForUser(DemoUser user) {
        ECKey key;
        String privKey = user.getOwnerKey();
        if (privKey.length() == 51 || privKey.length() == 52) {
            DumpedPrivateKey dumpedPrivateKey = DumpedPrivateKey.fromBase58(parameters, privKey);
            key = dumpedPrivateKey.getKey();
        } else {
            BigInteger privKeyNum= Base58.decodeToBigInteger(privKey);
            key = ECKey.fromPrivate(privKeyNum);
        }
        return key.toAddress(parameters).toString();
    }

    public Date getCurDate() {
        SimpleDateFormat format = new SimpleDateFormat("dd.MM.yyyy");
        try {
            return format.parse(context.getString(R.string.demo_cur_date));
        } catch (ParseException e) {
            e.printStackTrace();
            return new Date();
        }
    }

}
