import os
import re

import sqlite3

import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

data_path_s3 = "../data/local_lamda_api_data/bench_lambda_api_r1.db"

FETCH_API_DATA_BASELINE = "SELECT time_api_store_chunk, time_api_get_chunk FROM LAMBDA_API_LATENCY_BASELINE WHERE _rowid_>=? AND _rowid_<?;"
FETCH_API_DATA_DROPLET = "SELECT time_api_store_chunk, time_api_get_chunk FROM LAMBDA_API_LATENCY_DROPLET WHERE _rowid_>=? AND _rowid_<?;"

FETCH_API_DATA_BASELINE_TP = "SELECT time_fetch_all FROM LAMBDA_API_PTP_BASELINE WHERE _rowid_>=? AND _rowid_<?;"
FETCH_API_DATA_DROPLET_TP = "SELECT time_fetch_all FROM LAMBDA_API_PTP_DROPLET WHERE _rowid_>=? AND _rowid_<?;"

def fetch_s3_data_from_db(db_path, from_row, to_row, tab1, tab2):
    with sqlite3.connect(db_path) as conn:
        plain_data = np.asarray(conn.execute(tab1, (from_row, to_row)).fetchall())
        talos_data = np.asarray(conn.execute(tab2, (from_row, to_row)).fetchall())
        return plain_data, talos_data


def plot_s3_latency():

    api_plain_data, api_enc_data = fetch_s3_data_from_db(data_path_s3, 5, 1996, FETCH_API_DATA_BASELINE, FETCH_API_DATA_DROPLET)
    api_plain_data_tp, api_enc_data_tp = fetch_s3_data_from_db(data_path_s3, 2, 199, FETCH_API_DATA_BASELINE_TP, FETCH_API_DATA_DROPLET_TP)

    def compute_statistics(data):
        avg_latency = np.average(data, axis=0)
        std_latency = np.std(data, axis=0)
        return avg_latency, std_latency


    def compute_statistics_tp(data, div_val):
        tp = (div_val/data) *1000
        avg_latency = np.average(tp, axis=0)
        std_latency = np.std(tp, axis=0)
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

    pdf_pages = PdfPages('../plots/demo_api_latency.pdf')
    fig_size = [fig_width, fig_height / 1.2]

    plt.rcParams.update(params)
    plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
    plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3

    avg_plain_l, std_plain_l = compute_statistics(api_plain_data)
    avg_enc_l, std_enc_l = compute_statistics(api_enc_data)

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
    ax1.set_xticklabels(["AWS Cognito Secured API", "Droplet API"])
    ax1.set_xlabel("Amazon Cloud")

    #ax1.legend((rects1[0], rects2[0], rects3[0], rects4[0]), ('Store', 'Get', 'Routing Store', 'Routing Get'), loc="upper left", ncol=2)
    ax1.legend((rects1[0], rects2[0]), ('Store', 'Get'), bbox_to_anchor=(-0.02, 1.00, 1., .102), loc=3, ncol=4, columnspacing=1)

    #handletextpad=0.5, labelspacing=0.2, borderaxespad=0.2, borderpad=0.3)

    #f.suptitle("RTT-%d average latency DHT operations" % latency, fontsize=24, y=1.02)
    ax1.set_ylim([0, 500])
    ax1.yaxis.set_ticks(np.arange(0, 500, 50.0))


    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()


    # tp plot
    pdf_pages = PdfPages('../plots/demo_api_tp.pdf')
    plt.rcParams.update(params)

    avg_plain_l, std_plain_l = compute_statistics_tp(api_plain_data_tp, 100)
    avg_enc_l, std_enc_l = compute_statistics_tp(api_enc_data_tp, 100)

    avg_data = np.vstack((avg_plain_l, avg_enc_l))
    std_data = np.vstack((std_plain_l, std_enc_l))

    ind = np.arange(1, 3)
    width = 0.4

    colours = ['0.3', '0.3', '0.7', '0.7']
    hatch_style = '\\\\\\\\'

    f, ax1 = plt.subplots()

    ax1.grid(True, linestyle=':', color='0.8', zorder=0, axis='y')
    rects1 = ax1.bar(ind, avg_data[:, 0], align='center', color=colours[0], yerr=std_data[:, 0],
                     error_kw=dict(ecolor='0.6', lw=1, capsize=4, capthick=1))

    ax1.set_ylabel("Throughput [req/s]")
    ax1.set_xticklabels(["AWS Cognito Secured API", "Droplet API"])
    ax1.set_xticks(ind)
    ax1.set_xlabel("Amazon Cloud")

    # ax1.legend((rects1[0], rects2[0], rects3[0], rects4[0]), ('Store', 'Get', 'Routing Store', 'Routing Get'), loc="upper left", ncol=2)

    # handletextpad=0.5, labelspacing=0.2, borderaxespad=0.2, borderpad=0.3)
    # f.suptitle("RTT-%d average latency DHT operations" % latency, fontsize=24, y=1.02)
    ax1.set_ylim([0, 100])
    ax1.yaxis.set_ticks(np.arange(0, 100, 20.0))

    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()



if __name__ == "__main__":
    plot_s3_latency()
