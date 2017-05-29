package ch.ethz.blockadit.activities;

import android.app.Activity;
import android.app.DatePickerDialog;
import android.app.Dialog;
import android.app.DialogFragment;
import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.DatePicker;
import android.widget.ProgressBar;
import android.widget.SeekBar;
import android.widget.TextView;

import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.util.AppUtil;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoUser;
import ch.ethz.blockadit.util.StreamIDType;
import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.policy.PolicyClientException;

import static ch.ethz.blockadit.activities.PolicySettingsActivity.temporaryStreams;

public class CreateStream extends AppCompatActivity {

    private CheckBox stepsRadio;
    private CheckBox floorRadio;
    private CheckBox distRadio;
    private CheckBox calRadio;
    private CheckBox heartRadio;

    private Button fromDate;
    private SeekBar interval;
    private TextView intervalSelection;

    private long curInterval;
    private Date curDate = null;

    private DemoUser user;
    private BlockAditStorage storage;
    private ProgressBar bar;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_create_stream);

        Intent creator = getIntent();
        String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
        this.user = DemoUser.fromString(userData);

        try {
            storage = BlockaditStorageState.getStorageForUser(this.user);
        } catch (UnknownHostException | BlockStoreException | InterruptedException e) {
            e.printStackTrace();
        }

        stepsRadio = (CheckBox) findViewById(R.id.radioSteps);
        floorRadio = (CheckBox) findViewById(R.id.radioFloors);
        distRadio = (CheckBox) findViewById(R.id.radioDistance);
        calRadio = (CheckBox) findViewById(R.id.radioCalendar);
        heartRadio = (CheckBox) findViewById(R.id.radioHeart);

        fromDate = (Button) findViewById(R.id.fromDateSelect);
        interval = (SeekBar) findViewById(R.id.seekBarInterval);
        intervalSelection = (TextView) findViewById(R.id.selectedInterval);

        bar = (ProgressBar) findViewById(R.id.progressCreateStream);
        bar.setVisibility(View.INVISIBLE);
        interval.setProgress(100);
        curInterval = 24 * 3600;
        interval.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {

            private int updateProgress(SeekBar seekBar, int progressIn) {
                double progress = progressIn;
                progress = progress / 100 * 24;
                int numHours = (int) progress;
                if (numHours == 0) {
                    numHours = 1;
                }

                if (24 % numHours > 0) {
                    while (numHours < 24 && (24 % numHours > 0)) {
                        numHours++;
                    }
                }

                progress = (numHours / 24.0) * 100;
                seekBar.setProgress((int) progress);
                return numHours;
            }

            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                if (fromUser) {
                    int numHours = updateProgress(seekBar, progress);
                    if (numHours == 24) {
                        intervalSelection.setText(String.format("%dd", 1));
                    } else {
                        intervalSelection.setText(String.format("%dh", numHours));
                    }
                }
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {

            }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                int numHours = updateProgress(seekBar, seekBar.getProgress());
                curInterval = numHours * 3600;
            }
        });

    }

    public void selectedFromDate(View v) {
        DialogFragment newFragment = new CreateStreamDatePicker();
        newFragment.show(this.getFragmentManager(), "tag1");
    }

    public void onCreateStream(View v) {
        boolean[] types = new boolean[5];
        types[0] = stepsRadio.isChecked();
        types[1] = floorRadio.isChecked();
        types[2] = distRadio.isChecked();
        types[3] = calRadio.isChecked();
        types[4] = heartRadio.isChecked();

        boolean cur = false;
        for (boolean tmp : types)
            cur |= tmp;
        if (!cur)
            return;
        final int streamId = StreamIDType.createId(types);

        if (curDate == null)
            return;

        final long startTime = this.curDate.getTime() / 1000;

        new AsyncTask<Void, Integer, IBlockAditStream>() {
            @Override
            protected void onPreExecute() {
                super.onPreExecute();
                bar.setVisibility(View.VISIBLE);
            }

            @Override
            protected IBlockAditStream doInBackground(Void... params) {
                try {
                    return storage.createNewStream(user.getOwnerAddress(),
                            streamId, startTime, curInterval);
                } catch (PolicyClientException | BlockAditStreamException | InsufficientMoneyException e) {
                    e.printStackTrace();
                }
                return null;
            }

            @Override
            protected void onPostExecute(IBlockAditStream stream) {
                super.onPostExecute(stream);
                bar.setVisibility(View.INVISIBLE);
                if (stream == null) {
                    Intent returnIntent = new Intent();
                    setResult(Activity.RESULT_CANCELED, returnIntent);
                    finish();
                } else {
                    if (!temporaryStreams.containsKey(user.getName()))
                        temporaryStreams.put(user.getName(), new ArrayList<IBlockAditStream>());
                    temporaryStreams.get(user.getName()).add(stream);
                    Intent returnIntent = new Intent();
                    setResult(Activity.RESULT_OK, returnIntent);
                    finish();
                }

            }
        }.execute();
    }

    public void onFromDateSet(Date date) {
        //Hack
        curDate = new Date((new java.sql.Date(date.getTime())).getTime());
        fromDate.setText(ActivitiesUtil.titleFormat.format(curDate));
    }

    public static class CreateStreamDatePicker extends DialogFragment implements DatePickerDialog.OnDateSetListener {

        private CreateStream attached;

        @Override
        public void onAttach(Activity activity) {
            super.onAttach(activity);
            attached = (CreateStream) activity;
        }

        @Override
        public Dialog onCreateDialog(Bundle savedInstanceState) {
            final Calendar c = Calendar.getInstance();
            int month = c.get(Calendar.MONTH);
            int day = c.get(Calendar.DAY_OF_MONTH);
            int year = c.get(Calendar.YEAR);

            return new DatePickerDialog(getActivity(), this, year, month, day);
        }

        @Override
        public void onDateSet(DatePicker view, int year, int monthOfYear, int dayOfMonth) {
            Calendar cur = Calendar.getInstance();
            cur.set(year, monthOfYear, dayOfMonth);
            Date date = cur.getTime();
            attached.onFromDateSet(AppUtil.eraseTime(date));
        }
    }
}
