package ch.ethz.blockadit.activities;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.support.customtabs.CustomTabsIntent;
import android.support.v7.app.AppCompatActivity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.RelativeLayout;
import android.widget.Spinner;
import android.widget.TextView;

import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.fitbitapi.FitbitAPI;
import ch.ethz.blockadit.fitbitapi.TokenInfo;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoDataLoader;
import ch.ethz.blockadit.util.DemoUser;
import ch.ethz.blockadit.util.StreamIDType;
import ch.ethz.blockadit.util.Synchronizer;
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

public class FitbitSync extends AppCompatActivity {
    private static final String CALLBACK = "fitbittalos://logincallback";
    private static final String SCOPE = "activity%20heartrate";

    public static final String ACCESS_TOKEN_KEY = "ACC_KEY";

    private TokenInfo info = null;

    private Spinner streamSelect;
    private TextView progressText;
    private ProgressBar progressBar;

    private Date demoEndDate;

    public int dateIndex = 0;

    private static DemoUser user;
    private BlockAditStorage storage;
    ArrayList<IBlockAditStream> streams = new ArrayList<>();
    int curSelectIndex = -1;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_fitbit_auth);
        String data = getIntent().getDataString();
        SharedPreferences sharedPref = this.getPreferences(Context.MODE_PRIVATE);
        getSupportActionBar().setTitle(getResources().getString(R.string.title_sync));
        Intent creator = getIntent();
        if(creator!=null && creator.getExtras().containsKey(ActivitiesUtil.DEMO_USER_KEY)) {
            String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
            user = DemoUser.fromString(userData);
        }

        try {
            demoEndDate = ActivitiesUtil.titleFormat.parse(getString(R.string.demo_cur_date));
        } catch (ParseException e) {
            e.printStackTrace();
        }

        if(data==null || !data.contains(CALLBACK)) {
            boolean auth = true;
            if(sharedPref.contains(ACCESS_TOKEN_KEY)) {
                info = TokenInfo.fromJSON(sharedPref.getString(ACCESS_TOKEN_KEY, ""));
                auth = !info.isValid();
                if(auth) {
                    SharedPreferences.Editor editor = sharedPref.edit();
                    editor.remove(ACCESS_TOKEN_KEY);
                    editor.apply();
                }
            }

            if(auth) {
                Uri uri = FitbitAPI.getAccessTokenURI(getString(R.string.fitbit_client_id), SCOPE, CALLBACK);
                CustomTabsIntent customTabsIntent = new CustomTabsIntent.Builder().setToolbarColor(Color.GREEN).build();
                customTabsIntent.launchUrl(FitbitSync.this, uri);
            }

        } else {

            Uri uri = Uri.parse(data);
            try {
                info = TokenInfo.fromURI(uri);
            } catch (Exception e) {
                setResult(RESULT_CANCELED);
                finish();
            }
            SharedPreferences.Editor editor = sharedPref.edit();
            editor.putString(ACCESS_TOKEN_KEY, info.toString());
            editor.apply();
        }
        try {
            storage = BlockaditStorageState.getStorageForUser(user);
        } catch (UnknownHostException | InterruptedException | BlockStoreException e) {
            e.printStackTrace();
        }

        DemoDataLoader loader = new DemoDataLoader(this);
        progressBar = (ProgressBar) findViewById(R.id.progressBar);
        progressText = (TextView) findViewById(R.id.progress);
        streamSelect = (Spinner) findViewById(R.id.streamSelectSpinner);


        progressBar.setVisibility(View.INVISIBLE);
        progressText.setVisibility(View.INVISIBLE);
        setSpinnerData();
    }

    private void setSpinnerData() {
        final Spinner spinner = this.streamSelect;
        new AsyncTask<Void, Integer, List<IBlockAditStream>>() {
            @Override
            protected List<IBlockAditStream> doInBackground(Void... params) {
                try {
                    return storage.getStreams();
                } catch (PolicyClientException e) {
                    e.printStackTrace();
                    return new ArrayList<IBlockAditStream>();
                } catch (BlockAditStreamException e) {
                    e.printStackTrace();
                    return new ArrayList<IBlockAditStream>();
                }
            }

            @Override
            protected void onPostExecute(List<IBlockAditStream> s) {
                super.onPostExecute(s);

                ArrayList<IBlockAditStream> streamsTemp = new ArrayList<>();
                for (int i=0; i<s.size(); i++)
                    streamsTemp.add(s.get(i));
                streams = streamsTemp;
                spinner.setAdapter(new BasicStreamAdapter(getApplicationContext(), streamsTemp, user));
                spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
                    @Override
                    public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                        curSelectIndex = position;
                    }

                    @Override
                    public void onNothingSelected(AdapterView<?> parent) {
                        if(streams != null && !streams.isEmpty()) {
                            curSelectIndex = 0;
                        } else {
                            curSelectIndex = -1;
                        }
                    }
                });
            }
        }.execute();
    }



    public synchronized void onSyncPressed(View view) {
        if(curSelectIndex == -1 || storage == null)
            return;
        IBlockAditStream stream = streams.get(curSelectIndex);
        StreamIDType type = new StreamIDType(stream.getStreamId());
        final Synchronizer synchronizer = new Synchronizer(stream, this.info, type.getDatatypeSet());
        int numBlocks = (int) (86400 / stream.getInterval());

        Date startDate = new Date(stream.getStartTimestamp() * 1000);
        Calendar start = Calendar.getInstance();
        start.setTime(startDate);
        Calendar end = Calendar.getInstance();
        end.setTime(demoEndDate);

        List<Date> toProcess = new ArrayList<>();
        for (Date date = start.getTime(); start.before(end); start.add(Calendar.DATE, 1), date = start.getTime()) {
            toProcess.add(date);
        }

        if(toProcess.isEmpty())
            return;

        SyncTask[] tasks = new SyncTask[toProcess.size()];
        SyncState state = new SyncState(tasks.length);
        for(int iter=0; iter<tasks.length; iter++) {
            tasks[iter] = new SyncTask(iter, toProcess.get(iter), synchronizer, numBlocks, state);
        }

        progressBar.setVisibility(View.VISIBLE);
        // start Tasks (executed on internal Thread pool)
        for(int iter=0; iter<tasks.length; iter++) {
            tasks[iter].execute();
        }

    }

    private class SyncState {
        AtomicInteger counter = new AtomicInteger(0);
        boolean[] result;

        public SyncState(int numResults) {
            this.result = new boolean[numResults];
        }
    }

    private class SyncTask extends AsyncTask<Void, Integer, String> {

        private int taskID;
        private Synchronizer synchronizer;
        private int numBlocks;
        private Date date;
        private SyncState state;

        public SyncTask(int taskID, Date date, Synchronizer synchronizer, int numBlocks, SyncState state) {
            super();
            this.taskID = taskID;
            this.synchronizer = synchronizer;
            this.date = date;
            this.numBlocks = numBlocks;
            this.state = state;
        }

        @Override
        protected String doInBackground(Void... params) {
            try {
                synchronizer.transferDataForDate(date, numBlocks);
                state.result[taskID] = true;
                return "Success";
            } catch (BlockAditStreamException e) {
                e.printStackTrace();
                state.result[taskID] = false;
                return "Error occured :(";
            } finally {
                state.counter.incrementAndGet();
            }
        }

        @Override
        protected void onPostExecute(String s) {
            super.onPostExecute(s);
            int curCounter = state.counter.get();
            double length = (100.0 / state.result.length) * curCounter;
            progressBar.setProgress((int) length);
            if (curCounter == state.result.length) {
                boolean ok = true;
                for (boolean x : state.result) {
                    if(!x) {
                        ok = false;
                        break;
                    }
                }
                if (ok) {
                    progressText.setText("Success");
                    progressText.setVisibility(View.VISIBLE);
                } else {
                    progressText.setText("Failure");
                    progressText.setVisibility(View.VISIBLE);
                }
                progressBar.setVisibility(View.INVISIBLE);
            }

        }
    }


    private class BasicStreamAdapter extends ArrayAdapter<IBlockAditStream> {

        private ArrayList<IBlockAditStream> items;
        private DemoUser user;

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
}
