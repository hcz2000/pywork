#!/usr/bin/python

import psycopg2
import datetime
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib import animation


class Monitor:

    def __init__(self, database, user, password, host, port):
        self.__conn__ = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
        cur = self.__conn__.cursor()
        cur.execute("SELECT hostname from master_data_dir")
        for r in cur:
            self.masterNode = r[0]
        cur.close()

    def __del__(self):
        self.__conn__.close()

    def refresh(self):
        cur = self.__conn__.cursor()
        cur.execute("SELECT hostname,ctime,mem_total,mem_used,mem_actual_used,mem_actual_free,cpu_sys,cpu_user,cpu_idle from system_now")
        data = [r for r in cur]
        self.__frame__ = DataFrame(data)
        cur.close()
        return self.__frame__

    def getAvgCpuUsage(self):
        avg_data = self.__frame__[self.__frame__[0] != self.masterNode].mean()
        return avg_data[7]

    def getMasterNodeCpuUsage(self):
        master_data = self.__frame__[self.__frame__[0] == self.masterNode]
        return master_data.iloc[0,7]

    def getSegmentNodesCpuUsage(self):
        cpuUsage={}
        data=self.__frame__[self.__frame__[0] != self.masterNode]
        for idx in data.index:
            cpuUsage[data.loc[idx][0]]=data.loc[idx][0]
        return cpuUsage

#monitor=Monitor("gpperfmon","ridshcz","huang056","21.136.64.203","5432")
monitor = Monitor("gpperfmon", "gpmon", "gpmon", "192.168.3.5", "5432")


def data_gen():
    while True:
        tm = np.datetime64(datetime.datetime.now())
        frame = monitor.refresh()
        yield tm, monitor.getMasterNodeCpuUsage(), monitor.getAvgCpuUsage(), monitor.getSegmentNodesCpuUsage()

# 绘图
starttime = np.datetime64(datetime.datetime.now())
endtime = starttime + np.timedelta64(2, 'h')
# starttime=datetime.datetime.now()
# endtime=starttime+datetime.timedelta(hours=2)

fig = plt.figure()
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212)
line, = ax1.plot([], [], lw=1)
line2, = ax1.plot([], [], lw=2)
for tick in ax1.get_xticklabels():
    tick.set_rotation(30)
ax1.xaxis.set_major_locator(dates.MinuteLocator(byminute=False, interval=1,tz=None))
ax1.xaxis.set_major_formatter(dates.DateFormatter("%H:%M"))
ax1.set_ylim(0, 100)
ax1.set_xlim(starttime, endtime)
ax1.grid()

xdata, ydata, y2data = [], [], []


# 因为run的参数是调用函数data_gen的返回值
def run(data):
    global starttime, endtime
    t, y, y2, usageMap = data
    #print(y,y2,usageMap)
    xdata.append(t)
    ydata.append(y)
    y2data.append(y2)

    if t >= endtime:
        starttime = starttime + np.timedelta64(1, 'h')
        endtime = endtime + np.timedelta64(1, 'h')
        ax1.set_xlim(starttime, endtime)
        ax1.figure.canvas.draw()
    line.set_data(xdata, ydata)
    line2.set_data(xdata, y2data)
    ax2.clear()
    nodes= usageMap.keys()
    ind = np.arange(len(nodes))
    ax2.set_ylim(0, 100)
    ax2.set_xticks(ind)
    ax2.set_xticklabels(nodes)
    ax2.bar(ind, usageMap.values(), 0.5, label="db node", color="#87CEFA")

    return line, line2


ani = animation.FuncAnimation(fig, run, data_gen, interval=5 * 1000)
plt.show()

