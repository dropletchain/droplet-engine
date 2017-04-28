import os
import re

import sqlite3

import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

db_pattern = re.compile("local_dht_benchmark_par_fetch_k(.*)_a(.*)_n(.*)_l(.*)_t(.*).db")

data_parh = "../data/local_dht_benchmark_par_fetch_k10_a3"

FETCH_SUMMARY = "SELECT time_fetch_all FROM CLIENT_STORE_GET WHERE _rowid_>=? AND _rowid_<?;"


def fetch_data_from_db(db_path, from_row, to_row):
    with sqlite3.connect(db_path) as conn:
        return np.asarray(conn.execute(FETCH_SUMMARY, (from_row, to_row)).fetchall())

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


def compute_troughput(data, num_fetch):
    data_fetch = data[:, 1:] / 1000
    _, len_data = data_fetch.shape
    avg_tp = num_fetch / np.average(data_fetch, axis=1)
    std_tp = num_fetch / np.std(data_fetch, axis=1)
    return data[:, 0], avg_tp, std_tp




golden_mean = ((math.sqrt(5)-1.0)/2.0)*0.8
fig_with_pt = 600
inches_per_pt = 1.0/72.27*2
fig_with = fig_with_pt*inches_per_pt
fig_height = fig_with * golden_mean
fig_size = [fig_with,fig_height]

params = {'backend': 'ps',
    'axes.labelsize': 22,
    'font.size': 22,
    'legend.fontsize': 20,
    'xtick.labelsize': 20,
    'ytick.labelsize': 20,
    'figure.figsize': fig_size,
    'font.family': 'Times New Roman'}

# plot_latency fixed
plt.rcParams.update(params)
plt.rc('pdf',fonttype = 42)


f,  ax1 = plt.subplots()
nodes, avg_tp, std_tp = compute_troughput(result_data, 1000)
ind = np.arange(len(nodes.tolist()))
width = 0.5

rects1 = ax1.bar(ind, avg_tp, width, color='0.25')


ax1.set_ylabel("Throughput Get per seconds [Get/s]")
ax1.set_xticks(ind + width / 2)
ax1.set_xticklabels((map(lambda x: str(int(x)), nodes.tolist())))
ax1.set_xlabel("Number of nodes")

f.suptitle("RTT-%d Throughput DHT operations parallel fetch" % 20, fontsize=24, y=1.02)
plt.axis('tight')

F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages = PdfPages("../plots/dht_operations_par_fetch_bar.pdf")
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()