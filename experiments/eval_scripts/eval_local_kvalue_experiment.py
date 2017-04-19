import numpy as np
import os
import re
import math

import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

FETCH_CLIENT_DATA = "SELECT time_store_chunk, time_fetch_addr + time_fetch_nonce + time_fetch_chunk " \
                    "FROM CLIENT_STORE_GET " \
                    "WHERE _rowid_>=? AND _rowid_<?;"

FETCH_STORE_LOCAL = "SELECT time_total_rpc_store, time_fetch_policy, time_check_chunk_valid, time_db_store_chunk " \
                    "FROM STORE_CHUNK " \
                    "WHERE _rowid_>=? AND _rowid_<?;"

FETCH_QUERY_LOCAL = "SELECT time_total_local_query, time_check_token_valid, time_fetch_policy, time_check_access_valid, time_db_get_chunk " \
                    "FROM QUERY_CHUNK_LOCAL " \
                    "WHERE _rowid_>=? AND _rowid_<?;"

FETCH_STORE_DATA = "SELECT time_crawl_nearest, time_store_to_nodes " \
                   "FROM ADD_CHUNK " \
                   "WHERE _rowid_>=? AND _rowid_<?;"

FETCH_QUERY_DATA = "SELECT time_fetch_addr, time_fetch_nonce, time_fetch_chunk " \
                   "FROM CLIENT_STORE_GET " \
                   "WHERE _rowid_>=? AND _rowid_<?;"


STANDART_PERCENTILE = 95

def compute_median_and_err(conn, stmt, start_data, end_data, err_percentile=STANDART_PERCENTILE):
    data = np.asarray(conn.execute(stmt, (start_data, end_data)).fetchall())
    medians = np.percentile(data, 50, axis=0,)
    err = np.percentile(data, err_percentile, axis=0, )
    return medians, err


def extract_client_data_from_db(db_path, start_data, end_data, err_percentile=STANDART_PERCENTILE):
    with sqlite3.connect(db_path) as conn:
        return compute_median_and_err(conn, FETCH_CLIENT_DATA, start_data, end_data, err_percentile=err_percentile)


def extract_store_data_from_db(db_path, start_data, end_data, err_percentile=STANDART_PERCENTILE):
    with sqlite3.connect(db_path) as conn:
        return compute_median_and_err(conn, FETCH_STORE_DATA, start_data, end_data, err_percentile=err_percentile)


def extract_query_data_from_db(db_path, start_data, end_data, err_percentile=STANDART_PERCENTILE):
    with sqlite3.connect(db_path) as conn:
        return compute_median_and_err(conn, FETCH_QUERY_DATA, start_data, end_data, err_percentile=err_percentile)


def extract_detailed_local_data(db_path, start_data, end_data, err_percentile=90):
    with sqlite3.connect(db_path) as conn:
        median_store, err_store = compute_median_and_err(conn, FETCH_STORE_LOCAL, start_data, end_data, err_percentile=err_percentile)
        median_query, err_query = compute_median_and_err(conn, FETCH_QUERY_LOCAL, start_data, end_data, err_percentile=err_percentile)
        return tuple(median_store.tolist()+ err_store.tolist()), tuple(median_query.tolist() + err_query.tolist())

dtype = [('num_nodes', int), ('kvalue', int), ('median_store', float),
         ('median_get', float), ('err_store', float), ('err_get', float)]

dtype_store = [('num_nodes', int), ('kvalue', int), ('median_search', float),
               ('median_store_to_nodes', float), ('err_search', float), ('err_store', float)]

dtype_query = [('num_nodes', int), ('kvalue', int), ('median_fetch_address', float), ('median_fetch_nonce', float),
               ('median_fetch_chunk', float), ('err_fetch_address', float), ('err_fetch_nonce', float),
               ('err_fetch_chunk', float)]

db_pattern = re.compile("local_dht_benchmark_kvalue_l(.*)_a(.*)_n(.*)_k(.*).db")

kvalues = [10, 20, 30, 40]

