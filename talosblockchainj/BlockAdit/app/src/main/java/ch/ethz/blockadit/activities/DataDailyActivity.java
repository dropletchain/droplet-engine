package ch.ethz.blockadit.activities;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.graphics.Color;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Handler;
import android.support.v7.app.ActionBar;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.View;
import android.widget.TextView;

import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;

import org.bitcoinj.core.Address;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.blockadit.BlockAditFitbitAPI;
import ch.ethz.blockadit.blockadit.Datatype;
import ch.ethz.blockadit.blockadit.TalosAPIFactory;
import ch.ethz.blockadit.blockadit.model.DataEntryAgrTime;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoUser;
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

public class DataDailyActivity extends AppCompatActivity {

    private static final boolean AUTO_HIDE = true;

    private static final int AUTO_HIDE_DELAY_MILLIS = 3000;


    private static final int UI_ANIMATION_DELAY = 300;
    private final Handler mHideHandler = new Handler();
    private View mContentView;
    private final Runnable mHidePart2Runnable = new Runnable() {
        @SuppressLint("InlinedApi")
        @Override
        public void run() {
            // Delayed removal of status and navigation bar

            // Note that some of these constants are new as of API 16 (Jelly Bean)
            // and API 19 (KitKat). It is safe to use them, as they are inlined
            // at compile-time and do nothing on earlier devices.
            mContentView.setSystemUiVisibility(View.SYSTEM_UI_FLAG_LOW_PROFILE
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);
        }
    };
    private View mControlsView;
    private final Runnable mShowPart2Runnable = new Runnable() {
        @Override
        public void run() {
            // Delayed display of UI elements
            ActionBar actionBar = getSupportActionBar();
            if (actionBar != null) {
                actionBar.show();
            }
            mControlsView.setVisibility(View.VISIBLE);
        }
    };
    private boolean mVisible;
    private final Runnable mHideRunnable = new Runnable() {
        @Override
        public void run() {
            hide();
        }
    };

    private final View.OnTouchListener mDelayHideTouchListener = new View.OnTouchListener() {
        @Override
        public boolean onTouch(View view, MotionEvent motionEvent) {
            if (AUTO_HIDE) {
                delayedHide(AUTO_HIDE_DELAY_MILLIS);
            }
            return false;
        }
    };

    private LineChart mChart;
    private Date detailDate;
    private Datatype type;
    private TextView title;

