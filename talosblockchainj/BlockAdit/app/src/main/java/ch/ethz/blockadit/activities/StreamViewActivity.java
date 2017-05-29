package ch.ethz.blockadit.activities;

import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
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

import org.bitcoinj.core.Address;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoDataLoader;
import ch.ethz.blockadit.util.DemoUser;
import ch.ethz.blockadit.util.StreamIDType;
import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.policy.PolicyClientException;

public class StreamViewActivity extends AppCompatActivity {

    private ListView myStreams;
    private ListView streamsSharedWithMe;

    private DemoUser user;
    private BlockAditStorage storage;
    private List<DemoUser> users;
    private DemoDataLoader loader;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_stream_view);

        Intent creator = getIntent();
        String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
        this.user = DemoUser.fromString(userData);

        try {
            storage = BlockaditStorageState.getStorageForUser(this.user);
        } catch (UnknownHostException | BlockStoreException | InterruptedException e) {
            e.printStackTrace();
        }

        myStreams = (ListView) findViewById(R.id.streamSelectMine);
        streamsSharedWithMe = (ListView) findViewById(R.id.streamSelectShareWMe);

        loader = new DemoDataLoader(this);
        users = loader.loadDemoUsers();

        loadMyStreams();
        loadShareStreams();
    }

    private void loadMyStreams() {
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

            @Override
            protected void onPostExecute(List<IBlockAditStream> s) {
                super.onPostExecute(s);

                ArrayList<IBlockAditStream> streamsTemp = new ArrayList<>();
                for (int i = 0; i < s.size(); i++)
                    streamsTemp.add(s.get(i));
                BasicStreamAdapter adapter = new BasicStreamAdapter(getApplicationContext(), streamsTemp, user);
                myStreams.setAdapter(adapter);
                myStreams.setOnItemClickListener(new ItemSelectionListener(streamsTemp, false));
            }
        }.execute();
    }

    private void loadShareStreams() {
        new AsyncTask<Void, Integer, List<IBlockAditStream>>() {
            @Override
            protected List<IBlockAditStream> doInBackground(Void... params) {
                try {
                    return storage.getAccessableStreams();
                } catch (PolicyClientException | BlockAditStreamException e) {
                    e.printStackTrace();
                    return new ArrayList<>();
                }
            }

            @Override
            protected void onPostExecute(List<IBlockAditStream> s) {
                super.onPostExecute(s);

                ArrayList<IBlockAditStream> streamsTemp = new ArrayList<>();
                for (int i = 0; i < s.size(); i++)
                    streamsTemp.add(s.get(i));
                BasicStreamAdapterShare adapter = new BasicStreamAdapterShare(getApplicationContext(), streamsTemp, user);
                streamsSharedWithMe.setAdapter(adapter);
                streamsSharedWithMe.setOnItemClickListener(new ItemSelectionListener(streamsTemp, true));
            }
        }.execute();
    }

    private class ItemSelectionListener implements AdapterView.OnItemClickListener {

        private List<IBlockAditStream> streams;
        private boolean isShared;

        public ItemSelectionListener(List<IBlockAditStream> streams, boolean isShared) {
            this.streams = streams;
            this.isShared = isShared;
        }

        @Override
        public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
            IBlockAditStream selectedItem = streams.get(position);
            Intent intent = new Intent(getApplicationContext(), CloudSelectActivity.class);
            intent.putExtra(ActivitiesUtil.DEMO_USER_KEY, user.toString());
            intent.putExtra(ActivitiesUtil.STREAM_OWNER_KEY, selectedItem.getOwner().toString());
            intent.putExtra(ActivitiesUtil.STREAM_ID_KEY, selectedItem.getStreamId());
            intent.putExtra(ActivitiesUtil.IS_SHARED_KEY, isShared);
            startActivity(intent);
        }
    }

    private class BasicStreamAdapter extends ArrayAdapter<IBlockAditStream> {

        protected ArrayList<IBlockAditStream> items;
        protected DemoUser user;

        public BasicStreamAdapter(Context context, int resource, List<IBlockAditStream> objects) {
            super(context, resource, objects);
        }

        public BasicStreamAdapter(Context context, ArrayList<IBlockAditStream> items, DemoUser user) {
            super(context, R.layout.list_basic_stream, items);
            this.items = items;
            this.user = user;
        }

        @Override
        public View getView(final int position, View convertView, ViewGroup parent) {
            final IBlockAditStream item = items.get(position);
            if (convertView == null) {
                convertView = LayoutInflater.from(getContext()).inflate(R.layout.list_basic_stream, parent, false);
            }
            TextView streamName = (TextView) convertView.findViewById(R.id.streamName);
            TextView dateFrom = (TextView) convertView.findViewById(R.id.dateFromList);

            RelativeLayout layout = (RelativeLayout) convertView.findViewById(R.id.streamRelLayout);
            LinearLayout linearLayout = (LinearLayout) convertView.findViewById(R.id.streamLinLayout);

            ImageView stepsView = (ImageView) convertView.findViewById(R.id.listStepIcon);
            ImageView calView = (ImageView) convertView.findViewById(R.id.listCalIcon);
            ImageView floorView = (ImageView) convertView.findViewById(R.id.listFloorIcon);
            ImageView distView = (ImageView) convertView.findViewById(R.id.listDistIcon);
            ImageView heartView = (ImageView) convertView.findViewById(R.id.listHeartIcon);

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
        public View getDropDownView(int position, @Nullable View convertView, @NonNull ViewGroup parent) {
            return getView(position, convertView, parent);
        }
    }

    private class BasicStreamAdapterShare extends BasicStreamAdapter {

        public BasicStreamAdapterShare(Context context, ArrayList<IBlockAditStream> items, DemoUser user) {
            super(context, R.layout.list_basic_stream_share, items);
            this.items = items;
            this.user = user;
        }

        private int getResourceForImage(Address owner) {
            for (DemoUser user : users) {
                if (user.getOwnerAddress().equals(owner))
                    return loader.getImgResourceForUser(user);
            }
            return -1;
        }

        @Override
        public View getView(final int position, View convertView, ViewGroup parent) {
            final IBlockAditStream item = items.get(position);
            if (convertView == null) {
                convertView = LayoutInflater.from(getContext()).inflate(R.layout.list_basic_stream_share, parent, false);
            }
            View temp = super.getView(position, convertView, parent);
            ImageView sharePersonImage = (ImageView) temp.findViewById(R.id.sharePersonImage);
            int imgId = this.getResourceForImage(item.getOwner());
            imgId = imgId <= 0 ? R.mipmap.ic_launcher : imgId;
            sharePersonImage.setBackgroundResource(imgId);
            return temp;
        }
    }
}
