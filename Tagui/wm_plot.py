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

class Wm_plot():

    def __init__(self):
        with open('wm.yaml', 'r') as file:
            config = yaml.safe_load(file)
        self.products = []
        self.products.extend(config['cgbwm']['products'])
        self.products.extend(config['bocwm']['products'])
        print(self.products)
        self.basePath = os.path.dirname(__file__)
        self.net_value_data={}

    def rewrite(self):
        fig = plt.figure(figsize=(16, 16))
        ax = fig.add_subplot(111)
        for product in self.products:
            code = product['code']
            desc = product['desc']
            print(code,desc)
            fname = './data/%s.csv' % code
            dt = [('date', 'U16'), ('netvalue', 'f4')]
            net_values = np.loadtxt(fname,  dt, delimiter=',')
            xdata=[datetime.strptime(date,'%Y-%m-%d').date() for date in net_values['date']]
            ydata = net_values['netvalue']
            rewritten_xdata=[]
            rewritten_ydata=[]
            if len(xdata)==0:
                return
            prev_date=xdata[0]
            prev_value=ydata[0]
            rewritten_xdata.append(xdata[0])
            rewritten_ydata.append(ydata[0])
            for i in range(1,len(xdata)):
                next_date=xdata[i]
                next_value=ydata[i]
                date_interval=int((next_date-prev_date)/timedelta(days=1))
                for cnt in range(1,date_interval):
                    rewritten_xdata.append(prev_date+timedelta(days=cnt))
                    rewritten_ydata.append(prev_value+(next_value-prev_value)/date_interval*cnt)
                rewritten_xdata.append(next_date)
                rewritten_ydata.append(next_value)
                prev_date=next_date
                prev_value=next_value

            self.net_value_data[code]=(np.array(rewritten_xdata), np.array(rewritten_ydata))

    def draw(self):
        fig = plt.figure(figsize=(16, 16))
        ax1 = fig.add_subplot(211)
        self.draw_subplot(ax1, (datetime.now() - timedelta(days=365 + 1)).date())

        ax2 = fig.add_subplot(212)
        self.draw_subplot(ax2, (datetime.now() - timedelta(days=60 + 1)).date())

        plt.legend(prop={'family': 'SimHei', 'size': 16})
        plt.show()


    def draw_subplot(self,ax,start_date):
        if (datetime.now() - timedelta(days=30)).date()<start_date:
            ax.xaxis.set_major_locator(dates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m-%d'))
        else:
            ax.xaxis.set_major_locator(dates.MonthLocator())
            ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m'))
            ax.xaxis.set_minor_locator(dates.DayLocator(interval=1))
        font = {'family': 'SimHei', 'weight': 'normal', 'size': 18}
        ax.set_ylabel('净值', font)
        ax.set_xlabel('时间', font)
        ax.set_title('理财产品净值', font)
        for product in self.products:
            code = product['code']
            desc = product['desc']
            xdata=self.net_value_data[code][0]
            ydata=self.net_value_data[code][1]
            disp_xdata=xdata[xdata>start_date]
            disp_ydata=ydata[xdata>start_date]
            disp_ydata=disp_ydata/disp_ydata[0]
            line, = ax.plot(disp_xdata, disp_ydata, lw=4, label=desc)
            for label in ax.get_xticklabels():
                label.set_rotation(30)


if __name__ == '__main__':
    wm = Wm_plot()
    wm.rewrite()
    wm.draw()
