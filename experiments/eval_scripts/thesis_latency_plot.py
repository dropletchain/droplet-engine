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


def extract_data(conn, stmt, start_data, end_data):
    data = np.asarray(conn.execute(stmt, (start_data, end_data)).fetchall())
    return data[:, 0],  data[:, 1]


def extract_client_data_from_db(db_path, start_data, end_data):
    with sqlite3.connect(db_path) as conn:
        return extract_data(conn, FETCH_CLIENT_DATA, start_data, end_data)

filter_node = 512
path = "../data/local_dht_benchmark_k10_a3"
data_store = []
data_get = []
for filename in os.listdir(path):
    if filename.endswith(".db"):
        matching = db_pattern.match(filename)
        if matching:
            kval = int(matching.group(1))
            aval = int(matching.group(2))
            num_nodes = int(matching.group(3))
            if num_nodes != filter_node:
                continue

            latency = int(matching.group(4)) * 2
            store_result, get_result = extract_client_data_from_db(os.path.join(path, filename), 25, 1025)
            data_store.append([latency] + store_result.tolist())
            data_get.append([latency] + get_result.tolist())

data_store = np.asarray(data_store)
data_get = np.asarray(data_get)

data_store = data_store[np.argsort(data_store[:, 0])]
data_get = data_get[np.argsort(data_get[:, 0])]

print data_store.shape
print data_get.shape

print data_store[:, 0]
print data_get[:, 0]

#########
# PLOTS #
#########

# ---------------------------- GLOBAL VARIABLES --------------------------------#
# figure settings
fig_width_pt = 300.0  # Get this from LaTeX using \showthe
inches_per_pt = 1.0 / 72.27 * 2  # Convert pt to inches
golden_mean = ((math.sqrt(5) - 1.0) / 2.0) * .8  # Aesthetic ratio
fig_width = fig_width_pt * inches_per_pt  # width in inches
fig_height = (fig_width * golden_mean)  # height in inches
fig_size = [fig_width, fig_height / 1.22]

params = {'backend': 'ps',
          'axes.labelsize': 20,
          'legend.fontsize': 18,
          'xtick.labelsize': 18,
          'ytick.labelsize': 18,
          'font.size': 18,
          'figure.figsize': fig_size,
          'font.family': 'times new roman'}

pdf_pages = PdfPages('../plots/thesis_plot_latency.pdf')

fig_size = [fig_width, fig_height / 1.0]

plt.rcParams.update(params)
plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3

f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)

ax1.set_title("Store")
nodes = data_store[:, 0]
data = data_store[:, 1:]
bp1 = ax1.boxplot(data.tolist(), 0, 'b+', patch_artist=True)
ax1.set_xticklabels(map(lambda x: str(int(x)), nodes.tolist()))
ax1.set_ylabel("Time [ms]")
ax1.set_xlabel("Emulated RTT [ms]")

plt.setp(bp1['boxes'], color='0.4', linewidth=1.5)
plt.setp(bp1['whiskers'], color='0.4', linestyle='-', linewidth=1)
plt.setp(bp1['medians'], color='0.0', linewidth=1)
plt.setp(bp1['caps'], color='0.4', linewidth=1)
ax1.yaxis.grid(True, linestyle=':', which='major', color='0.7',
               alpha=0.5)

ax1.set_ylim([0, 400])

ax2.set_title("Get")
nodes = data_get[:, 0]
data = data_get[:, 1:]
bp2 = ax2.boxplot(data.tolist(), 0, 'b+', patch_artist=True)
ax2.set_xticklabels(map(lambda x: str(int(x)), nodes.tolist()))
ax2.set_xlabel("Emulated RTT [ms]")

plt.setp(bp2['boxes'], color='0.4', linewidth=1.5)
plt.setp(bp2['whiskers'], color='0.4', linestyle='-', linewidth=1)
plt.setp(bp2['medians'], color='0.0', linewidth=1)
plt.setp(bp2['fliers'], color='0.4', linewidth=1)
plt.setp(bp2['caps'], color='0.4', linewidth=1)
ax2.yaxis.grid(True, linestyle=':', which='major', color='0.7',
               alpha=0.5)
#plt.tight_layout()

# fill with colors
colors = ['0.4']
for bplot in (bp1, bp2):
    for patch, color in zip(bplot['boxes'], colors):
        patch.set_facecolor(color)


F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()


