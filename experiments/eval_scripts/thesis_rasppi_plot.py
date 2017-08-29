import math
from numpy import genfromtxt
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def parse_date(date):
    return datetime.strptime(date, "%Y-%m-%d  %H:%M:%S").date()


def rasppy_plot():
    rasp_data = []
    with open("../data/log_rasp_pilatus.csv") as file_data:
        for ind, line in enumerate(file_data):
            if ind == 0:
                continue
            items_line = line.split(",")
            rasp_data.append(map(float, items_line[:-1]))
    rasp_data = np.asarray(rasp_data)

    ########
    # PLOT #
    ########

    # ---------------------------- GLOBAL VARIABLES --------------------------------#
    # figure settings
    fig_width_pt = 300.0  # Get this from LaTeX using \showthe
    inches_per_pt = 1.0 / 72.27 * 2  # Convert pt to inches
    golden_mean = ((math.sqrt(5) - 1.0) / 2.0) * .8  # Aesthetic ratio
    fig_width = fig_width_pt * inches_per_pt  # width in inches
    fig_height = (fig_width * 0.5)  # height in inches
    fig_size = [fig_width, fig_height]
    params = {'backend': 'ps',
        'axes.labelsize': 20,
        'legend.fontsize': 18,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'font.size': 18,
        'figure.figsize': fig_size,
        'font.family': 'times new roman'}

    pdf_pages = PdfPages('../plots/thesis_plot_rasp.pdf')


    plt.rcParams.update(params)
    plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
    plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3

    colors = ['0.1', '0.3', '0.6']
    linestyles = ['-o', '--o', '-']

    x_size, y_size = rasp_data.shape
    #times = np.asarray(map(lambda x: x*2, range(0, x_size))) / 24


    iters = x_size/12
    rasp_data_avg = np.zeros((iters, y_size))
    for i in range(iters):
        rasp_data_avg[i, :] = np.average(rasp_data[(i*12):(i+1)*12], axis=0)
    times = range(iters)

    p1 = plt.plot(times, rasp_data_avg[:, 4], linestyles[0], color=colors[0], linewidth=1, label='Avg Chunk Creation Time')
    p2 = plt.plot(times, rasp_data_avg[:, 5], linestyles[1], color=colors[1], linewidth=1, label='Avg Store Time')

    plt.ylabel('Time in milliseconds [ms]')
    plt.xlabel('Timeline in days [d]')
    plt.ylim(0, 400)
    plt.xlim(0, 34)
    plt.legend(bbox_to_anchor=(-0.03, 1.00, 1., .102), loc=3, ncol=4, columnspacing=0.75)

    plt.grid(True, linestyle=':', color='0.8', zorder=0)
    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()

if __name__ == "__main__":
    rasppy_plot()
