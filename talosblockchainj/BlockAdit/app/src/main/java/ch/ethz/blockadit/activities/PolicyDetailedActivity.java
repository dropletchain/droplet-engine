package ch.ethz.blockadit.activities;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.RelativeLayout;
import android.widget.TextView;

import com.daimajia.swipe.adapters.ArraySwipeAdapter;

import org.bitcoinj.core.Address;
import org.bitcoinj.core.InsufficientMoneyException;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.util.AppUtil;
import ch.ethz.blockadit.util.BlockaditStorageState;
import ch.ethz.blockadit.util.DemoDataLoader;
import ch.ethz.blockadit.util.DemoUser;
import ch.ethz.blockadit.util.StreamIDType;
import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.policy.PolicyClientException;

public class PolicyDetailedActivity extends AppCompatActivity {

    private TextView ownerView;
    private TextView tsFrom;
    private TextView tsInterval;
    private ImageView qrView;
    private ProgressBar progress;
    private DemoUser user;

    private ListView sharesView;

    private BlockAditStorage storage;
    private IBlockAditStream stream = null;

    private String[] intervalValues = null;
    private ArrayList<DemoUser> users;

    ImageView stepsView;
    ImageView calView;
    ImageView floorView;
    ImageView distView;
    ImageView heartView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_policy_detailed);

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

        intervalValues = getResources().getStringArray(R.array.intervals);

        Address ownerAddr =  Address.fromBase58(DemoUser.params, ownerString);
        loadQR(ownerAddr);

        ownerView = (TextView) findViewById(R.id.ownerNearQr);
        ownerView.setText(String.format("Owner\n%s", user.getOwnerAddress().toString()));
        qrView = (ImageView) findViewById(R.id.qrView);
        sharesView = (ListView) findViewById(R.id.shareItems);
        tsFrom = (TextView) findViewById(R.id.startTimestamp);
        tsInterval = (TextView) findViewById(R.id.intervalTimestamp);
        progress = (ProgressBar) findViewById(R.id.progressLoadDetailed);

        DemoDataLoader loader = new DemoDataLoader(this);
        users = loader.loadDemoUsers();

        loadStream(ownerAddr, streamID);

        stepsView = (ImageView) findViewById(R.id.listStepIcon);
        calView = (ImageView) findViewById(R.id.listCalIcon);
        floorView = (ImageView) findViewById(R.id.listFloorIcon);
        distView = (ImageView) findViewById(R.id.listDistIcon);
        heartView = (ImageView) findViewById(R.id.listHeartIcon);
    }

    private void loadQR(final Address address) {
        new AsyncTask<Void, Integer, Bitmap>() {
            @Override
            protected Bitmap doInBackground(Void... params) {
                return AppUtil.createQRCode(address.toString(), 256);
            }

            @Override
            protected void onPostExecute(Bitmap qrImage) {
                super.onPostExecute(qrImage);
                if(qrImage != null ) {
                    qrView.setImageBitmap(qrImage);
                }
            }
        }.execute();
    }

    private void loadStream(final Address owner, final int streamID) {
        new AsyncTask<Void, Integer, IBlockAditStream>() {
            @Override
            protected void onPreExecute() {
                super.onPreExecute();
                progress.setVisibility(View.VISIBLE);
            }

            @Override
            protected IBlockAditStream doInBackground(Void... params) {
                try {
                    return storage.getStreamForID(owner, streamID);
                } catch (PolicyClientException | BlockAditStreamException e) {
                    e.printStackTrace();
                    return null;
                }
            }

            private String intervalToString(long interval) {
                int id = (int) (interval/3600);
                if(id == 24)
                    return intervalValues[0];
                if(id == 12)
                    return intervalValues[1];
                if(id == 6)
                    return intervalValues[2];
                return String.valueOf(id);
            }

            @Override
            protected void onPostExecute(IBlockAditStream streamRes) {
                super.onPostExecute(streamRes);
                if(streamRes != null) {
                    stream = streamRes;
                    Date dateFrom = new Date(stream.getStartTimestamp() * 1000);
                    tsFrom.setText(String.format("Start: %s", ActivitiesUtil.titleFormat.format(dateFrom)));
                    tsInterval.setText(String.format("Interval: %s", intervalToString(stream.getInterval())));
                    loadShares(stream, true);
                    StreamIDType typesStrem = new StreamIDType(streamRes.getStreamId());

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
                }

                progress.setVisibility(View.INVISIBLE);
            }
        }.execute();
    }

    private void loadShares(final IBlockAditStream streamIn, final boolean doLocal) {
        new AsyncTask<Void, Integer, List<Address>>() {
            @Override
            protected void onPreExecute() {
                super.onPreExecute();
                progress.setVisibility(View.VISIBLE);
            }

            @Override
            protected List<Address> doInBackground(Void... params) {
                try {
                    if(doLocal)
                        return streamIn.getSharesLocal();
                    else
                        return streamIn.getShares();
                } catch (PolicyClientException  e) {
                    e.printStackTrace();
                    return new ArrayList<>();
                }
            }
            @Override
            protected void onPostExecute(List<Address> streamRes) {
                super.onPostExecute(streamRes);
                ArrayList<DemoUser> shares = new ArrayList<>();
                ArrayList<Date> dates = new ArrayList<>();
                Date defaultDate = new Date(streamIn.getStartTimestamp() * 1000);
                for(Address addr : streamRes) {
                    for (DemoUser user : users) {
                        if (user.getShareAddress().equals(addr)) {
                            shares.add(user);
                            dates.add(defaultDate);
                            break;
                        }
                    }
                }

                ShareUserAdapter adapter = new ShareUserAdapter(getApplicationContext(),
                        shares, dates, new DemoDataLoader(getApplicationContext()), streamIn);
                sharesView.setAdapter(adapter);
                progress.setVisibility(View.INVISIBLE);
            }
        }.execute();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 1) {
            if(resultCode == Activity.RESULT_OK){
                loadShares(stream, true);
            }
            if (resultCode == Activity.RESULT_CANCELED) {
                Log.e("Streams", "Creation Failed :(");
            }
        }
    }

    public void onAddShare(View v) {
        if(stream != null) {
            Intent i = new Intent(this, AddShareActivity.class);
            i.putExtra(ActivitiesUtil.DEMO_USER_KEY, this.user.toString());
            i.putExtra(ActivitiesUtil.STREAM_OWNER_KEY, stream.getOwner().toString());
            i.putExtra(ActivitiesUtil.STREAM_ID_KEY, stream.getStreamId());
            startActivityForResult(i, 1);
        }
    }

    private void erasejob(DemoUser user) {

    }


    public static class ShareUserAdapter extends ArraySwipeAdapter<DemoUser> {

        private ArrayList<DemoUser> items;
        private ArrayList<Date> fromDates;
        private DemoDataLoader loader;
        private IBlockAditStream stream;

        public ShareUserAdapter(Context context, ArrayList<DemoUser> items, ArrayList<Date> fromDates, DemoDataLoader loader, IBlockAditStream stream) {
            super(context, R.layout.list_share_user_layout, items);
            this.items = items;
            this.loader = loader;
            this.fromDates = fromDates;
            this.stream = stream;
        }

        private void removeShare(final Address share) {
            new AsyncTask<Void, Integer, Boolean>() {
                @Override
                protected Boolean doInBackground(Void... params) {
                    try {
                        stream.getPolicyManipulator().removeShare(share);
                    } catch (InsufficientMoneyException | PolicyClientException e) {
                        e.printStackTrace();
                        return false;
                    }
                    return true;
                }

                @Override
                protected void onPostExecute(Boolean ok) {
                    super.onPostExecute(ok);
                }
            }.execute();
        }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            final int positionTemp = position;
            final DemoUser item = items.get(positionTemp);
            if (convertView == null) {
                convertView = LayoutInflater.from(getContext()).inflate(R.layout.list_share_user_layout, parent, false);
            }
            TextView shareUserNameView = (TextView) convertView.findViewById(R.id.shareUserName);
            TextView shareUseAddressView = (TextView) convertView.findViewById(R.id.shareUserAddress);

            int imgId = this.loader.getImgResourceForUser(item);
            imgId = imgId == 0 ? R.mipmap.ic_launcher : imgId;
            ImageView imgView = (ImageView) convertView.findViewById(R.id.personimageShare);
            RelativeLayout layout = (RelativeLayout) convertView.findViewById(R.id.shareUserrelLayoutList);
            LinearLayout linearLayout = (LinearLayout) convertView.findViewById(R.id.shareUserlinlay);

            layout.setBackgroundColor(getContext().getResources().getColor(R.color.lightBG));
            linearLayout.setBackgroundColor(getContext().getResources().getColor(R.color.heavierBG));

            Button button = (Button) convertView.findViewById(R.id.deleteButton);
            button.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    removeShare(item.getShareAddress());
                    items.remove(positionTemp);
                    notifyDataSetChanged();
                }
            });


            shareUserNameView.setText(item.getName());
            shareUseAddressView.setText(item.getShareAddress().toString());
            shareUseAddressView.setTextColor(Color.BLACK);
            shareUserNameView.setTextColor(Color.BLACK);
            imgView.setBackgroundResource(imgId);

            Date cur = fromDates.get(position);
            TextView fromDateView = (TextView) convertView.findViewById(R.id.shareUserFromDate);
            fromDateView.setText(String.format("From: %s", ActivitiesUtil.titleFormat.format(cur)));
            return convertView;
        }

        @Override
        public int getSwipeLayoutResourceId(int position) {
            return R.id.swipeSharedUser;
        }
    }
}
