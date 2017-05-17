package ch.ethz.blockadit.blockadit;

import android.content.Context;

import java.sql.Date;
import java.sql.Time;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import ch.ethz.blockadit.R;
import ch.ethz.blockadit.activities.CloudSelectActivity;
import ch.ethz.blockadit.blockadit.model.DataEntry;
import ch.ethz.blockadit.blockadit.model.DataEntryAgrDate;
import ch.ethz.blockadit.blockadit.model.DataEntryAgrTime;
import ch.ethz.blockadit.fitbitapi.model.CaloriesQuery;
import ch.ethz.blockadit.fitbitapi.model.Dataset;
import ch.ethz.blockadit.fitbitapi.model.DistQuery;
import ch.ethz.blockadit.fitbitapi.model.DoubleDataSet;
import ch.ethz.blockadit.fitbitapi.model.FloorQuery;
import ch.ethz.blockadit.fitbitapi.model.HeartQuery;
import ch.ethz.blockadit.fitbitapi.model.StepsQuery;
import ch.ethz.blockadit.util.AppUtil;
import ch.ethz.blockadit.util.BlockIDComputer;
import ch.ethz.blokcaditapi.BlockAditStorage;
import ch.ethz.blokcaditapi.BlockAditStreamException;
import ch.ethz.blokcaditapi.IBlockAditStream;
import ch.ethz.blokcaditapi.storage.ChunkData;
import ch.ethz.blokcaditapi.storage.chunkentries.Entry;

import static android.os.Build.VERSION_CODES.M;


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

public class BlockAditFitbitAPI {

    private IBlockAditStream stream;
    private BlockIDComputer blockIDComp;

    public BlockAditFitbitAPI(IBlockAditStream stream) {
        this.stream = stream;
        blockIDComp = new BlockIDComputer();
    }

    public IBlockAditStream getStream() {
        return stream;
    }

    public void storeChunks(int[] blockIds, ChunkData[] data) {
        if (blockIds.length != data.length)
            throw new IllegalArgumentException("Arrays do not have the same size");

        for (int idx=0; idx < blockIds.length; idx++) {
            this.stream.storeChunk(blockIds[idx], data[idx]);
        }
    }

    public ArrayList<DataEntryAgrDate> getAgrDataPerDate(Date from, Date to, Datatype type) throws BlockAditStreamException {
        long fromUnix = blockIDComp.dateToUnix(from);
        long toUnix = blockIDComp.dateToUnix(to);
        List<Entry> entries = stream.getRange(fromUnix, toUnix);
        ArrayList<DataEntryAgrDate> data = new ArrayList<>();
        List<Aggregator.DateSummary> byDate = Aggregator.splitByDate(entries, type);
        for (Aggregator.DateSummary summary : byDate) {
            double[] result = Aggregator.aggregateDataForType(summary.entries, type);
            data.add(DataEntry.createFrom(summary.date, result[0]));
        }
        return data;
    }

    public ArrayList<DataEntryAgrTime> getAgrDataForDate(Date curDate, Datatype type) throws BlockAditStreamException {
        long fromUnix = blockIDComp.dateToUnix(curDate);
        Calendar c = Calendar.getInstance();
        c.setTime(curDate);
        c.add(Calendar.DATE, 1);
        long toUnix =  blockIDComp.dateToUnix(c.getTime());
        List<Entry> entries = stream.getRange(fromUnix, toUnix);
        ArrayList<DataEntryAgrTime> data = new ArrayList<>();
        List<Aggregator.DateTimeSummary> byDate = Aggregator.splitByGranularity(entries, curDate, 15 * 60, type);
        for (Aggregator.DateTimeSummary summary : byDate) {
            double[] result = Aggregator.aggregateDataForType(summary.entries, type);
            data.add(DataEntry.createTimeFrom(summary.time, result[0]));
        }
        return data;
    }

    public ArrayList<CloudSelectActivity.CloudListItem> getCloudListItems(Date today) throws BlockAditStreamException {
        ArrayList<CloudSelectActivity.CloudListItem> items = new ArrayList<>();
        HashMap<Datatype, CloudSelectActivity.CloudListItem> mappings = new HashMap<>();
        long fromUnix = blockIDComp.dateToUnix(today);
        Calendar c = Calendar.getInstance();
        c.setTime(today);
        c.add(Calendar.DATE, 1);
        long toUnix =  blockIDComp.dateToUnix(c.getTime());
        List<Entry> entries = stream.getRange(fromUnix, toUnix);
        Map<Datatype, List<Entry>> dataTypeToEntry = Aggregator.splitByDatype(entries);
        for (Map.Entry<Datatype, List<Entry>> mapping :dataTypeToEntry.entrySet()) {
            double[] aggrData = Aggregator.aggregateDataForType(mapping.getValue(), mapping.getKey());
            Datatype type = mapping.getKey();
            mappings.put(type, new CloudSelectActivity.CloudListItem(type, type.formatValue(aggrData[0])));
        }
        for(Datatype in : Datatype.values()) {
            if(mappings.containsKey(in)) {
                items.add(mappings.get(in));
            } else {
                items.add(new CloudSelectActivity.CloudListItem(in, in.formatValue(0)));
            }
        }
        return items;
    }

}
