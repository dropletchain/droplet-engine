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

dtype = [('num_nodes', int), ('latency', int), ('median_store', float),
         ('median_get', float), ('err_store', float), ('err_get', float)]

dtype_store = [('num_nodes', int), ('latency', int), ('median_search', float),
               ('median_store_to_nodes', float), ('err_search', float), ('err_store', float)]

dtype_query = [('num_nodes', int), ('latency', int), ('median_fetch_address', float), ('median_fetch_nonce', float),
               ('median_fetch_chunk', float), ('err_fetch_address', float), ('err_fetch_nonce', float),
               ('err_fetch_chunk', float)]

paths = ["../data/local_dht_benchmark_k10_a3"]
data_sets = []
data_sets_store = []
data_sets_query = []
detailed_data = None
for path in paths:
    result = []
    result_store = []
    result_query = []
    for filename in os.listdir(path):
        if filename.endswith(".db"):
            matching = db_pattern.match(filename)
            if matching:
                kval = int(matching.group(1))
                aval = int(matching.group(2))
                num_nodes = int(matching.group(3))
                latency = int(matching.group(4)) * 2
                medians, err = extract_client_data_from_db(os.path.join(path, filename), 25, 1025)
                result.append(tuple([num_nodes, latency] + medians.tolist() + err.tolist()))

                medians, err = extract_store_data_from_db(os.path.join(path, filename), 25, 1025)
                result_store.append(tuple([num_nodes, latency] + medians.tolist() + err.tolist()))

                medians, err = extract_query_data_from_db(os.path.join(path, filename), 25, 1025)
                result_query.append(tuple([num_nodes, latency] + medians.tolist() + err.tolist()))

                if num_nodes == 512 and latency == 30:
                    detailed_data = extract_detailed_local_data(os.path.join(path, filename), 25, 1025)

    result = np.array(result, dtype=dtype)
    result_store = np.array(result_store, dtype=dtype_store)
    result_query = np.array(result_query, dtype=dtype_query)
    data = np.sort(result, order=['num_nodes', 'latency'])
    result_store = np.sort(result_store, order=['num_nodes', 'latency'])
    result_query = np.sort(result_query, order=['num_nodes', 'latency'])
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
print detailed_data[0]
print detailed_data[1]
print data_store

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

result = data[(data['latency'] == 0)]
x = result['num_nodes']
f, axarr = plt.subplots(2, 2)
a, = axarr[0, 0].plot(x, result['median_store'], '-o', color='g')
b, = axarr[0, 0].plot(x, result['median_get'], '-o', color='b')
c, = axarr[0, 0].plot(x, result['err_store'],'-*', color='r')
d, = axarr[0, 0].plot(x, result['err_get'], '-*', color='m')
axarr[0, 0].grid(color='gray', linestyle='dashed')
axarr[0, 0].set_title('%dms-rtt-latency client times' % 0)
axarr[0, 0].set_ylabel("time in milliseconds [ms]")
axarr[0, 0].legend([a, b, c, d], ['median store', 'median get','95th percentile store', '95th percentile get'], bbox_to_anchor=(0., 1.08, 1., .102), loc=3, ncol=4)

result = data[(data['latency'] == 10)]
axarr[0, 1].plot(x, result['median_store'], '-o', color='g')
axarr[0, 1].plot(x, result['median_get'], '-o', color='b')
axarr[0, 1].plot(x, result['err_store'],'-*', color='r')
axarr[0, 1].plot(x, result['err_get'], '-*', color='m')
axarr[0, 1].grid(color='gray', linestyle='dashed')
axarr[0, 1].set_title('%dms-rtt-latency client times' % 10)

result = data[(data['latency'] == 20)]
axarr[1, 0].plot(x, result['median_store'], '-o', color='g')
axarr[1, 0].plot(x, result['median_get'], '-o', color='b')
axarr[1, 0].plot(x, result['err_store'], '-*', color='r')
axarr[1, 0].plot(x, result['err_get'], '-*', color='m')
axarr[1, 0].grid(color='gray', linestyle='dashed')
axarr[1, 0].set_title('%dms-rtt-latency client times' % 20)
axarr[1, 0].set_ylabel("time in milliseconds [ms]")
axarr[1, 0].set_xlabel("number of nodes")

result = data[(data['latency'] == 30)]
axarr[1, 1].plot(x, result['median_store'], '-o', color='g')
axarr[1, 1].plot(x, result['median_get'], '-o', color='b')
axarr[1, 1].plot(x, result['err_store'], '-*', color='r')
axarr[1, 1].plot(x, result['err_get'], '-*', color='m')
axarr[1, 1].grid(color='gray', linestyle='dashed')
axarr[1, 1].set_title('%dms-rtt-latency client times' % 30)
axarr[1, 1].set_xlabel("number of nodes")


