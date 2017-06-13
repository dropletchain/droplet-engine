package ch.ethz.dropletcam;

import android.app.Activity;
import android.content.Intent;
import android.graphics.BitmapFactory;
import android.graphics.drawable.BitmapDrawable;
import android.os.AsyncTask;
import android.support.v7.app.ActionBar;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageSwitcher;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.ViewSwitcher;

import org.bitcoinj.core.Address;
import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;
import java.util.Date;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.policy.PolicyClientException;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;
import ch.ethz.blokcaditapi.storage.chunkentries.PictureEntry;
import ch.ethz.dropletcam.util.DemoDataLoader;
import ch.ethz.dropletcam.util.DemoUser;

public class WebCam extends AppCompatActivity {

    private DemoUser user;
    private ImageView pictureView;
    private Button leftClick;
    private Button rightClick;
    private TextView title;

    private BlockAditStorage storage;
    private IBlockAditStream loadedStream = null;
    private int actual = -1;
    private AtomicInteger currentImage = new AtomicInteger(-1);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_web_cam);

        Intent creator = getIntent();
        String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
        String ownerString = creator.getExtras().getString(ActivitiesUtil.STREAM_OWNER_KEY);

        int streamID = creator.getExtras().getInt(ActivitiesUtil.STREAM_ID_KEY);
        this.user = DemoUser.fromString(userData);
        Address ownerAddr = Address.fromBase58(DemoUser.params, ownerString);

        try {
            storage = BlockaditStorageState.getStorageForUser(this.user);
        } catch (UnknownHostException | BlockStoreException | InterruptedException e) {
            e.printStackTrace();
        }


        pictureView = (ImageView) findViewById(R.id.webImage);
        title = (TextView) findViewById(R.id.title);
        leftClick = (Button) findViewById(R.id.leftClick);
        rightClick = (Button) findViewById(R.id.rightClick);
        leftClick.setVisibility(View.INVISIBLE);
        rightClick.setVisibility(View.INVISIBLE);
        title.setVisibility(View.INVISIBLE);

        loadStream(ownerAddr, streamID);
    }

    private int computeCurrentBLockid(long startTime, long interval) {
        long unixTime = System.currentTimeMillis() / 1000L;
        unixTime -= (interval + startTime);
        //return (int) (unixTime / interval);
        return 4;
    }

    private void loadStream(final Address owner, final int streamID) {
        new AsyncTask<Void, Integer, IBlockAditStream>() {
            @Override
            protected IBlockAditStream doInBackground(Void... params) {
                try {
                    return storage.getAccessStreamForID(owner, streamID);
                } catch (PolicyClientException | BlockAditStreamException e) {
                    e.printStackTrace();
                    return null;
                }
            }


            @Override
            protected void onPostExecute(IBlockAditStream streamRes) {
                super.onPostExecute(streamRes);
                if (streamRes==null)
                    return;
                actual = computeCurrentBLockid(streamRes.getStartTimestamp(), streamRes.getInterval());
                currentImage.set(actual);
                loadedStream = streamRes;
                loadImage(currentImage.get());
                leftClick.setVisibility(View.VISIBLE);
            }
        }.execute();
    }

    private void loadImage(final int blockId) {
        new AsyncTask<Void, Void, PictureEntry>() {
            @Override
            protected PictureEntry doInBackground(Void... params) {
                try {
                    List<Entry> entries = loadedStream.getEntriesForBlock(blockId);
                    if (entries.isEmpty() || !(entries.get(0) instanceof PictureEntry))
                        return null;
                    return (PictureEntry) entries.get(0);
                } catch (Exception e) {
                    e.printStackTrace();
                    return null;
                }
            }

            @Override
            protected void onPostExecute(PictureEntry entry) {
                super.onPostExecute(entry);
                if (entry == null)
                    return;
                byte[] image = entry.getPictureData();
                pictureView.setImageBitmap(BitmapFactory.decodeByteArray(image, 0, image.length));
                title.setVisibility(View.VISIBLE);
                title.setText(ActivitiesUtil.titleWeb.format(new Date(entry.getTimestamp() * 1000L)));
            }
        }.execute();
    }

    private Lock lock = new ReentrantLock(true);

    public void onLeftClick(View view) {
        if (currentImage.get() < 0)
            return;

        lock.lock();
        try {
            int currentIdx = currentImage.get();
            if (currentIdx == 1) {
                leftClick.setVisibility(View.INVISIBLE);
            } else if (currentIdx == actual) {
                rightClick.setVisibility(View.VISIBLE);
            }

            int id = currentImage.decrementAndGet();
            loadImage(id);
        } finally {
            lock.unlock();
        }
    }

    public void onRightClick(View view) {
        if (currentImage.get() < 0)
            return;

        lock.lock();
        try {
            int currentIdx = currentImage.get();
            if (currentIdx == actual - 1) {
                rightClick.setVisibility(View.INVISIBLE);
            } else if (currentIdx == 0) {
                leftClick.setVisibility(View.VISIBLE);
            }

            int id = currentImage.incrementAndGet();
            loadImage(id);
        } finally {
            lock.unlock();
        }
    }
}
