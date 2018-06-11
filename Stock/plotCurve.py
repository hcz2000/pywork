import pymysql
from pandas import DataFrame
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def getData(stock_no):
    conn=pymysql.connect(host='localhost',port=3306,user='root',passwd=None,db='test')
    cur=conn.cursor()
    cur.execute('select * from stock_price where stock_no="'+stock_no+'"')
    #data=[]
    #for r in cur:
    #    data.append(r)
    data=[r for r in cur]
    frame=DataFrame(data)
    cur.close()
    conn.close()
    return frame

def plot(frame):
    dates=frame[0]
    close=frame[5]
    fig=plt.figure()
    ax=fig.add_subplot(111)
    ax.set_title("Stock Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(45)
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=range(1,32),interval=15))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.plot(dates,close)
    plt.subplots_adjust(bottom=0.13,top=0.95)
    plt.legend('daily')
    plt.grid(True)
    plt.show()
    
    

def main():
    frame=getData('300001.sz')
    plot(frame)

if __name__=='__main__':
    main()
    