    private DemoUser user;
    private BlockAditStorage storage;
    private boolean isShare;
    private IBlockAditStream stream = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_data_daily);
        ActionBar actionBar = getSupportActionBar();
        if (actionBar != null) {
            actionBar.setDisplayHomeAsUpEnabled(true);
        }

        mVisible = true;
        mControlsView = findViewById(R.id.fullscreen_content_controls);
        mContentView = findViewById(R.id.fullscreen_content);

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


        // Set up the user interaction to manually show or hide the system UI.
        mContentView.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                toggle();
            }
        });

        // Upon interacting with UI controls, delay any scheduled hide()
        // operations to prevent the jarring behavior of controls going away
        // while interacting with the UI.

        try {
            detailDate = ActivitiesUtil.titleFormat.parse(getIntent().getExtras().getString(ActivitiesUtil.DETAIL_DATE_KEY));
        } catch (ParseException e) {
            e.printStackTrace();
        }
        type = Datatype.valueOf(getIntent().getExtras().getString(ActivitiesUtil.DATATYPE_KEY));

        title = (TextView) findViewById(R.id.titlelinechart);
        title.setText(getTitle(type,detailDate));

        mChart = (LineChart) findViewById(R.id.linechart);
        mChart.getAxisRight().setEnabled(false);
        mChart.setClickable(false);
        XAxis xAxis = mChart.getXAxis();
        xAxis.setEnabled(true);
        //xAxis.setValueFormatter(new XValFormatter());
        xAxis.setPosition(XAxis.XAxisPosition.TOP);
        xAxis.setTextSize(10f);
        xAxis.setTextColor(Color.BLACK);
        xAxis.setDrawAxisLine(true);
        xAxis.setDrawLabels(true);
        xAxis.setDrawGridLines(false);
        xAxis.setAvoidFirstLastClipping(true);
        xAxis.setLabelsToSkip(4);
        mChart.setDescription("");
        mChart.getLegend().setEnabled(false);
        mChart.setGridBackgroundColor(getResources().getColor(R.color.lightBG));
        setEmptyData();

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
                    loadData();
                }
            }
        }.execute();
    }

    private String getTitle(Datatype titleType, Date titleDate) {
        StringBuilder sb = new StringBuilder();
        sb.append(titleType.getDisplayRep())
                .append(" ")
                .append(ActivitiesUtil.titleFormat.format(titleDate));
        return sb.toString();
    }

    private void setEmptyData() {
        int index = 0;
        Calendar from = Calendar.getInstance();
        from.setTime(detailDate);
        Calendar to = Calendar.getInstance();
        to.setTime(detailDate);
        to.add(Calendar.DATE,1);

        ArrayList<String> xVals = new ArrayList<String>();
        ArrayList<Entry> yVals = new ArrayList<Entry>();
        for(;from.getTime().before(to.getTime()); from.add(Calendar.MINUTE, 30)) {
            Date date = from.getTime();
            Log.d("Date", from.toString());
            Log.d("Date", ActivitiesUtil.timeFormat.format(date));
            xVals.add(ActivitiesUtil.timeFormat.format(date));
            yVals.add(new Entry(0, index));
            index++;
        }

        LineDataSet set1 = new LineDataSet(yVals, "DataSet1");
        setLineLayout(set1);



        ArrayList<LineDataSet> dataSets = new ArrayList<LineDataSet>();
        dataSets.add(set1);
        LineData data = new LineData(xVals, dataSets);
        mChart.setData(data);
    }

    private void setData(ArrayList<DataEntryAgrTime> times) {
        int index = 0;
        HashMap<String,DataEntryAgrTime> mappings = new HashMap<>(times.size());
        Calendar from = Calendar.getInstance();
        from.setTime(detailDate);
        Calendar to = Calendar.getInstance();
        to.setTime(detailDate);
        to.add(Calendar.DATE,1);

        for(DataEntryAgrTime time : times) {
            mappings.put(ActivitiesUtil.keyFormat.format(new Date(time.getTime().getTime())),time);
        }

        ArrayList<String> xVals = new ArrayList<String>();
        ArrayList<Entry> yVals = new ArrayList<Entry>();
        for(;from.getTime().before(to.getTime()); from.add(Calendar.MINUTE, 30)) {
            Date time = from.getTime();
            xVals.add(ActivitiesUtil.timeFormat.format(time));
            String key = ActivitiesUtil.keyFormat.format(time);
            if(mappings.containsKey(key)) {
                DataEntryAgrTime container = mappings.get(key);
                yVals.add(new Entry(Float.valueOf(type.formatValue(container.getValue())), index));
            } else {
                yVals.add(new Entry(0, index));
            }
            index++;
        }

        LineDataSet set1 = new LineDataSet(yVals, "DataSet2");
        setLineLayout(set1);

        ArrayList<LineDataSet> dataSets = new ArrayList<>();
        dataSets.add(set1);
        LineData data = new LineData(xVals, dataSets);
        mChart.setData(data);
        mChart.animateX(3000);
    }

    private void setLineLayout(LineDataSet set1) {
        set1.setDrawValues(false);
        set1.setColor(getResources().getColor(R.color.heavierBG));
        set1.setCircleColor(getResources().getColor(R.color.heavierBG));
        set1.setCircleColorHole(getResources().getColor(R.color.lightBG));
        set1.setLineWidth(3f);
        set1.setCircleSize(4f);
    }

    private void loadData() {
        final BlockAditFitbitAPI api = TalosAPIFactory.createAPI(stream);
        final Date dstDate = new Date(detailDate.getTime());
        (new AsyncTask<Void, Void, ArrayList<DataEntryAgrTime>>() {
            @Override
            protected ArrayList<DataEntryAgrTime> doInBackground(Void... params) {
                try {
                    return api.getAgrDataForDate(new java.sql.Date(dstDate.getTime()), type);
                } catch (BlockAditStreamException e) {
                    e.printStackTrace();
                    return null;
                }
            }

            @Override
            protected void onPostExecute(ArrayList<DataEntryAgrTime> s) {
                super.onPostExecute(s);
                if(s!=null) {
                    setData(s);
                }
            }
        }).execute();
    }

    @Override
    protected void onPostCreate(Bundle savedInstanceState) {
        super.onPostCreate(savedInstanceState);

        // Trigger the initial hide() shortly after the activity has been
        // created, to briefly hint to the user that UI controls
        // are available.
        delayedHide(100);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        int id = item.getItemId();
        if (id == android.R.id.home) {
            Intent intent = new Intent(getApplicationContext(), DataWeeklyActivity.class);
            intent.putExtra(ActivitiesUtil.DATATYPE_KEY, type.name());
            intent.putExtra(ActivitiesUtil.DETAIL_DATE_KEY, ActivitiesUtil.titleFormat.format(detailDate));
            startActivity(intent);
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    private void toggle() {
        if (mVisible) {
            hide();
        } else {
            show();
        }
    }

    private void hide() {
        // Hide UI first
        ActionBar actionBar = getSupportActionBar();
        if (actionBar != null) {
            actionBar.hide();
        }
        mControlsView.setVisibility(View.GONE);
        mVisible = false;

        // Schedule a runnable to remove the status and navigation bar after a delay
        mHideHandler.removeCallbacks(mShowPart2Runnable);
        mHideHandler.postDelayed(mHidePart2Runnable, UI_ANIMATION_DELAY);
    }

    @SuppressLint("InlinedApi")
    private void show() {
        // Show the system bar
        mContentView.setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
        mVisible = true;

        // Schedule a runnable to display UI elements after a delay
        mHideHandler.removeCallbacks(mHidePart2Runnable);
        mHideHandler.postDelayed(mShowPart2Runnable, UI_ANIMATION_DELAY);
    }


    private void delayedHide(int delayMillis) {
        mHideHandler.removeCallbacks(mHideRunnable);
        mHideHandler.postDelayed(mHideRunnable, delayMillis);
    }

}
