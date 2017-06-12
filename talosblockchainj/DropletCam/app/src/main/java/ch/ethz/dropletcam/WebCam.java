package ch.ethz.dropletcam;

import android.app.Activity;
import android.content.Intent;
import android.graphics.BitmapFactory;
import android.os.AsyncTask;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.ImageView;

import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;
import ch.ethz.blokcaditapi.storage.chunkentries.PictureEntry;
import ch.ethz.dropletcam.util.DemoDataLoader;
import ch.ethz.dropletcam.util.DemoUser;

public class WebCam extends AppCompatActivity {

    private DemoUser user;
    private ImageView pictureView;

    private AtomicBoolean loaded = new AtomicBoolean(false);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_web_cam);
        DemoDataLoader loader = new DemoDataLoader(this);
        List<DemoUser> users = loader.loadDemoUsers();
        user = users.get(0);
        pictureView = (ImageView) findViewById(R.id.webImage);
        loadStorage();
    }

    private void loadStorage() {
        if (!loaded.get()) {
            Intent i = new Intent(this, LoadingBlockchainActivity.class);
            i.putExtra(ActivitiesUtil.DEMO_USER_KEY, user.toString());
            startActivityForResult(i, 1);
        }
    }

    public void onLoadImg(View view) {
        BlockAditStorage storage = null;
        try {
            storage = BlockaditStorageState.getStorageForUser(this.user);
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }
        final BlockAditStorage api_storage = storage;
        final int blockID = 6;
        new AsyncTask<Void, Void, byte[]>() {
            @Override
            protected byte[] doInBackground(Void... params) {
                try {
                    List<IBlockAditStream> streams = api_storage.getAccessableStreams();
                    if (streams.isEmpty())
                        return null;
                    IBlockAditStream stream = streams.get(0);
                    List<Entry> entries = stream.getEntriesForBlock(blockID);
                    if (entries.isEmpty() || !(entries.get(0) instanceof PictureEntry))
                        return null;
                    PictureEntry entry = (PictureEntry) entries.get(0);
                    return entry.getPictureData();
                } catch (Exception e) {
                    e.printStackTrace();
                    return null;
                }
            }

            @Override
            protected void onPostExecute(byte[] image) {
                super.onPostExecute(image);
                if (image == null)
                    return;
                pictureView.setImageBitmap(BitmapFactory.decodeByteArray(image, 0, image.length));
            }
        }.execute();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 1) {
            if (resultCode == Activity.RESULT_OK) {
                loaded.set(true);
            }
            if (resultCode == Activity.RESULT_CANCELED) {
                loaded.set(false);
                Log.e("Streams", "Creation Failed :(");
            }
        }
    }
}