F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages = PdfPages('../plots/local_latency_fixed.pdf')
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()

# plot_nodes_fixed

plt.rcParams.update(params)
plt.rc('pdf',fonttype = 42)

result = data[(data['num_nodes'] == 16)]
x = result['latency']
f, axarr = plt.subplots(2, 2)
a, = axarr[0, 0].plot(x, result['median_store'], '-o', color='g')
b, = axarr[0, 0].plot(x, result['median_get'], '-o', color='b')
c, = axarr[0, 0].plot(x, result['err_store'], '-*', color='r')
d, = axarr[0, 0].plot(x, result['err_get'], '-*', color='m')
axarr[0, 0].grid(color='gray', linestyle='dashed')
axarr[0, 0].set_title('%d-nodes client times' % 16)
axarr[0, 0].set_ylabel("time in milliseconds [ms]")
axarr[0, 0].legend([a, b, c, d], ['median store', 'median get','95th percentile store', '95th percentile get'], bbox_to_anchor=(0., 1.08, 1., .102), loc=3, ncol=4)

result = data[(data['num_nodes'] == 256)]
axarr[0, 1].plot(x, result['median_store'], '-o', color='g')
axarr[0, 1].plot(x, result['median_get'], '-o', color='b')
axarr[0, 1].plot(x, result['err_store'], '-*',color='r')
axarr[0, 1].plot(x, result['err_get'], '-*', color='m')
axarr[0, 1].grid(color='gray', linestyle='dashed')
axarr[0, 1].set_title('%d-nodes client times' % 256)

result = data[(data['num_nodes'] == 512)]
axarr[1, 0].plot(x, result['median_store'], '-o', color='g')
axarr[1, 0].plot(x, result['median_get'], '-o', color='b')
axarr[1, 0].plot(x, result['err_store'], '-*',color='r')
axarr[1, 0].plot(x, result['err_get'], '-*', color='m')
axarr[1, 0].grid(color='gray', linestyle='dashed')
axarr[1, 0].set_title('%d-nodes client times' % 512)
axarr[1, 0].set_ylabel("time in milliseconds [ms]")
axarr[1, 0].set_xlabel("RTT-latency [ms]")

result = data[(data['num_nodes'] == 1024)]
axarr[1, 1].plot(x, result['median_store'], '-o', color='g')
axarr[1, 1].plot(x, result['median_get'], '-o', color='b')
axarr[1, 1].plot(x, result['err_store'], '-*',color='r')
axarr[1, 1].plot(x, result['err_get'], '-*', color='m')
axarr[1, 1].grid(color='gray', linestyle='dashed')
axarr[1, 1].set_title('%d-nodes client times' % 1024)
axarr[1, 1].set_xlabel("RTT-latency [ms]")


F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages = PdfPages('../plots/local_nodes_fixed.pdf')
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()

# Detailed Store Plot
plt.rcParams.update(params)
plt.rc('pdf',fonttype = 42)

result = data_store[(data_store['latency'] == 0)]
x = result['num_nodes']
f, axarr = plt.subplots(2, 2)
a, = axarr[0, 0].plot(x, result['median_search'], '-o', color='g')
b, = axarr[0, 0].plot(x, result['median_store_to_nodes'], '-o', color='b')
c, = axarr[0, 0].plot(x, result['err_search'],'-*', color='r')
d, = axarr[0, 0].plot(x, result['err_store'], '-*', color='m')
axarr[0, 0].grid(color='gray', linestyle='dashed')
axarr[0, 0].set_title('%dms-rtt-latency store times' % 0)
axarr[0, 0].set_ylabel("time in milliseconds [ms]")
axarr[0, 0].legend([a, b, c, d], ['median search', 'median store to nodes','95th percentile search',
                                  '95th percentile store to nodes'], bbox_to_anchor=(0., 1.08, 1., .102), loc=3, ncol=2)

result = data_store[(data_store['latency'] == 10)]
axarr[0, 1].plot(x, result['median_search'], '-o', color='g')
axarr[0, 1].plot(x, result['median_store_to_nodes'], '-o', color='b')
axarr[0, 1].plot(x, result['err_search'],'-*', color='r')
axarr[0, 1].plot(x, result['err_store'], '-*', color='m')
axarr[0, 1].grid(color='gray', linestyle='dashed')
axarr[0, 1].set_title('%dms-rtt-latency store times' % 10)

result = data_store[(data_store['latency'] == 20)]
axarr[1, 0].plot(x, result['median_search'], '-o', color='g')
axarr[1, 0].plot(x, result['median_store_to_nodes'], '-o', color='b')
axarr[1, 0].plot(x, result['err_search'], '-*', color='r')
axarr[1, 0].plot(x, result['err_store'], '-*', color='m')
axarr[1, 0].grid(color='gray', linestyle='dashed')
axarr[1, 0].set_title('%dms-rtt-latency store times' % 20)
axarr[1, 0].set_ylabel("time in milliseconds [ms]")
axarr[1, 0].set_xlabel("number of nodes")

