import os
import yaml
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.axis import Axis
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
import time
import csv

class WmPic():

    def __init__(self):
        with open('wm.yaml', 'r') as file:
            config = yaml.safe_load(file)
        self.products = []
        self.products.extend(config['cgbwm']['products'])
        self.products.extend(config['bocwm']['products'])
        print(self.products)
        self.basePath = os.path.dirname(__file__)

    def draw(self):
        fig = plt.figure(figsize=(16, 16))
        ax = fig.add_subplot(111)
        for product in self.products:
            code = product['code']
            desc = product['desc']
            print(code,desc)
            fname = './data/%s.csv' % code
            #net_values = np.loadtxt(fname, converters={0: (lambda s: np.datetime64(s))}, delimiter=',')
            #xdata = net_values[:, 0]
            #ydata = net_values[:, 1]
            dt = [('date', 'U16'), ('netvalue', 'f4')]
            net_values = np.loadtxt(fname,  dt, delimiter=',')
            xdata=[datetime.strptime(date,'%Y-%m-%d').date() for date in net_values['date']]
            ydata=net_values['netvalue']
            line, = ax.plot(xdata, ydata, lw=4, label=desc)
            for label in ax.get_xticklabels():
                label.set_rotation(60)
            ax.xaxis.set_major_locator(dates.MonthLocator())
            ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m'))
            ax.xaxis.set_minor_locator(dates.DayLocator(interval=1))
            font = {'family': 'SimHei', 'weight': 'normal', 'size': 18}
            ax.set_ylabel('净值', font)
            ax.set_xlabel('时间', font)
            ax.set_title('理财产品净值', font)
        plt.legend(prop={'family': 'SimHei', 'size': 16})
        plt.show()



if __name__ == '__main__':
    wm = WmPic()
    wm.draw()
