package ch.ethz.blockadit.activities;

import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.widget.Button;

import ch.ethz.blockadit.R;


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

public class StartActivity extends AppCompatActivity  {

    private static final int RC_SIGN_IN = 9001;


    private Button logoutButton = null;
    private static boolean logInState = false;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        logoutButton = (Button) findViewById(R.id.logbutton);
        updateUI(logInState);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
    }



    private void updateUI(boolean signedIn) {
        if (signedIn) {
            logoutButton.setText("Logout");
            findViewById(R.id.syndata).setVisibility(View.VISIBLE);
            findViewById(R.id.mycloud).setVisibility(View.VISIBLE);
            findViewById(R.id.fitbitimg).setVisibility(View.VISIBLE);
            findViewById(R.id.cloudimg).setVisibility(View.VISIBLE);
            findViewById(R.id.userimg).setVisibility(View.VISIBLE);
            logInState = true;
        } else {
            logoutButton.setText("LogIn");
            findViewById(R.id.syndata).setVisibility(View.INVISIBLE);
            findViewById(R.id.mycloud).setVisibility(View.INVISIBLE);
            findViewById(R.id.fitbitimg).setVisibility(View.INVISIBLE);
            findViewById(R.id.cloudimg).setVisibility(View.INVISIBLE);
            findViewById(R.id.userimg).setVisibility(View.INVISIBLE);
            logInState = false;
        }
    }

    public void onSyncData(View v) {
        Intent intent = new Intent(this, FitbitSync.class);
        startActivity(intent);
    }

    public void onMyCloud(View v) {
        Intent intent = new Intent(this, CloudSelectActivity.class);
        startActivity(intent);
    }

    public void onLogButton(View v) {
    }


}
