import os
import yaml
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import FuncFormatter
from datetime import datetime,timedelta
import time
import csv


def date_converter(s):
    return np.datetime64(s)
class WmPic():

    def __init__(self):
        with open('wm.yaml', 'r') as file:
            config=yaml.safe_load(file)
        self.products=[]
        self.products.extend(config['cgbwm']['products'])
        self.products.extend(config['bocwm']['products'])
        self.basePath = os.path.dirname(__file__)

    def draw(self):
        fig=plt.figure(figsize=(16,16))
        ax=fig.add_subplot(111)
        for product in self.products:
            code=product['code']
            print(code)
            fname='./data/%s.csv' % code
            dt=[('date','U16'),('netvalue','f4')]
            #net_values=np.loadtxt(fname,converters={0:date_converter},delimiter=',')
            net_values = np.loadtxt(fname,  dt, delimiter=',')
            xdata=net_values['date'][-16:]
            ydata=net_values['netvalue'][-16:]
            line, = ax.plot(xdata,ydata, lw=1, label=code)
            for label in ax.get_xticklabels():
                label.set_rotation(90)
            ax.xaxis.set_major_locator(dates.DateLocator(interval=1))
            ax.xaxis.set_major_formatter(dates.DateFromatter('%Y-%m-%d'))
            font={'family':'SimHei','weight':'normal','size':10}
            ax.set_ylabel('netvalue',font)
            ax.set_xlabel('date',font)
            ax.set_title('理财产品净值')
            plt.show()
            break



if __name__ == '__main__':
    wm = WmPic()
    wm.draw()
