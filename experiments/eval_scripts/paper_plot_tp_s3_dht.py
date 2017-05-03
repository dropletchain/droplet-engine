import os
import re

import sqlite3

import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

db_pattern = re.compile("local_dht_benchmark_par_fetch_k(.*)_a(.*)_n(.*)_l(.*)_t(.*).db")

data_parh = "../data/local_dht_benchmark_par_fetch_k10_a3"
data_path_s3 = "../data/local_s3_benchmark/local_s3_benchmark.db"

FETCH_SUMMARY = "SELECT time_fetch_all FROM CLIENT_STORE_GET WHERE _rowid_>=? AND _rowid_<?;"
FETCH_S3_DATA_PLAIN = "SELECT time_fetch_all FROM CLIENT_S3_PAR_FETCH_PLAIN WHERE _rowid_>=? AND _rowid_<?;"
FETCH_S3_DATA_TALOS = "SELECT time_fetch_all FROM CLIENT_S3_PAR_FETCH_TALOS WHERE _rowid_>=? AND _rowid_<?;"


def fetch_data_from_db(db_path, from_row, to_row):
    with sqlite3.connect(db_path) as conn:
        return np.asarray(conn.execute(FETCH_SUMMARY, (from_row, to_row)).fetchall())

def fetch_s3_data_from_db(db_path, from_row, to_row):
    with sqlite3.connect(db_path) as conn:
        plain_data = np.asarray(conn.execute(FETCH_S3_DATA_PLAIN, (from_row, to_row)).fetchall())
        talos_data = np.asarray(conn.execute(FETCH_S3_DATA_TALOS, (from_row, to_row)).fetchall())
        return plain_data, talos_data

result_data = []
for filename in os.listdir(data_parh):
    if filename.endswith(".db"):
        matching = db_pattern.match(filename)
        if matching:
            kval = int(matching.group(1))
            aval = int(matching.group(2))
            num_nodes = int(matching.group(3))
            latency = int(matching.group(4)) * 2
            data = fetch_data_from_db(os.path.join(data_parh, filename), 5, 105)
            result_data.append([num_nodes] + [x for [x] in data.tolist()])
result_data = np.asarray(result_data)
result_data = result_data[result_data[:, 0].argsort()]


s3_plain_data, s3_enc_data = fetch_s3_data_from_db(data_path_s3, 0, 100)


def compute_troughput(data, num_fetch):
    data_fetch = num_fetch / (data[:, 1:] / 1000)
    _, len_data = data_fetch.shape
    avg_tp = np.average(data_fetch, axis=1)
    std_tp = np.std(data_fetch, axis=1)
    return data[:, 0], avg_tp, std_tp

def compute_tp_s3(data, num_fetch):
    data_tp = num_fetch / (data/1000)
    avg_tp =  np.average(data_tp, axis=0)
    std_tp = num_fetch / np.std(data_tp, axis=0)
    return avg_tp, std_tp


golden_mean = ((math.sqrt(5)-1.0)/2.0)*0.8
fig_with_pt = 600
inches_per_pt = 1.0/72.27*2
fig_with = fig_with_pt*inches_per_pt
fig_height = fig_with * golden_mean
fig_size = [fig_with,fig_height]

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

fig_size = [fig_width, fig_height / 1.2]

plt.rcParams.update(params)
plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3

# plot_latency fixed
pdf_pages = PdfPages("../plots/paper_plot_get_tp.pdf")


f,  ax1 = plt.subplots()
nodes, avg_tp, std_tp = compute_troughput(result_data, 1000)
avg_tp_s3_plain, std_tp_s3_plain = compute_tp_s3(s3_plain_data, 1000)
avg_tp_s3_enc, std_tp_s3_enc = compute_tp_s3(s3_enc_data, 1000)

ind = np.arange(len(nodes.tolist()) + 2)
width = 0.5

data_bars = np.asarray(avg_tp.tolist() + avg_tp_s3_plain.tolist() + avg_tp_s3_enc.tolist())
rects1 = ax1.bar(ind, data_bars, width, color='0.25')


ax1.set_ylabel("Throughput [Get/s]")
xticks = ind + width / 2
ax1.set_xticks(xticks)
ax1.set_xticklabels((map(lambda x: str(int(x)), nodes.tolist())) + ["plain", "check"])
# HACK xD
ax1.set_xlabel("DHT Number of nodes                                  S3")


f.suptitle("Parallel get throughput 20ms RTT", fontsize=24, y=1.02)
#plt.axis('tight')

F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()