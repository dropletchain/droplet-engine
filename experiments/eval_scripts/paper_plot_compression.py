#!/usr/bin/env python
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


import os

import math
import numpy as np



def plot_compression():
    FITBIT = "fb"
    AVA = "av"
    SMART_METER = "smam"

    types = [FITBIT, AVA, SMART_METER]

    files = {
        FITBIT: "chunk_bench_Fitbit_5605640.csv",
        AVA: "chunk_bench_AVA_525600.csv",
        SMART_METER: "chunk_bench_SmartMeter.csv"
    }


    path = "../data/chunk_compression_data"

    result = {}
    for compdata in types:
        file_path = os.path.join(path, files[compdata])
        with open(file_path, 'r') as data_file:
            temp_data = []
            for idx, line in enumerate(data_file):
                if idx > 0:
                    temp_data.append(map(float, line.split(",")))
            result[compdata] = np.asarray(temp_data)

    ########
    # PLOT #
    ########

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


    pdf_pages = PdfPages('../plots/plot_compression-rate.pdf')
    fig_size = [fig_width, fig_height / 1.8]

    plt.rcParams.update(params)
    plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
    plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3

    colors = ['0.1', '0.3', '0.6']
    linestyles = ['-', '--', '-']

    data_ava = result[AVA]
    plt.semilogx(data_ava[:, 0], data_ava[:, 2], '-o', label='Ava dataset', color=colors[0], linestyle=linestyles[0], linewidth=2)

    data_smart = result[SMART_METER]
    plt.semilogx(data_smart[:, 0], data_smart[:, 1], '-o', label='SmartMeter dataset', color=colors[1], linestyle=linestyles[1],
                 linewidth=2)

    data_fitbit = result[FITBIT]
    plt.semilogx(data_fitbit[:, 0], data_fitbit[:, 2], '-o', label='FitBit dataset', color=colors[2], linestyle=linestyles[2],
                 linewidth=2)

    plt.semilogx(1, 1)
    plt.xlabel('Number of Chunk Entries')
    plt.xlim(xmin=2, xmax=300000)

    plt.ylabel('Compression Ratio')
    plt.ylim(ymin=0, ymax=12)

    plt.legend(bbox_to_anchor=(0., 1.08, 1., .102), loc=3, ncol=4)

    plt.grid(True, linestyle=':', color='0.8', zorder=0)
    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()

if __name__ == "__main__":
    plot_compression()