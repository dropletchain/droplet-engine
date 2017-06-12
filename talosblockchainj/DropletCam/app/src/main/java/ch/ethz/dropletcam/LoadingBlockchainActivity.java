package ch.ethz.dropletcam;

import android.app.Activity;
import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;

import org.bitcoinj.store.BlockStoreException;

import java.net.UnknownHostException;

import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.dropletcam.util.DemoUser;

public class LoadingBlockchainActivity extends AppCompatActivity {

    private DemoUser user;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_loading_blockchain);

        Intent creator = getIntent();
        String userData = creator.getExtras().getString(ActivitiesUtil.DEMO_USER_KEY);
        this.user = DemoUser.fromString(userData);
        loadStorage();
    }

    private void loadStorage() {
        new AsyncTask<Void, Integer, Boolean>() {
            @Override
            protected void onPreExecute() {
                super.onPreExecute();
            }

            @Override
            protected Boolean doInBackground(Void... params) {
                try {
                    BlockAditStorage storage = BlockaditStorageState.getStorageForUser(user);
                    if (storage != null)
                        storage.preLoadBlockchainState();
                } catch (UnknownHostException | BlockStoreException | InterruptedException e) {
                    e.printStackTrace();
                    return false;
                }
                return true;
            }

            @Override
            protected void onPostExecute(Boolean stream) {
                super.onPostExecute(stream);
                Intent returnIntent = new Intent();
                setResult(Activity.RESULT_OK, returnIntent);
                finish();
            }
        }.execute();
    }
}
