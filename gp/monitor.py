#!/usr/bin/python

import psycopg2
import time
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib import animation

class Monitor:
    __conn=None
    __hosts=None
    __fig=None
    __axes={}
    __lines={}
    __frame=None
    def __init__(self,database,user,password,host,port):
        self.__conn=psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
        cur=self.__conn.cursor()
        cur.execute("SELECT hostname from system_now order by hostname asc")
        self.__hosts=DataFrame([r for r in cur])[0]
        cur.close()
        self.__fig=plt.figure()
        no=0
        for host in self.__hosts:
            no=no+1
            self.__axes[host]=self.__fig.add_subplot(2, 5, no)
            plt.title(host)
        self.loadData()

    def __del__(self):
        self.__conn.close()

    def loadData(self):
        starttime=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()-300))
        cur=self.__conn.cursor()
        cur.execute("SELECT hostname,ctime,mem_total,mem_used,mem_actual_used,mem_actual_free,cpu_sys,cpu_user,cpu_idle  from system_history where  ctime >'"+starttime+"' order by ctime asc")
        data=[r for r in cur]
        self.__frame=DataFrame(data)
        cur.close()
        return self.__frame
    
    def draw(self):
        for host in self.__hosts:
            ax=self.__axes[host]
            data=self.__frame[self.__frame[0] == host]
            times=data[1]
            cpu_usr=data[7]
            for tick in ax.get_xticklabels():
                tick.set_rotation(90)
            ax.xaxis.set_major_locator(dates.MinuteLocator(byminute=None, interval=1, tz=None))
            ax.xaxis.set_major_formatter(dates.DateFormatter("%H:%M"))
            line, =ax.plot(times,cpu_usr)
            self.__lines[host]=line
    
    def update(self):
        x_min=self.__frame[1].min()
        x_max=self.__frame[1].max()
        y_max=self.__frame[7].max()
        for host in self.__hosts:
            ax=self.__axes[host]
            line=self.__lines[host]
            data=self.__frame[self.__frame[0] == host]
            x_data=data[1]
            y_data=data[7]
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(0,y_max)
            ax.figure.canvas.draw()
            line.set_data(x_data.tolist(),y_data.tolist())


#loader=DataLoader("gpperfmon","ridshcz","huang056","21.136.64.203","5432")
monitor=Monitor("gpperfmon","gpmon","gpmon","192.168.3.5","5432")
monitor.draw()
 
def update_data(frame):
    monitor.update()
    
    
def data_gen():
    while True:  
        frame=monitor.loadData()
        yield frame
	

ani = animation.FuncAnimation(monitor.__fig, update_data, data_gen, interval=5 * 1000)
plt.show()