result = data_store[(data_store['latency'] == 30)]
axarr[1, 1].plot(x, result['median_search'], '-o', color='g')
axarr[1, 1].plot(x, result['median_store_to_nodes'], '-o', color='b')
axarr[1, 1].plot(x, result['err_search'], '-*', color='r')
axarr[1, 1].plot(x, result['err_store'], '-*', color='m')
axarr[1, 1].grid(color='gray', linestyle='dashed')
axarr[1, 1].set_title('%dms-rtt-latency store times' % 30)
axarr[1, 1].set_xlabel("number of nodes")


F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages = PdfPages('../plots/local_store_detailed.pdf')
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()


# Detailed Query Plot
plt.rcParams.update(params)
plt.rc('pdf',fonttype = 42)

result = data_query[(data_query['latency'] == 0)]
x = result['num_nodes']
fig, axarr = plt.subplots(2, 2)
a, = axarr[0, 0].plot(x, result['median_fetch_nonce'], '-o', color='g')
b, = axarr[0, 0].plot(x, result['median_fetch_address'], '-o', color='b')
d, = axarr[0, 0].plot(x, result['median_fetch_chunk'], '-o', color='y')
e, = axarr[0, 0].plot(x, result['err_fetch_nonce'],'-*', color='r')
h, = axarr[0, 0].plot(x, result['err_fetch_address'], '-*', color='m')
g, = axarr[0, 0].plot(x, result['err_fetch_chunk'], '-*', color='c')
axarr[0, 0].grid(color='gray', linestyle='dashed')
axarr[0, 0].set_title('%dms-rtt-latency query times' % 0)
axarr[0, 0].set_ylabel("time in milliseconds [ms]")
axarr[0, 0].legend([a, b, d, e, h, g], ['median fetch nonce', 'median fetch address', 'median fetch chunk',
                                           '95th percentile fetch nonce', '95th percentile fetch address',
                                           '95th percentile fetch chunk'],
                   bbox_to_anchor=(0., 1.08, 1., .102), loc=3, ncol=2)

result = data_query[(data_query['latency'] == 10)]
axarr[0, 1].plot(x, result['median_fetch_nonce'], '-o', color='g')
axarr[0, 1].plot(x, result['median_fetch_address'], '-o', color='b')
axarr[0, 1].plot(x, result['median_fetch_chunk'], '-o', color='y')
axarr[0, 1].plot(x, result['err_fetch_nonce'],'-*', color='r')
axarr[0, 1].plot(x, result['err_fetch_address'], '-*', color='m')
axarr[0, 1].plot(x, result['err_fetch_chunk'], '-*', color='c')
axarr[0, 1].grid(color='gray', linestyle='dashed')
axarr[0, 1].set_title('%dms-rtt-latency query times' % 10)

result = data_query[(data_query['latency'] == 20)]
axarr[1, 0].plot(x, result['median_fetch_nonce'], '-o', color='g')
axarr[1, 0].plot(x, result['median_fetch_address'], '-o', color='b')
axarr[1, 0].plot(x, result['median_fetch_chunk'], '-o', color='y')
axarr[1, 0].plot(x, result['err_fetch_nonce'], '-*', color='r')
axarr[1, 0].plot(x, result['err_fetch_address'], '-*', color='m')
axarr[1, 0].plot(x, result['err_fetch_chunk'], '-*', color='c')
axarr[1, 0].grid(color='gray', linestyle='dashed')
axarr[1, 0].set_title('%dms-rtt-latency query times' % 20)
axarr[1, 0].set_ylabel("time in milliseconds [ms]")
axarr[1, 0].set_xlabel("number of nodes")

result = data_query[(data_query['latency'] == 30)]
axarr[1, 1].plot(x, result['median_fetch_nonce'], '-o', color='g')
axarr[1, 1].plot(x, result['median_fetch_address'], '-o', color='b')
axarr[1, 1].plot(x, result['median_fetch_chunk'], '-o', color='y')
axarr[1, 1].plot(x, result['err_fetch_nonce'], '-*', color='r')
axarr[1, 1].plot(x, result['err_fetch_address'], '-*', color='m')
axarr[1, 1].plot(x, result['err_fetch_chunk'], '-*', color='c')
axarr[1, 1].grid(color='gray', linestyle='dashed')
axarr[1, 1].set_title('%dms-rtt-latency query times' % 30)
axarr[1, 1].set_xlabel("number of nodes")

F = plt.gcf()
F.set_size_inches(fig_size)
pdf_pages = PdfPages('../plots/local_query_detailed.pdf')
pdf_pages.savefig(F, bbox_inches='tight')
plt.clf()
pdf_pages.close()
