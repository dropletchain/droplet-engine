package ch.ethz.blockadit.util;

import android.content.Context;

import java.sql.Time;
import java.util.Date;
import java.util.List;
import java.util.Set;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.blockadit.Datatype;
import ch.ethz.blockadit.blockadit.TalosAPIFactory;
import ch.ethz.blockadit.blockadit.BlockAditFitbitAPI;
import ch.ethz.blockadit.fitbitapi.FitbitAPI;
import ch.ethz.blockadit.fitbitapi.FitbitAPIException;
import ch.ethz.blockadit.fitbitapi.TokenInfo;
import ch.ethz.blockadit.fitbitapi.model.CaloriesQuery;
import ch.ethz.blockadit.fitbitapi.model.Dataset;
import ch.ethz.blockadit.fitbitapi.model.DistQuery;
import ch.ethz.blockadit.fitbitapi.model.FloorQuery;
import ch.ethz.blockadit.fitbitapi.model.HeartQuery;
import ch.ethz.blockadit.fitbitapi.model.StepsQuery;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.storage.ChunkData;

import static ch.ethz.blockadit.blockadit.Datatype.CALORIES;
import static ch.ethz.blockadit.blockadit.Datatype.DISTANCE;
import static ch.ethz.blockadit.blockadit.Datatype.FLOORS;
import static ch.ethz.blockadit.blockadit.Datatype.STEPS;


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

public class Synchronizer {

    private BlockAditFitbitAPI talosApi;

    private FitbitAPI fitbit;

    private BlockIDComputer computer;

    private Set<Datatype> types;

    public Synchronizer(IBlockAditStream con, TokenInfo token, Set<Datatype> types) {
        talosApi = TalosAPIFactory.createAPI(con);
        fitbit = new FitbitAPI(token);
        this.types = types;
        computer = new BlockIDComputer(talosApi.getStream().getStartTimestamp(),
                talosApi.getStream().getInterval());
    }

    private static void transferData(ChunkData[] chunks, java.sql.Date dateSql, List<Dataset> datasets) {
        for(Dataset dataSet : datasets) {
            Time time = Time.valueOf(dataSet.getTime());
            dateSql.getTime(); +
            module.insertDataset(u, datesql, time, Datatype.FLOORS.name(), dataSet.getValue());
        }
    }

    public void transferDataForDate(Date date, int numBlocks) {
        ChunkData[] chunkdata = new ChunkData[numBlocks];
        for (int iter=0; iter<chunkdata.length; iter++)
                chunkdata[iter] = new ChunkData();

        if (types.contains(Datatype.FLOORS)) {
            FloorQuery query = fitbit.getFloorsFromDate(date);
            String dateStr = query.activitiesFloors.iterator().next().getDateTime();
            java.sql.Date datesql = java.sql.Date.valueOf(dateStr);
        }
        if (types.contains(Datatype.CALORIES)) {
            CaloriesQuery query = fitbit.getCaloriesFromDate(date);
        }
        if (types.contains(Datatype.DISTANCE)) {
            DistQuery query = fitbit.getDistanceFromDate(date);
        }
        if (types.contains(Datatype.STEPS)) {
            StepsQuery query = fitbit.getStepsFromDate(date);
        }
        if (types.contains(Datatype.HEARTRATE)) {
            HeartQuery query = fitbit.getHearthRateFromDate(date);
        }
    }
}
