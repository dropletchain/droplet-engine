package ch.ethz.blockadit.activities;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v4.widget.SwipeRefreshLayout;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.RelativeLayout;
import android.widget.TextView;

import com.daimajia.swipe.adapters.ArraySwipeAdapter;

import org.bitcoinj.core.Coin;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoUser;
import ch.ethz.blockadit.util.StreamIDType;
import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.policy.PolicyClientException;

public class PolicySettingsActivity extends AppCompatActivity {

    private DemoUser user;
    private BlockAditStorage storage;

    public  ArrayList<IBlockAditStream> streams = new ArrayList<>();
    private ListView listView;
    private SwipeRefreshLayout refreshLayout;
    private TextView ownerView;
    private TextView balanceView;



    public static Map<String, ArrayList<IBlockAditStream>> temporaryStreams = new HashMap<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_policy_settings);

        Intent creator = getIntent();
        String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
        this.user = DemoUser.fromString(userData);

        try {
            storage = BlockaditStorageState.getStorageForUser(this.user);
        } catch (UnknownHostException | BlockStoreException | InterruptedException e) {
            e.printStackTrace();
        }

        ownerView = (TextView) findViewById(R.id.ownerSetting);
        ownerView.setText(String.format("Owner: %s", user.getOwnerAddress().toString()));

        balanceView = (TextView) findViewById(R.id.BalanceSetting);
        listView = (ListView) findViewById(R.id.streamSelectView);
        refreshLayout = (SwipeRefreshLayout) findViewById(R.id.swiperefresh);
        refreshLayout.setOnRefreshListener(
                new SwipeRefreshLayout.OnRefreshListener() {
                    @Override
                    public void onRefresh() {
                        loadStreams();
                        refreshLayout.setRefreshing(false);
                    }
                }
        );
        loadStreams();
        loadBalance();
    }

    private void loadStreams() {
        new AsyncTask<Void, Integer, List<IBlockAditStream>>() {
            @Override
            protected List<IBlockAditStream> doInBackground(Void... params) {
                try {
                    return storage.getStreams();
                } catch (PolicyClientException | BlockAditStreamException e) {
                    e.printStackTrace();
                    return new ArrayList<>();
                }
            }

            private boolean checkInList(List<IBlockAditStream> streams, IBlockAditStream stream) {
                for (IBlockAditStream cur : streams)
                    if(cur.getOwner().equals(stream.getOwner()) && cur.getStreamId() == stream.getStreamId())
                        return true;
                return false;
            }

            @Override
            protected void onPostExecute(List<IBlockAditStream> s) {
                super.onPostExecute(s);
                if(!temporaryStreams.containsKey(user.getName()))
                    temporaryStreams.put(user.getName(), new ArrayList<IBlockAditStream>());

                ArrayList<IBlockAditStream> streamsTemp = new ArrayList<>();
                for (int i=0; i<s.size(); i++)
                    streamsTemp.add(s.get(i));
                Iterator<IBlockAditStream> iter = temporaryStreams.get(user.getName()).iterator();
                while (iter.hasNext()) {
                    IBlockAditStream cur = iter.next();
                    if(checkInList(s, cur)) {
                        iter.remove();
                    } else {
                        streamsTemp.add(cur);
                    }
                }
                streams = streamsTemp;
                StreamAdapter adapter = new StreamAdapter(getApplicationContext(), streamsTemp, user);
                listView.setAdapter(adapter);
                listView.setOnItemClickListener(adapter);
            }
        }.execute();
    }

    public void onAddStream(View v) {
        Intent i = new Intent(this, CreateStream.class);
        i.putExtra(ActivitiesUtil.DEMO_USER_KEY, this.user.toString());
        startActivityForResult(i, 1);
    }

    public void loadBalance() {
        new AsyncTask<Void, Integer, Coin>() {
            @Override
            protected Coin doInBackground(Void... params) {
                return storage.getBalance();
            }

            @Override
            protected void onPostExecute(Coin ok) {
                super.onPostExecute(ok);

                if(ok != null ) {
                    balanceView.setText(ok.toFriendlyString());
                }
            }
        }.execute();
    }

    public void onQR(View v) {
        Intent i = new Intent(this, QRCodeActivity.class);
        i.putExtra(ActivitiesUtil.QR_SELECT_STRING_KEY, this.user.getShareAddress().toString());
        startActivityForResult(i, 0);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 1) {
            if(resultCode == Activity.RESULT_OK){
                loadStreams();
                loadBalance();
            }
            if (resultCode == Activity.RESULT_CANCELED) {
                Log.e("Streams", "Creation Failed :(");
            }
        }
    }


    private class StreamAdapter extends ArraySwipeAdapter<IBlockAditStream> implements AdapterView.OnItemClickListener {

        private ArrayList<IBlockAditStream> items;
        private DemoUser user;

        public StreamAdapter(Context context, ArrayList<IBlockAditStream> items, DemoUser user) {
            super(context, R.layout.list_stream_layout, items);
            this.items = items;
            this.user = user;
        }

        private void erasejob(final IBlockAditStream item) {
            new AsyncTask<Void, Integer, Boolean>() {
                @Override
                protected Boolean doInBackground(Void... params) {
                    try {
                        item.getPolicyManipulator().invalidate();
                    } catch (InsufficientMoneyException | PolicyClientException e) {
                        e.printStackTrace();
                        return false;
                    }
                    return true;
                }

                @Override
                protected void onPostExecute(Boolean ok) {
                    super.onPostExecute(ok);
                    if(!temporaryStreams.containsKey(user.getName()))
                        temporaryStreams.put(user.getName(), new ArrayList<IBlockAditStream>());
                    Iterator<IBlockAditStream> iter = temporaryStreams.get(user.getName()).iterator();
                    while (iter.hasNext()) {
                        IBlockAditStream cur = iter.next();
                        if(cur.getOwner().equals(item.getOwner())
                                && cur.getStreamId() == item.getStreamId()) {
                            iter.remove();
                            break;
                        }

                    }
                }
            }.execute();
        }

        @Override
        public View getView(final int position, View convertView, ViewGroup parent) {
            final IBlockAditStream item = items.get(position);
            if (convertView == null) {
                convertView = LayoutInflater.from(getContext()).inflate(R.layout.list_stream_layout, parent, false);
            }
            TextView streamName = (TextView) convertView.findViewById(R.id.streamName);
            TextView dateFrom = (TextView) convertView.findViewById(R.id.dateFromList);

            //ImageView imgView = (ImageView) convertView.findViewById(R.id.imgStream);
            RelativeLayout layout = (RelativeLayout) convertView.findViewById(R.id.streamRelLayout);
            LinearLayout linearLayout = (LinearLayout) convertView.findViewById(R.id.streamLinLayout);

            ImageView stepsView = (ImageView) convertView.findViewById(R.id.listStepIcon);
            ImageView calView = (ImageView) convertView.findViewById(R.id.listCalIcon);
            ImageView floorView = (ImageView) convertView.findViewById(R.id.listFloorIcon);
            ImageView distView = (ImageView) convertView.findViewById(R.id.listDistIcon);
            ImageView heartView = (ImageView) convertView.findViewById(R.id.listHeartIcon);
            TextView temporaryField = (TextView) convertView.findViewById(R.id.temporaryField);

            Button button = (Button) convertView.findViewById(R.id.deleteButton);
            final StreamAdapter adapter = this;
            button.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    erasejob(item);
                    items.remove(position);
                    adapter.notifyDataSetChanged();
                }
            });

            StreamIDType typesStrem = new StreamIDType(item.getStreamId());

            if (typesStrem.hasSteps())
                stepsView.setVisibility(View.VISIBLE);
            else
                stepsView.setVisibility(View.INVISIBLE);
            if (typesStrem.hasCalories())
                calView.setVisibility(View.VISIBLE);
            else
                calView.setVisibility(View.INVISIBLE);
            if (typesStrem.hasFloor())
                floorView.setVisibility(View.VISIBLE);
            else
                floorView.setVisibility(View.INVISIBLE);
            if (typesStrem.hasDist())
                distView.setVisibility(View.VISIBLE);
            else
                distView.setVisibility(View.INVISIBLE);
            if (typesStrem.hasHeart())
                heartView.setVisibility(View.VISIBLE);
            else
                heartView.setVisibility(View.INVISIBLE);


            if(item.isTemporary())
                temporaryField.setVisibility(View.VISIBLE);
            else
                temporaryField.setVisibility(View.INVISIBLE);


            layout.setBackgroundColor(getContext().getResources().getColor(R.color.lightBG));
            linearLayout.setBackgroundColor(getContext().getResources().getColor(R.color.heavierBG));

            Date startDate = new Date(item.getStartTimestamp() * 1000);

            streamName.setText(String.format("Stream %d", item.getStreamId()));
            dateFrom.setText(String.format("From: %s", ActivitiesUtil.titleFormat.format(startDate)));
            //imgView.setImageBitmap(AppUtil.createQRCode(item.getOwner().toString() + item.getStreamId()));
            streamName.setTextColor(Color.BLACK);
            dateFrom.setTextColor(Color.BLACK);

            return convertView;
        }

        @Override
        public int getSwipeLayoutResourceId(int position) {
            return R.id.swipe;
        }

        @Override
        public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
            final IBlockAditStream item = items.get(position);
            if(!item.isTemporary()) {
                Intent intent = new Intent(getApplicationContext(), PolicyDetailedActivity.class);
                intent.putExtra(ActivitiesUtil.DEMO_USER_KEY, this.user.toString());
                intent.putExtra(ActivitiesUtil.STREAM_OWNER_KEY, item.getOwner().toString());
                intent.putExtra(ActivitiesUtil.STREAM_ID_KEY, item.getStreamId());
                startActivity(intent);
            }
        }
    }

}
