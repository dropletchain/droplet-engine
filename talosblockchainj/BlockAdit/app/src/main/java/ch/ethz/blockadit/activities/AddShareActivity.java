package ch.ethz.blockadit.activities;

import android.app.Activity;
import android.app.DatePickerDialog;
import android.app.Dialog;
import android.app.DialogFragment;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.DatePicker;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;
import android.widget.Spinner;
import android.widget.TextView;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.core.Transaction;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoDataLoader;
import ch.ethz.blockadit.util.DemoUser;
import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.policy.PolicyClientException;

import static ch.ethz.blockadit.activities.ActivitiesUtil.TRANSACTION_ID_KEY;
import static ch.ethz.blockadit.activities.PolicySettingsActivity.temporaryStreams;

public class AddShareActivity extends AppCompatActivity {

    Spinner shareSpinner;
    Button fromSelectButton;
    DemoUser user;
    BlockAditStorage storage;

    private ArrayList<DemoUser> users;

    private IBlockAditStream stream = null;
    private DemoUser selectedUser = null;
    private Date selectedDate = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_add_share);

        Intent creator = getIntent();
        String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
        String ownerString = creator.getExtras().getString(ActivitiesUtil.STREAM_OWNER_KEY);
        int streamID = creator.getExtras().getInt(ActivitiesUtil.STREAM_ID_KEY);

        this.user = DemoUser.fromString(userData);

        try {
            storage = BlockaditStorageState.getStorageForUser(this.user);
        } catch (UnknownHostException | BlockStoreException | InterruptedException e) {
            e.printStackTrace();
        }

        fromSelectButton = (Button) findViewById(R.id.fromDateSelect);
        shareSpinner = (Spinner) findViewById(R.id.spinnerShares);


        Address ownerAddr =  Address.fromBase58(DemoUser.params, ownerString);

        DemoDataLoader loader = new DemoDataLoader(this);
        users = loader.loadDemoUsers();

        loadStream(ownerAddr, streamID);
    }

    private void loadStream(final Address owner, final int streamID) {
        new AsyncTask<Void, Integer, IBlockAditStream>() {
            @Override
            protected IBlockAditStream doInBackground(Void... params) {
                try {
                    return storage.getStreamForID(owner, streamID);
                } catch (PolicyClientException | BlockAditStreamException e) {
                    e.printStackTrace();
                    return null;
                }
            }

            @Override
            protected void onPostExecute(IBlockAditStream streamRes) {
                super.onPostExecute(streamRes);
                if(streamRes != null) {
                    stream = streamRes;
                    loadShares(streamRes);
                    onFromDateSet(new Date(streamRes.getStartTimestamp() * 1000));
                }

            }
        }.execute();
    }

    private void loadShares(final IBlockAditStream streamIn) {
        new AsyncTask<Void, Integer, List<Address>>() {
            @Override
            protected List<Address> doInBackground(Void... params) {
                try {
                    return streamIn.getShares();
                } catch (PolicyClientException e) {
                    e.printStackTrace();
                    return new ArrayList<>();
                }
            }

            @Override
            protected void onPostExecute(List<Address> streamRes) {
                super.onPostExecute(streamRes);
                ArrayList<DemoUser> shareOptions = new ArrayList<DemoUser>();
                Address owner = streamIn.getOwner();
                for(DemoUser user : users) {
                    if(!streamRes.contains(user.getShareAddress())
                            && !user.getOwnerAddress().equals(owner))
                        shareOptions.add(user);
                }

                ShareUserListAdapter adapter =
                        new ShareUserListAdapter(getApplicationContext(),
                                shareOptions, new DemoDataLoader(getApplicationContext()));
                shareSpinner.setAdapter(adapter);
                if(!shareOptions.isEmpty())
                    selectedUser = shareOptions.get(0);
            }
        }.execute();
    }

    private void addShareBlockchain(final Address address) {
        new AsyncTask<Void, Integer, Transaction>() {
            @Override
            protected Transaction doInBackground(Void... params) {
                try {
                    return stream.getPolicyManipulator().addShare(address);
                } catch (InsufficientMoneyException | PolicyClientException e) {
                    e.printStackTrace();
                    return null;
                }
            }

            @Override
            protected void onPostExecute(Transaction streamRes) {
                super.onPostExecute(streamRes);
                if (streamRes == null) {
                    Intent returnIntent = new Intent();
                    setResult(Activity.RESULT_CANCELED, returnIntent);
                    finish();
                } else {
                    Bundle resData = new Bundle();
                    temporaryStreams.get(user.getName()).add(stream);
                    Intent returnIntent = new Intent();
                    setResult(Activity.RESULT_OK,returnIntent);
                    resData.putString(TRANSACTION_ID_KEY, streamRes.getHashAsString());
                    returnIntent.putExtras(resData);
                    finish();
                }

            }
        }.execute();
    }

    public void onAddShare(View v) {
        if(selectedUser == null || selectedDate == null || stream == null)
            return;
        addShareBlockchain(selectedUser.getShareAddress());

    }

    public void onFromDateSelect(View v) {
        DialogFragment newFragment = new FromDatePicker();
        newFragment.show(this.getFragmentManager(), "tag1");
    }

    public static class FromDatePicker extends DialogFragment implements DatePickerDialog.OnDateSetListener {

        private AddShareActivity attached;

        @Override
        public void onAttach(Activity activity) {
            super.onAttach(activity);
            attached = (AddShareActivity) activity;
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

    private void onFromDateSet(Date date) {
        this.selectedDate = date;
        fromSelectButton.setText(ActivitiesUtil.titleFormat.format(date));
    }

    public static class ShareUserListAdapter extends ArrayAdapter<DemoUser> {

        private ArrayList<DemoUser> items;
        private DemoDataLoader loader;

        public ShareUserListAdapter(Context context, ArrayList<DemoUser> items, DemoDataLoader loader) {
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
            demoUseAddressView.setText(item.getShareAddress().toString());
            demoUseAddressView.setTextColor(Color.BLACK);
            demoUserNameView.setTextColor(Color.BLACK);
            imgView.setBackgroundResource(imgId);

            return convertView;
        }

        @Override
        public View getDropDownView(int position, View convertView, ViewGroup parent) {
            return getView(position, convertView, parent);
        }
    }
}
