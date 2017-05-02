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

FETCH_ADDRESS_STORE = "SELECT time_crawl_nearest " \
                   "FROM ADD_CHUNK " \
                   "WHERE _rowid_>=? AND _rowid_<?;"

FETCH_ADDRESS_GET = "SELECT time_find_value " \
                   "FROM QUERY_CHUNK_ADDR " \
                   "WHERE _rowid_>=? AND _rowid_<?;"


def extract_client_data_from_db(db_path, start_data, end_data):
    with sqlite3.connect(db_path) as conn:
        data = np.asarray(conn.execute(FETCH_CLIENT_DATA, (start_data, end_data)).fetchall())
        return data[:, 0], data[:, 1]


def extract_address_data_from_db(query, db_path, start_data, end_data):
    with sqlite3.connect(db_path) as conn:
        list_data = conn.execute(query, (start_data, end_data)).fetchall()
        list_data = [0.0 if x[0] is None else x[0] for x in list_data]
        return np.asarray(list_data)


def extract_address_all_data_from_db(db_path, start_data, end_data):
    res1 = extract_address_data_from_db(FETCH_ADDRESS_STORE, db_path, start_data, end_data)
    res2 = extract_address_data_from_db(FETCH_ADDRESS_GET, db_path, start_data, end_data)
    return res1, res2

latencies = [20]

path = "../data/local_dht_benchmark_k10_a3"

data_store = []
data_get = []
data_get_addr = []
data_store_addr = []
for filename in os.listdir(path):
    if filename.endswith(".db"):
        matching = db_pattern.match(filename)
        if matching:
            kval = int(matching.group(1))
            aval = int(matching.group(2))
            num_nodes = int(matching.group(3))
            latency = int(matching.group(4)) * 2
            store_data, get_data = extract_client_data_from_db(os.path.join(path, filename), 25, 1025)
            data_store.append([num_nodes, latency] + store_data.tolist())
            data_get.append([num_nodes, latency] + get_data.tolist())

            store_data_addr, get_data_addr = extract_address_all_data_from_db(os.path.join(path, filename), 25, 1025)
            data_store_addr.append([num_nodes, latency] + store_data_addr.tolist())
            data_get_addr.append([num_nodes, latency] + get_data_addr.tolist())

data_store = np.asarray(data_store)
data_get = np.asarray(data_get)
data_get_addr = np.asarray(data_get_addr)
data_store_addr = np.asarray(data_store_addr)

data_store = data_store[data_store[:, 0].argsort()]
data_get = data_get[data_get[:, 0].argsort()]
data_get_addr = data_get_addr[data_get_addr[:, 0].argsort()]
data_store_addr = data_store_addr[data_store_addr[:, 0].argsort()]



print data_store.shape
print data_get.shape
print data_get_addr.shape
print data_store_addr.shape


def get_data_for_latency(latency, data):
    temp = data[data[:, 1] == latency]
    temp = temp[temp[:, 0].argsort()]
    return temp[:, 0], temp[:, 2:]



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


pdf_pages = PdfPages('../plots/paper_dht_latency.pdf')
fig_size = [fig_width, fig_height / 1.2]

plt.rcParams.update(params)
plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3


def compute_avg_std(data):
    return np.average(data, axis=1), np.std(data, axis=1)


latency = 20

f,  ax1 = plt.subplots()

nodes_s, data_s = get_data_for_latency(latency, data_store)
mean_s, std_s = compute_avg_std(data_s)
nodes_g, data_g = get_data_for_latency(latency, data_get)
mean_g, std_g = compute_avg_std(data_g)

_, addr_data_s = get_data_for_latency(latency, data_store_addr)
addr_mean_s, addr_std_s = compute_avg_std(addr_data_s)
_, addr_data_g = get_data_for_latency(latency, data_get_addr)
addr_mean_g, addr_std_g = compute_avg_std(addr_data_g)

ind = np.arange(1, len(nodes_g.tolist())+1)
width = 0.25

colours = ['0.3', '0.3', '0.7', '0.7']
hatch_style='\\\\\\\\'

ax1.grid(True, linestyle=':', color='0.8', zorder=0, axis='y')
rects1 = ax1.bar(ind, mean_s, width, color=colours[0], yerr=std_g, error_kw=dict(ecolor='0.6', lw=1, capsize=4, capthick=1), zorder=3)
rects2 = ax1.bar(ind + width, mean_g, width, hatch=hatch_style, color=colours[1], yerr=std_s, error_kw=dict(ecolor='0.6', lw=1, capsize=5, capthick=1), zorder=3)
rects3 = ax1.bar(ind, addr_mean_s, width, color=colours[2], zorder=3) #, yerr=addr_std_s, error_kw=dict(ecolor='0.75', lw=2, capsize=5, capthick=2))
rects4 = ax1.bar(ind + width, addr_mean_g, width, color=colours[3], hatch=hatch_style, zorder=3) #, yerr=addr_std_g, error_kw=dict(ecolor='0.25', lw=2, capsize=5, capthick=2))


ax1.set_ylabel("Time in milliseconds [ms]")
ax1.set_xticks(ind + width)
ax1.set_xticklabels((map(lambda x: str(int(x)), nodes_g.tolist())))
ax1.set_xlabel("Number of nodes")

#ax1.legend((rects1[0], rects2[0], rects3[0], rects4[0]), ('Store', 'Get', 'Routing Store', 'Routing Get'), loc="upper left", ncol=2)
ax1.legend((rects1[0], rects2[0], rects3[0], rects4[0]), ('Store', 'Get', 'Routing Store', 'Routing Get'), bbox_to_anchor=(-0.02, 1.00, 1., .102), loc=3, ncol=4, columnspacing=1)

#handletextpad=0.5, labelspacing=0.2, borderaxespad=0.2, borderpad=0.3)

#f.suptitle("RTT-%d average latency DHT operations" % latency, fontsize=24, y=1.02)
ax1.set_ylim([0, 205])
ax1.yaxis.set_ticks(np.arange(0, 201, 20.0))


F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()