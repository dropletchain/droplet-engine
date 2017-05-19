package ch.ethz.blockadit.util;

import android.content.Context;
import android.content.res.Resources;

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
        return user.getOwnerAddress().toString();
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
