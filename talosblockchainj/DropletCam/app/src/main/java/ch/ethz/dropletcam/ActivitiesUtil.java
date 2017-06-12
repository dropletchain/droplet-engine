package ch.ethz.dropletcam;

import java.text.SimpleDateFormat;

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

public class ActivitiesUtil {

    static final int RESULT_OK = 1;
    static final int RESULT_ERROR = 2;

    static final String QR_SELECT_STRING_KEY = "selected_qr_string";
    static final String SELECTED_USER_KEY = "selectedUser";
    static final String DEMO_USER_KEY = "demo_user";
    static final String STREAM_OWNER_KEY = "stream_owner_key";
    static final String STREAM_ID_KEY = "stream_id_key";
    static final String TRANSACTION_ID_KEY = "transaction";
    static final String IS_SHARED_KEY = "is_shared";

    static final String DATATYPE_KEY = "type";
    static final String DETAIL_DATE_KEY = "detail_date";

    static final String SHARED_PREF_LAST_DOWNLOAD_KEY = "last_downlaod";

    static final SimpleDateFormat dateFormat = new SimpleDateFormat("E");
    static final SimpleDateFormat titleFormat = new SimpleDateFormat("dd.MM.yyyy");
    static final SimpleDateFormat timeFormat = new SimpleDateFormat("HH");
    static final SimpleDateFormat keyFormat = new SimpleDateFormat("HH:mm:ss");

}
