package ch.ethz.blockadit.activities;

import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.RelativeLayout;
import android.widget.TextView;

import org.bitcoinj.core.Address;
import org.bitcoinj.store.BlockStoreException;

import java.io.Serializable;
import java.net.UnknownHostException;
import java.sql.Date;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.concurrent.atomic.AtomicInteger;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.blockadit.BlockAditFitbitAPI;
import ch.ethz.blockadit.blockadit.Datatype;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoUser;
import ch.ethz.blockadit.util.StreamIDType;
import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.policy.PolicyClientException;
/*
 * Copyright (c) 2016, Institute for Pervasive Computing, ETH Zurich.
 * All rights reserved.
 *
 * Author:
 *       Lukas Burkhalter <lubu@student.ethz.ch>
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
 * COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

public class CloudSelectActivity extends AppCompatActivity {

    private ListView list;
    private ArrayList<CloudListItem> itemsList = new ArrayList<>();

    private static ArrayList<CloudListItem> cachedOld = null;
    private static AtomicInteger loadCount = new AtomicInteger();

    private TextView dateTitle;
    private Date curDate;
    private Date today;

    private ImageButton leftButton;
    private ImageButton rightButton;

    private DemoUser user;
    private BlockAditStorage storage;
    private boolean isShare;
    private IBlockAditStream stream = null;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_cloud_select);
        getSupportActionBar().setTitle(getString(R.string.title_cloud));

        dateTitle = (TextView) findViewById(R.id.selectedDate);

        try {
            Calendar cal = Calendar.getInstance();
            cal.setTime(ActivitiesUtil.titleFormat.parse(getString(R.string.demo_cur_date)));
            cal.add(Calendar.DATE, -1);
            today = new Date(cal.getTime().getTime());
        } catch (ParseException e) {
            e.printStackTrace();
        }

        Intent creator = getIntent();
        String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
        String owner = creator.getExtras().getString(ActivitiesUtil.STREAM_OWNER_KEY);
        final int streamID = creator.getExtras().getInt(ActivitiesUtil.STREAM_ID_KEY);
        isShare = creator.getExtras().getBoolean(ActivitiesUtil.IS_SHARED_KEY);

        this.user = DemoUser.fromString(userData);

        try {
            storage = BlockaditStorageState.getStorageForUser(this.user);
        } catch (UnknownHostException | BlockStoreException | InterruptedException e) {
            e.printStackTrace();
        }


        curDate = today;
        dateTitle.setText(ActivitiesUtil.titleFormat.format(curDate));

        leftButton = (ImageButton) findViewById(R.id.imageButton);
        rightButton = (ImageButton) findViewById(R.id.imageButton2);
        rightButton.setVisibility(View.INVISIBLE);

        list = (ListView) findViewById(R.id.listView);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view,
                                    int position, long id) {
                if (!itemsList.isEmpty()) {
                    CloudListItem item = itemsList.get(position);
                    Intent intent = new Intent(getApplicationContext(), DataWeeklyActivity.class);
                    intent.putExtra(ActivitiesUtil.DETAIL_DATE_KEY, ActivitiesUtil.titleFormat.format(curDate));
                    intent.putExtra(ActivitiesUtil.DATATYPE_KEY, item.type.name());
                    intent.putExtra(ActivitiesUtil.DEMO_USER_KEY, user.toString());
                    intent.putExtra(ActivitiesUtil.STREAM_OWNER_KEY, stream.getOwner().toString());
                    intent.putExtra(ActivitiesUtil.STREAM_ID_KEY, stream.getStreamId());
                    intent.putExtra(ActivitiesUtil.IS_SHARED_KEY, isShare);
                    startActivity(intent);
                }

            }
        });
        if (cachedOld != null) {
            list.setAdapter(new CloudListAdapter(this, cachedOld));
            itemsList = cachedOld;
        }
        loadStream(Address.fromBase58(DemoUser.params, owner), streamID, isShare);
    }

    private void loadStream(final Address owner, final int streamID, final boolean isShare) {
        new AsyncTask<Void, Integer, IBlockAditStream>() {
            @Override
            protected IBlockAditStream doInBackground(Void... params) {
                try {
                    if (isShare) {
                        return storage.getAccessStreamForID(owner, streamID);
                    } else {
                        return storage.getStreamForID(owner, streamID);
                    }
                } catch (PolicyClientException | BlockAditStreamException e) {
                    e.printStackTrace();
                    return null;
                }
            }

            @Override
            protected void onPostExecute(IBlockAditStream streamRes) {
                super.onPostExecute(streamRes);
                if (streamRes != null) {
                    stream = streamRes;
                    loadCloudItems();
                }
            }
        }.execute();
    }

    private synchronized void loadCloudItems() {
        if (stream == null)
            return;
        final BlockAditFitbitAPI api = new BlockAditFitbitAPI(stream);
        final Date fixedDate = new Date(curDate.getTime());
        new AsyncTask<Void, Void, ArrayList<CloudListItem>>() {
            @Override
            protected ArrayList<CloudListItem> doInBackground(Void... params) {
                try {
                    StreamIDType types = new StreamIDType(stream.getStreamId());
                    return api.getCloudListItems(fixedDate, types.getDatatypeSet());
                } catch (BlockAditStreamException e) {
                    e.printStackTrace();
                    return new ArrayList<CloudListItem>();
                }
            }

            @Override
            protected void onPostExecute(ArrayList<CloudListItem> items) {
                super.onPostExecute(items);
                if (items == null)
                    return;
                itemsList = items;
                if (0 == loadCount.getAndIncrement())
                    cachedOld = items;
                CloudListAdapter adapter = new CloudListAdapter(getApplicationContext(), items);
                list.setAdapter(adapter);
                adapter.notifyDataSetChanged();
                list.invalidateViews();
            }
        }.execute();
    }

    public static class CloudListItem implements Serializable {
        private Datatype type;
        private String content;

        public CloudListItem(Datatype type, String content) {
            this.type = type;
            this.content = content;
        }
    }


    public synchronized void onRightClick(View v) {
        Calendar cal = Calendar.getInstance();
        cal.setTime(curDate);
        cal.add(Calendar.DATE, 1);
        curDate = new Date(cal.getTime().getTime());
        if (curDate.compareTo(today) >= 0) {
            rightButton.setVisibility(View.INVISIBLE);
        }
        dateTitle.setText(ActivitiesUtil.titleFormat.format(curDate));
        this.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                loadCloudItems();
            }
        });

    }

    public synchronized void onLeftClick(View v) {
        Calendar cal = Calendar.getInstance();
        cal.setTime(curDate);
        cal.add(Calendar.DATE, -1);
        curDate = new Date(cal.getTime().getTime());
        dateTitle.setText(ActivitiesUtil.titleFormat.format(curDate));
        if (rightButton.getVisibility() == View.INVISIBLE) {
            rightButton.setVisibility(View.VISIBLE);
        }
        this.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                loadCloudItems();
            }
        });
    }

    public static class CloudListAdapter extends ArrayAdapter<CloudListItem> {

        private ArrayList<CloudListItem> items;

        public CloudListAdapter(Context context, ArrayList<CloudListItem> items) {
            super(context, R.layout.list_cloud_layout, items);
            this.items = items;
        }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            CloudListItem item = items.get(position);
            if (convertView == null) {
                convertView = LayoutInflater.from(getContext()).inflate(R.layout.list_cloud_layout, parent, false);
            }
            TextView type = (TextView) convertView.findViewById(R.id.clouddataype);
            TextView content = (TextView) convertView.findViewById(R.id.numtoday);
            ImageView imgView = (ImageView) convertView.findViewById(R.id.cloudimage);
            RelativeLayout layout = (RelativeLayout) convertView.findViewById(R.id.relLayoutList);
            LinearLayout linearLayout = (LinearLayout) convertView.findViewById(R.id.cloudlinlay);

            layout.setBackgroundColor(getContext().getResources().getColor(R.color.lightBG));
            linearLayout.setBackgroundColor(getContext().getResources().getColor(R.color.heavierBG));


            type.setText(item.type.getDisplayRep());
            content.setText(item.content + " " + item.type.getUnit());
            content.setTextColor(Color.BLACK);
            type.setTextColor(Color.BLACK);
            imgView.setBackgroundResource(item.type.getImgResource());

            return convertView;
        }
    }
}
