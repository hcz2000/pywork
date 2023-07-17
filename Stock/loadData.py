import urllib.request
from urllib.error import HTTPError
import datetime
import pymysql

# 获取指定股票的所有历史数据
def download_stock_data(stock_list):
    for sid in stock_list:
        url = "http://table.finance.yahoo.com/table.csv?s=" + sid
        frame = sid + ".csv"
        print("downloading %s from %s" % (frame, url))
        urllib.request.urlretrieve(url, frame)

# 获取某个时间段指定股票数据
def download_stock_data_in_period(stock_list, start, end):
    for sid in stock_list:
        params = {"a": start.month - 1, "b": start.day, "c": start.year,
                  "d": end.month - 1, "e": end.day, "f": end.year, "s": sid}
        url = "http://table.finance.yahoo.com/table.csv?" + urllib.parse.urlencode(params)
        frame = "%s_%d%d%d_%d%d%d.csv" % (sid, start.year, start.month, start.day,
                                          end.year, end.month, end.day)
        print("downloading %s from %s" % (frame, url))
        urllib.request.urlretrieve(url, frame)

def load_stock_data_to_db(stock_list, start, end):
    url = "http://table.finance.yahoo.com/table.csv"
    for sid in stock_list:
        params = {"a": start.month - 1, "b": start.day, "c": start.year,
                  "d": end.month - 1, "e": end.day, "f": end.year, "s": sid}
        data=urllib.parse.urlencode(params)
        try:
            #req=urllib.request.urlopen(url,data.encode('utf-8'))
            req=urllib.request.urlopen(url+'?'+data)
            line=req.readline().decode('utf-8')
            conn=pymysql.connect(host='localhost',port=3306,user='root',passwd=None,db='test')
            while line:
                line=req.readline().decode('utf-8')
                if line!='':
                    cols=line[0:-1].split(',')
                    print(cols)
                    cur=conn.cursor()
                    sql= "INSERT INTO stock_price(date,stock_no,open,high,low,close,volumn,adj_close) VALUES ('"+cols[0]+"','"+sid+"',"+cols[1]+","+cols[2]+","+cols[3]+","+cols[4]+","+cols[5]+","+cols[6]+")"  
                    sta=cur.execute(sql)  
                    if sta==1:  
                        print('Done')  
                    else:  
                        print('Failed')
                    cur.close()  
                    
            conn.commit()  
            conn.close()  
                
            
        except HTTPError as e:
            print(e)
            
           

def main():
    stock_list = ["300001.sz"]
    start = datetime.date(year=2013, month=1, day=1)
    end = datetime.date(year=2015, month=12, day=31)
    #download_stock_data(stock_list)
    #download_stock_data_in_period(stock_list, start, end)
    load_stock_data_to_db(stock_list, start, end)

if __name__ == "__main__":
    main()
