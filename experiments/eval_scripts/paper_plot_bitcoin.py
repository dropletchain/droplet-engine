import math
from numpy import genfromtxt
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def parse_date(date):
    return datetime.strptime(date, "%Y-%m-%d  %H:%M:%S").date()


def bitcoin_plot():
    bc_data = []
    bc_dates = []
    with open("../data/bitcoin_blockchain/median-confirmation-time.csv") as file_data:
        for line in file_data:
            [date, minutes] = line.split(",")
            bc_data.append(float(minutes))
            bc_dates.append(parse_date(date))
    bc_data = np.asarray(bc_data)

    ########
    # PLOT #
    ########

    # ---------------------------- GLOBAL VARIABLES --------------------------------#
    # figure settings
    fig_width_pt = 300.0  # Get this from LaTeX using \showthe
    inches_per_pt = 1.0 / 72.27 * 2  # Convert pt to inches
    golden_mean = ((math.sqrt(5) - 1.0) / 2.0) * .8  # Aesthetic ratio
    fig_width = fig_width_pt * inches_per_pt  # width in inches
    fig_height = (fig_width * golden_mean)  # height in inches
    fig_size = [fig_width, fig_height / 1.22]

    params = {'backend': 'ps',
              'axes.labelsize': 18,
              'legend.fontsize': 16,
              'xtick.labelsize': 16,
              'ytick.labelsize': 16,
              'font.size': 16,
              'figure.figsize': fig_size,
              'font.family': 'times new roman'}

    pdf_pages = PdfPages('../plots/paper_plot_bitcoin_transaction.pdf')
    fig_size = [fig_width, fig_height / 1.2]

    plt.rcParams.update(params)
    plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
    plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3

    colors = ['0.1', '0.3', '0.6']
    linestyles = ['-', '--', '-']

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()

    plt.plot(bc_dates, bc_data, color=colors[1], linestyle=linestyles[0])

    plt.ylabel('Time in minutes [m]')
    plt.xlabel('Month from 2016 to 2017')

    plt.grid(True, linestyle=':', color='0.8', zorder=0)
    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()

if __name__ == "__main__":
    bitcoin_plot()
