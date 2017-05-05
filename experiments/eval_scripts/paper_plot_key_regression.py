import math
from matplotlib import ticker
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

SMARTPHONE = "Smartphone"
IOT_DEVICE = "Iot device SW"



hast_time_data = {
    SMARTPHONE: 0.044979,
    IOT_DEVICE: 0.297,
}



def plot_key_regression(max_power):
    number_of_hashes = np.asarray([1 << x for x in xrange(max_power)])
    sqrt_number_of_hashes = np.sqrt(number_of_hashes)

    data = {}
    for device_type in hast_time_data.keys():
        time_plain = number_of_hashes * hast_time_data[device_type]
        time_optimized = sqrt_number_of_hashes * hast_time_data[device_type]
        data[device_type] = np.transpose(np.vstack((time_plain, time_optimized)))

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

    fig_size = [fig_width, fig_height / 1.2]

    plt.rcParams.update(params)
    plt.axes([0.12, 0.32, 0.85, 0.63], frameon=True)
    plt.rc('pdf', fonttype=42)  # IMPORTANT to get rid of Type 3

    # plot_latency fixed
    pdf_pages = PdfPages("../plots/paper_plot_key_regression.pdf")
    fig, ax = plt.subplots()

    colors = ['0.1', '0.3', '0.5', '0.7', '0.9']
    linestyles = ['-', '--', '-', '-.', '--']

    ax.set_yscale('log')
    ax.set_xscale('log', basex=2)
    for idx, type_key in enumerate(hast_time_data.keys()):
        cur_data = data[type_key]
        ax.plot(number_of_hashes, cur_data[:, 0], '-o', label="%s normal" % type_key, color=colors[idx * 2],
                linestyle=linestyles[idx])
        ax.plot(number_of_hashes, cur_data[:, 1], '-o', label="%s optimized" % type_key, color=colors[idx * 2 + 1],
                linestyle=linestyles[idx])

    ax.get_yaxis().set_major_formatter(ticker.FormatStrFormatter("%d"))
    plt.xlabel('Version of the key')
    plt.ylabel('Time in milliseconds[ms]')

    plt.legend(bbox_to_anchor=(0., 1.00, 1., .102), loc=3, ncol=2)

    F = plt.gcf()
    F.set_size_inches(fig_size)
    pdf_pages.savefig(F, bbox_inches='tight')
    plt.clf()
    pdf_pages.close()

if __name__ == "__main__":
    plot_key_regression(17)