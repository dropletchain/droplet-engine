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
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.DatePicker;
import android.widget.ProgressBar;
import android.widget.RadioButton;
import android.widget.Spinner;

import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.Calendar;
import java.util.Date;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoUser;
import ch.ethz.blockadit.util.StreamIDType;
import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.policy.PolicyClientException;

import static ch.ethz.blockadit.activities.PolicySettingsActivity.temporaryStreams;

public class CreateStream extends AppCompatActivity {

    private RadioButton stepsRadio;
    private RadioButton floorRadio;
    private RadioButton distRadio;
    private RadioButton calRadio;
    private RadioButton heartRadio;

    private Button fromDate;
    private Spinner interval;

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

        stepsRadio = (RadioButton) findViewById(R.id.radioSteps);
        floorRadio = (RadioButton) findViewById(R.id.radioFloors);
        distRadio = (RadioButton) findViewById(R.id.radioDistance);
        calRadio = (RadioButton) findViewById(R.id.radioCalendar);
        heartRadio = (RadioButton) findViewById(R.id.radioHeart);

        fromDate = (Button) findViewById(R.id.fromDateSelect);
        interval = (Spinner) findViewById(R.id.spinnerInterval);

        bar = (ProgressBar) findViewById(R.id.progressCreateStream);
        bar.setVisibility(View.INVISIBLE);

        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(this, R.array.intervals, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        interval.setAdapter(adapter);
        interval.setSelection(0);
        interval.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                curInterval = 3600 * (24/(1<<position));
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {
                interval.setSelection(0);
            }

        });
        curInterval = 84600;

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

        if (curDate==null)
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
                    setResult(Activity.RESULT_CANCELED,returnIntent);
                    finish();
                } else {
                    temporaryStreams.add(stream);
                    Intent returnIntent = new Intent();
                    setResult(Activity.RESULT_OK,returnIntent);
                    finish();
                }

            }
        }.execute();
    }

    public void onFromDateSet(Date date) {
        curDate = date;
        fromDate.setText(ActivitiesUtil.titleFormat.format(date));
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

            return new DatePickerDialog(getActivity(),this,year,month,day);
        }

        @Override
        public void onDateSet(DatePicker view, int year, int monthOfYear, int dayOfMonth) {
            Calendar cur = Calendar.getInstance();
            cur.set(year, monthOfYear, dayOfMonth);
            Date date = cur.getTime();
            attached.onFromDateSet(date);
        }
    }
}
