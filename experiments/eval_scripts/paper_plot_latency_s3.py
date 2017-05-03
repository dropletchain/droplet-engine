import os
import re

import sqlite3

import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

db_pattern = re.compile("local_dht_benchmark_par_fetch_k(.*)_a(.*)_n(.*)_l(.*)_t(.*).db")

data_path_s3 = "../data/local_s3_benchmark/local_s3_benchmark.db"

FETCH_S3_DATA_PLAIN = "SELECT time_s3_store_chunk, time_s3_get_chunk FROM CLIENT_S3_SYNC_PLAIN WHERE _rowid_>=? AND _rowid_<?;"
FETCH_S3_DATA_TALOS = "SELECT time_s3_store_chunk, time_s3_get_chunk FROM CLIENT_S3_SYNC_TALOS WHERE _rowid_>=? AND _rowid_<?;"


def fetch_s3_data_from_db(db_path, from_row, to_row):
    with sqlite3.connect(db_path) as conn:
        plain_data = np.asarray(conn.execute(FETCH_S3_DATA_PLAIN, (from_row, to_row)).fetchall())
        talos_data = np.asarray(conn.execute(FETCH_S3_DATA_TALOS, (from_row, to_row)).fetchall())
        return plain_data, talos_data


def plot_s3_latency():

    s3_plain_data, s3_enc_data = fetch_s3_data_from_db(data_path_s3, 0, 100)

    def compute_latency(data):
        avg_latency = np.average(data, axis=0)
        std_latency = np.std(data, axis=0)
        return avg_latency, std_latency


    #########
    # PLOTS #
    #########

    #---------------------------- GLOBAL VARIABLES --------------------------------#
    # figure settings
    fig_width_pt = 300.0                        # Get this from LaTeX using \showthe
    inches_per_pt = 1.0/72.27*2                 # Convert pt to inches
    golden_mean = ((math.sqrt(5)-1.0)/2.0)*.8   # Aesthetic ratio
    fig_width = fig_width_pt*inches_per_pt      # width in inches
    fig_height =(fig_width*golden_mean)           # height in inches
    fig_size = [fig_width,fig_height/1.22]

    params = {'backend': 'ps',
        'axes.labelsize': 18,
        'legend.fontsize': 16,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'font.size': 16,
        'figure.figsize': fig_size,
        'font.family': 'times new roman'}

    pdf_pages = PdfPages('../plots/paper_s3_latency.pdf')
    fig_size = [fig_width, fig_height / 1.2]

    plt.rcParams.update(params)
    plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
    plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3

    avg_plain_l, std_plain_l = compute_latency(s3_plain_data)
    avg_enc_l, std_enc_l = compute_latency(s3_plain_data)

    avg_data = np.vstack((avg_plain_l, avg_enc_l))
    std_data = np.vstack((std_plain_l, std_enc_l))

    ind = np.arange(2)
    width = 0.4

    colours = ['0.3', '0.3', '0.7', '0.7']
    hatch_style='\\\\\\\\'

    f, ax1 = plt.subplots()

    ax1.grid(True, linestyle=':', color='0.8', zorder=0, axis='y')
    rects1 = ax1.bar(ind, avg_data[:, 0], width, color=colours[0], yerr=std_data[:, 0], error_kw=dict(ecolor='0.6', lw=1, capsize=4, capthick=1), zorder=3)
    rects2 = ax1.bar(ind + width,  avg_data[:, 1], width, hatch=hatch_style, color=colours[1], yerr=std_data[:, 1], error_kw=dict(ecolor='0.6', lw=1, capsize=5, capthick=1), zorder=3)


    ax1.set_ylabel("Time [ms]")
    ax1.set_xticks(ind + width)
    ax1.set_xticklabels(["plain", "check"])
    ax1.set_xlabel("S3")

    #ax1.legend((rects1[0], rects2[0], rects3[0], rects4[0]), ('Store', 'Get', 'Routing Store', 'Routing Get'), loc="upper left", ncol=2)
    ax1.legend((rects1[0], rects2[0]), ('Store', 'Get'), bbox_to_anchor=(-0.02, 1.00, 1., .102), loc=3, ncol=4, columnspacing=1)

    #handletextpad=0.5, labelspacing=0.2, borderaxespad=0.2, borderpad=0.3)

    #f.suptitle("RTT-%d average latency DHT operations" % latency, fontsize=24, y=1.02)
    ax1.set_ylim([0, 205])
    ax1.yaxis.set_ticks(np.arange(0, 201, 20.0))


    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()

if __name__ == "__main__":
    plot_s3_latency()
