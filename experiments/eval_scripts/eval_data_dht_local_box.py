import numpy as np
import os
import re
import math

import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

db_pattern = re.compile("local_dht_benchmark_k(.*)_a(.*)_n(.*)_l(.*).db")
FETCH_CLIENT_DATA = "SELECT time_store_chunk, time_fetch_addr + time_fetch_nonce + time_fetch_chunk " \
                    "FROM CLIENT_STORE_GET " \
                    "WHERE _rowid_>=? AND _rowid_<?;"


def extract_client_data_from_db(db_path, start_data, end_data):
    with sqlite3.connect(db_path) as conn:
        data = np.asarray(conn.execute(FETCH_CLIENT_DATA, (start_data, end_data)).fetchall())
        return data[:, 0], data[:, 1]


dtype = [('num_nodes', int), ('latency', int), ('median_store', float),
         ('median_get', float), ('err_store', float), ('err_get', float)]

dtype_store = [('num_nodes', int), ('latency', int), ('median_search', float),
               ('median_store_to_nodes', float), ('err_search', float), ('err_store', float)]

dtype_query = [('num_nodes', int), ('latency', int), ('median_fetch_address', float), ('median_fetch_nonce', float),
               ('median_fetch_chunk', float), ('err_fetch_address', float), ('err_fetch_nonce', float),
               ('err_fetch_chunk', float)]

latencies = [0, 10, 20, 30]

paths = ["../data/local_dht_benchmark_k10_a3"]
data_sets_store = []
data_sets_get = []
for path in paths:
    result_store = []
    result_get = []
    for filename in os.listdir(path):
        if filename.endswith(".db"):
            matching = db_pattern.match(filename)
            if matching:
                kval = int(matching.group(1))
                aval = int(matching.group(2))
                num_nodes = int(matching.group(3))
                latency = int(matching.group(4)) * 2
                store_data, get_data = extract_client_data_from_db(os.path.join(path, filename), 25, 1025)
                result_store.append([num_nodes, latency] + store_data.tolist())
                result_get.append([num_nodes, latency] + get_data.tolist())

    result_store = np.asarray(result_store)
    result_get = np.asarray(result_get)
    result_store = result_store[result_store[:, 0].argsort()]
    result_get = result_get[result_get[:, 0].argsort()]

    data_sets_store.append(result_store)
    data_sets_get.append(result_get)

if len(paths) > 1:
    # TODO: Not ok fix
    assert False
    #data_store = np.sum(np.asarray(data_sets_store), axis=0) / len(data_sets_store)
    #data_get = np.sum(np.asarray(data_sets_get), axis=0) / len(data_sets_get)
else:
    data_store = data_sets_store[0]
    data_get = data_sets_get[0]


print data_store.shape
print data_get.shape


def get_data_for_latency(latency, data):
    temp = data[data[:, 1] == latency]
    temp = temp[temp[:, 0].argsort()]
    return temp[:, 0], temp[:, 2:]



#########
# PLOTS #
#########

golden_mean = ((math.sqrt(5) - 1.0) / 2.0) * 0.8
fig_with_pt = 600
inches_per_pt = 1.0 / 72.27 * 2
fig_with = fig_with_pt * inches_per_pt
fig_height = fig_with * golden_mean
fig_size = [fig_with, fig_height]

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
plt.rc('pdf', fonttype=42)

# boxplots
for latency in latencies:
    f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)

    ax1.set_title("Put")
    nodes, data = get_data_for_latency(latency, data_store)
    print len(data.tolist())
    ax1.boxplot(data.tolist(),  0, '')
    ax1.set_xticklabels(map(lambda x: str(int(x)), nodes.tolist()))
    ax1.set_ylabel("Time in milliseconds [ms]")
    ax1.set_xlabel("Number of nodes")


    ax2.set_title("Get")
    nodes, data = get_data_for_latency(latency, data_get)
    ax2.boxplot(data.tolist(),  0, '')
    ax2.set_xticklabels(map(lambda x: str(int(x)), nodes.tolist()))
    ax2.set_xlabel("Number of nodes")

    f.suptitle("RTT-%d median latency DHT operations" % latency, fontsize=24, y=1.02)

    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages = PdfPages("../plots/dht_operations_client_box_l%d.pdf" % latency)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()


def compute_avg_std(data):
    return np.average(data, axis=1), np.std(data, axis=1)

# barplots
for latency in latencies:
    f,  ax1 = plt.subplots()

    nodes_s, data_s = get_data_for_latency(latency, data_store)
    mean_s, std_s = compute_avg_std(data_s)
    nodes_g, data_g = get_data_for_latency(latency, data_get)
    mean_g, std_g = compute_avg_std(data_g)
    ind = np.arange(len(nodes_g.tolist()))
    width = 0.35

    rects1 = ax1.bar(ind, mean_s, width, color='0.25', yerr=std_g, error_kw=dict(ecolor='0.75', lw=2, capsize=5, capthick=2))
    rects2 = ax1.bar(ind + width, mean_g, width, color='0.75', yerr=std_s, error_kw=dict(ecolor='0.25', lw=2, capsize=5, capthick=2))


    ax1.set_ylabel("Time in milliseconds [ms]")
    ax1.set_xticks(ind + width)
    ax1.set_xticklabels((map(lambda x: str(int(x)), nodes_g.tolist())))
    ax1.set_xlabel("Number of nodes")

    ax1.legend((rects1[0], rects2[0]), ('Put', 'Get'), loc="upper left")

    f.suptitle("RTT-%d average latency DHT operations" % latency, fontsize=24, y=1.02)
    plt.axis('tight')

    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages = PdfPages("../plots/dht_operations_client_bar_l%d.pdf" % latency)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()