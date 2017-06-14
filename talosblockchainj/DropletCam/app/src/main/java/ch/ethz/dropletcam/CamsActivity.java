package ch.ethz.dropletcam;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.os.AsyncTask;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.RelativeLayout;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;
import ch.ethz.blokcaditapi.storage.chunkentries.PictureEntry;
import ch.ethz.dropletcam.util.DemoDataLoader;
import ch.ethz.dropletcam.util.DemoUser;

public class CamsActivity extends AppCompatActivity {

    private DemoUser user;
    private ListView camList;

    private AtomicBoolean loaded = new AtomicBoolean(false);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_cams);
        Intent creator = getIntent();
        String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
        user = DemoUser.fromString(userData);

        camList = (ListView) findViewById(R.id.camsList);

        if (loaded.get())
            loadCams();
        else
            loadStorage();
    }

    private void loadStorage() {
        if (!loaded.get()) {
            Intent i = new Intent(this, LoadingBlockchainActivity.class);
            i.putExtra(ActivitiesUtil.DEMO_USER_KEY, user.toString());
            startActivityForResult(i, 1);
        }
    }

    private void loadCams() {
        BlockAditStorage storage = null;
        try {
            storage = BlockaditStorageState.getStorageForUser(this.user);
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }
        final BlockAditStorage api_storage = storage;
        new AsyncTask<Void, Void, ArrayList<IBlockAditStream>>() {
            @Override
            protected ArrayList<IBlockAditStream> doInBackground(Void... params) {
                try {
                    List<IBlockAditStream> streams = api_storage.getAccessableStreams();
                    ArrayList<IBlockAditStream> filteredStreams = new ArrayList<>();
                    for (IBlockAditStream stream : streams) {
                        int id = stream.getStreamId();
                        if (id >= 0 && id < 20)
                            filteredStreams.add(stream);
                    }
                    return filteredStreams;
                } catch (Exception e) {
                    e.printStackTrace();
                    return null;
                }
            }

            @Override
            protected void onPostExecute(ArrayList<IBlockAditStream> streams) {
                super.onPostExecute(streams);
                StreamCamAdapter adapter = new StreamCamAdapter(getApplicationContext(), streams);
                camList.setAdapter(adapter);
                camList.setOnItemClickListener(adapter);
            }
        }.execute();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 1) {
            if (resultCode == Activity.RESULT_OK) {
                loaded.set(true);
                loadCams();
            }
            if (resultCode == Activity.RESULT_CANCELED) {
                loaded.set(false);
                Log.e("Streams", "Creation Failed :(");
            }
        }
    }

    private class StreamCamAdapter extends ArrayAdapter<IBlockAditStream> implements AdapterView.OnItemClickListener {

        private ArrayList<IBlockAditStream> items;

        StreamCamAdapter(Context context, ArrayList<IBlockAditStream> items) {
            super(context, R.layout.list_stream_layout, items);
            this.items = items;
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
        public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
            final IBlockAditStream item = items.get(position);
            if (!item.isTemporary()) {
                Intent intent = new Intent(getApplicationContext(), WebCam.class);
                intent.putExtra(ActivitiesUtil.DEMO_USER_KEY, user.toString());
                intent.putExtra(ActivitiesUtil.STREAM_OWNER_KEY, item.getOwner().toString());
                intent.putExtra(ActivitiesUtil.STREAM_ID_KEY, item.getStreamId());
                startActivity(intent);
            }
        }
    }
}
