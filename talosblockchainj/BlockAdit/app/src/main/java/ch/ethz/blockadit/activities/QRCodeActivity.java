package ch.ethz.blockadit.activities;

import android.content.Intent;
import android.graphics.Bitmap;
import android.os.AsyncTask;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.ImageView;

import org.bitcoinj.core.Address;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.util.AppUtil;

public class QRCodeActivity extends AppCompatActivity {

    private ImageView qrCodeView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_qrcode);

        Intent creator = getIntent();
        String dataString = creator.getExtras().getString(ActivitiesUtil.QR_SELECT_STRING_KEY);
        qrCodeView = (ImageView) findViewById(R.id.qrCodeImageView);

        loadQR(dataString);
    }

    private void loadQR(final String data) {
        new AsyncTask<Void, Integer, Bitmap>() {
            @Override
            protected Bitmap doInBackground(Void... params) {
                return AppUtil.createQRCode(data, 512);
            }

            @Override
            protected void onPostExecute(Bitmap qrImage) {
                super.onPostExecute(qrImage);
                if(qrImage != null ) {
                    qrCodeView.setImageBitmap(qrImage);
                }
            }
        }.execute();
    }
}
