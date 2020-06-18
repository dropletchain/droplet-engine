//© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

package ch.ethz.dropletcam;

import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.RelativeLayout;
import android.widget.TextView;

import java.util.ArrayList;

import ch.ethz.dropletcam.util.DemoDataLoader;
import ch.ethz.dropletcam.util.DemoUser;


public class DemoSelectActivity extends AppCompatActivity {

    ListView demoView;
    ArrayList<DemoUser> users = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_demo_select);
        demoView = (ListView) findViewById(R.id.userSelectView);
        demoView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view,
                                    int position, long id) {
                if (!users.isEmpty()) {
                    Intent intent = new Intent(getApplicationContext(), CamsActivity.class);
                    intent.putExtra(ActivitiesUtil.DEMO_USER_KEY, users.get(position).toString());
                    startActivity(intent);
                }

            }
        });
        DemoDataLoader loader = new DemoDataLoader(this.getApplicationContext());
        users = loader.loadDemoUsers();
        demoView.setAdapter(new DemoUserListAdapter(this, users, loader));

    }


    public static class DemoUserListAdapter extends ArrayAdapter<DemoUser> {

        private ArrayList<DemoUser> items;
        private DemoDataLoader loader;

        public DemoUserListAdapter(Context context, ArrayList<DemoUser> items, DemoDataLoader loader) {
            super(context, R.layout.list_demo_users_layout, items);
            this.items = items;
            this.loader = loader;
        }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            DemoUser item = items.get(position);
            if (convertView == null) {
                convertView = LayoutInflater.from(getContext()).inflate(R.layout.list_demo_users_layout, parent, false);
            }
            TextView demoUserNameView = (TextView) convertView.findViewById(R.id.demoUserName);
            TextView demoUseAddressView = (TextView) convertView.findViewById(R.id.demoUserAddress);

            int imgId = this.loader.getImgResourceForUser(item);
            imgId = imgId == 0 ? R.mipmap.ic_launcher : imgId;
            ImageView imgView = (ImageView) convertView.findViewById(R.id.personimage);
            RelativeLayout layout = (RelativeLayout) convertView.findViewById(R.id.demoUserrelLayoutList);
            LinearLayout linearLayout = (LinearLayout) convertView.findViewById(R.id.demoUserlinlay);

            layout.setBackgroundColor(getContext().getResources().getColor(R.color.lightBG));
            linearLayout.setBackgroundColor(getContext().getResources().getColor(R.color.heavierBG));


            demoUserNameView.setText(item.getName());
            demoUseAddressView.setText(loader.getAddressForUser(item));
            demoUseAddressView.setTextColor(Color.BLACK);
            demoUserNameView.setTextColor(Color.BLACK);
            imgView.setBackgroundResource(imgId);

            return convertView;
        }
    }

}
