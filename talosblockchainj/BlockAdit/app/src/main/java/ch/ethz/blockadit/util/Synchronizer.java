package ch.ethz.blockadit.util;

import java.sql.Time;
import java.util.Date;
import java.util.List;
import java.util.Set;

import ch.ethz.blockadit.blockadit.BlockAditFitbitAPI;
import ch.ethz.blockadit.blockadit.Datatype;
import ch.ethz.blockadit.blockadit.TalosAPIFactory;
import ch.ethz.blockadit.fitbitapi.FitbitAPI;
import ch.ethz.blockadit.fitbitapi.TokenInfo;
import ch.ethz.blockadit.fitbitapi.model.CaloriesQuery;
import ch.ethz.blockadit.fitbitapi.model.Dataset;
import ch.ethz.blockadit.fitbitapi.model.DistQuery;
import ch.ethz.blockadit.fitbitapi.model.DoubleDataSet;
import ch.ethz.blockadit.fitbitapi.model.FloorQuery;
import ch.ethz.blockadit.fitbitapi.model.HeartQuery;
import ch.ethz.blockadit.fitbitapi.model.StepsQuery;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.storage.ChunkData;
import ch.ethz.blokcaditapi.storage.chunkentries.DoubleEntry;
import ch.ethz.blokcaditapi.storage.chunkentries.IntegerEntry;

import static ch.ethz.blockadit.util.AppUtil.transformDates;


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

    private static final int DAILY_SECONDS = 86400;

    private static void transferData(ChunkData[] chunks, java.sql.Date dateSql, List<Dataset> datasets, Datatype type) {
        int interval = DAILY_SECONDS / chunks.length;
        for(Dataset dataSet : datasets) {
            Time time = Time.valueOf(dataSet.getTime());
            long timeMs = transformDates(dateSql, time).getTime() - dateSql.getTime();
            int id =(int) ((timeMs *1000) / interval);
            chunks[id].addEntry(new IntegerEntry(timeMs * 1000, type.getDisplayRep(), dataSet.getValue()));
        }
    }

    private static void transferDataDouble(ChunkData[] chunks, java.sql.Date dateSql, List<DoubleDataSet> datasets, Datatype type) {
        int interval = DAILY_SECONDS / chunks.length;
        for(DoubleDataSet dataSet : datasets) {
            Time time = Time.valueOf(dataSet.getTime());
            long timeMs = transformDates(dateSql, time).getTime() - dateSql.getTime();
            int id =(int) ((timeMs *1000) / interval);
            chunks[id].addEntry(new DoubleEntry(timeMs * 1000, type.getDisplayRep(), dataSet.getValue()));
        }
    }

    private int[] computeBlockIDs(Date date, int numBlocks) {
        int startId = this.computer.getIdForDate(date);
        int[] res = new int[numBlocks];
        for (int i=0; i<res.length; i++) {
            res[i] = i + startId;
        }
        return res;
    }

    public void transferDataForDate(Date date, int numBlocks) throws BlockAditStreamException {
        ChunkData[] chunkdata = new ChunkData[numBlocks];
        int[] blockIds = this.computeBlockIDs(date, numBlocks);
        for (int iter=0; iter<chunkdata.length; iter++)
                chunkdata[iter] = new ChunkData();

        if (types.contains(Datatype.FLOORS)) {
            FloorQuery query = fitbit.getFloorsFromDate(date);
            String dateStr = query.activitiesFloors.iterator().next().getDateTime();
            java.sql.Date datesql = java.sql.Date.valueOf(dateStr);
            transferData(chunkdata, datesql, query.activitiesFloorsIntraday.getDataset(), Datatype.FLOORS);
        }

        if (types.contains(Datatype.CALORIES)) {
            CaloriesQuery query = fitbit.getCaloriesFromDate(date);
            String dateStr = query.activitiesCalories.iterator().next().getDateTime();
            java.sql.Date datesql = java.sql.Date.valueOf(dateStr);
            transferDataDouble(chunkdata, datesql, query.activitiesCaloriesIntraday.getDataset(), Datatype.CALORIES);
        }

        if (types.contains(Datatype.DISTANCE)) {
            DistQuery query = fitbit.getDistanceFromDate(date);
            String dateStr = query.activitiesDistance.iterator().next().getDateTime();
            java.sql.Date datesql = java.sql.Date.valueOf(dateStr);
            transferDataDouble(chunkdata, datesql, query.activitiesDistanceIntraday.getDataset(), Datatype.DISTANCE);
        }

        if (types.contains(Datatype.STEPS)) {
            StepsQuery query = fitbit.getStepsFromDate(date);
            String dateStr = query.activitiesSteps.iterator().next().getDateTime();
            java.sql.Date datesql = java.sql.Date.valueOf(dateStr);
            transferData(chunkdata, datesql, query.activitiesStepsIntraday.getDataset(), Datatype.STEPS);
        }
        if (types.contains(Datatype.HEARTRATE)) {
            HeartQuery query = fitbit.getHearthRateFromDate(date);
            String dateStr = query.getActivitiesHeart().iterator().next().getDateTime();
            java.sql.Date datesql = java.sql.Date.valueOf(dateStr);
            transferDataDouble(chunkdata, datesql, query.getActivitiesHeartIntraday().getDataset(), Datatype.HEARTRATE);
        }
        this.talosApi.storeChunks(blockIds, chunkdata);
    }
}