paths = ["../data/local_dht_benchmark_kvalue_l10_a3"]
data_sets = []
data_sets_store = []
data_sets_query = []
for path in paths:
    result = []
    result_store = []
    result_query = []
    for filename in os.listdir(path):
        if filename.endswith(".db"):
            matching = db_pattern.match(filename)
            if matching:
                kval = int(matching.group(4))
                aval = int(matching.group(2))
                num_nodes = int(matching.group(3))
                latency = int(matching.group(1)) * 2

                adapted = False
                adapted_idx = -1
                if kval not in kvalues:
                    for idx, val in enumerate(kvalues):
                        if val < kval < kvalues[idx + 1]:
                            kval = kvalues[idx + 1]
                            adapted = True
                            adapted_idx = idx + 1
                            break

                medians1, err1 = extract_client_data_from_db(os.path.join(path, filename), 25, 1025)
                result.append(tuple([num_nodes, kval] + medians1.tolist() + err1.tolist()))

                medians2, err2 = extract_store_data_from_db(os.path.join(path, filename), 25, 1025)
                result_store.append(tuple([num_nodes, kval] + medians2.tolist() + err2.tolist()))

                median3, err3 = extract_query_data_from_db(os.path.join(path, filename), 25, 1025)
                result_query.append(tuple([num_nodes, kval] + median3.tolist() + err3.tolist()))

                if adapted:
                    for idx, val in enumerate(kvalues):
                        if idx > adapted_idx:
                            result.append(tuple([num_nodes, val] + medians1.tolist() + err1.tolist()))
                            result_store.append(tuple([num_nodes, val] + medians2.tolist() + err2.tolist()))
                            result_query.append(tuple([num_nodes, val] + median3.tolist() + err3.tolist()))


    result = np.array(result, dtype=dtype)
    result_store = np.array(result_store, dtype=dtype_store)
    result_query = np.array(result_query, dtype=dtype_query)
    data = np.sort(result, order=['num_nodes', 'kvalue'])
    result_store = np.sort(result_store, order=['num_nodes', 'kvalue'])
    result_query = np.sort(result_query, order=['num_nodes', 'kvalue'])
    data_sets.append(data)
    data_sets_store.append(result_store)
    data_sets_query.append(result_query)

if len(paths) > 1:
    # TODO: Not ok fix
    data = np.sum(np.asarray(data_sets), axis=0) / len(data_sets)
    data = np.array(data, dtype=dtype)
    data_store = data_sets_store[0]
    data_query = data_sets_query[0]
else:
    data = data_sets[0]
    data_store = data_sets_store[0]
    data_query = data_sets_query[0]


print data
print data_store
print data_query

#########
# PLOTS #
#########

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

result1 = data[(data['kvalue'] == 10)]
result2 = data[(data['kvalue'] == 20)]
result3 = data[(data['kvalue'] == 30)]
result4 = data[(data['kvalue'] == 40)]

x = result1['num_nodes']
f, axarr = plt.subplots(2, 2)
a, = axarr[0, 0].plot(x, result1['median_store'], '-o', color='g')
b, = axarr[0, 0].plot(x, result2['median_store'], '-o', color='b')
c, = axarr[0, 0].plot(x, result3['median_store'], '-o', color='y')
d, = axarr[0, 0].plot(x, result4['median_store'], '-o', color='c')
axarr[0, 0].grid(color='gray', linestyle='dashed')
axarr[0, 0].set_title("Median store latency")
axarr[0, 0].set_ylabel("time in milliseconds [ms]")
axarr[0, 0].legend([a, b, c, d], ['k=%d' % 10, 'k=%d' % 20, 'k=%d' % 30, 'k=%d' % 40], bbox_to_anchor=(0., 1.08, 1., .102), loc=3, ncol=4)

axarr[0, 1].plot(x, result1['median_get'], '-o', color='g')
axarr[0, 1].plot(x, result2['median_get'], '-o', color='b')
axarr[0, 1].plot(x, result3['median_get'],'-o', color='y')
axarr[0, 1].plot(x, result4['median_get'], '-o', color='c')
axarr[0, 1].grid(color='gray', linestyle='dashed')
axarr[0, 1].set_title("Median get latency")

axarr[1, 0].plot(x, result1['err_store'], '-o', color='g')
axarr[1, 0].plot(x, result2['err_store'], '-o', color='b')
axarr[1, 0].plot(x, result3['err_store'], '-o', color='y')
axarr[1, 0].plot(x, result4['err_store'], '-o', color='c')
axarr[1, 0].grid(color='gray', linestyle='dashed')
axarr[1, 0].set_title("95th-percentile store latency")
axarr[1, 0].set_ylabel("time in milliseconds [ms]")
axarr[1, 0].set_xlabel("number of nodes")

axarr[1, 1].plot(x, result1['err_get'], '-o', color='g')
axarr[1, 1].plot(x, result2['err_get'], '-o', color='b')
axarr[1, 1].plot(x, result3['err_get'], '-o', color='y')
axarr[1, 1].plot(x, result4['err_get'], '-o', color='c')
axarr[1, 1].grid(color='gray', linestyle='dashed')
axarr[1, 1].set_title("95th-percentile get latency")
axarr[1, 1].set_xlabel("number of nodes")


F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages = PdfPages('../plots/local_kexperiment.pdf')
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()
