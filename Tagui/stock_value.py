import urllib.request
from urllib.error import HTTPError
import datetime
import os
import sqlite3
import yaml

class SQLLiteTool:
    def __init__(self,dbfile):
        self.conn=sqlite3.connect(dbfile)

    def __del__(self):
        self.conn.close()

    def queryDB(self,sql):
        try:
            cur=self.conn.cursor()
            cur.execute(sql)
            result=cur.fetchall()
            cur.close()
            return result
        except Exception as e:
            print(e)

    def updateDB(self,sql):
        try:
            cur=self.conn.cursor()
            cur.execute(sql)
            self.conn.commit()
            return
        except Exception as e:
            print(e)

class StockValue():
    def __init__(self):
        #with open('wm.yaml', 'r', encoding='utf-8') as file:
        #    self.config=yaml.safe_load(file)
        self.basePath = os.path.dirname(__file__)
        if not os.path.exists('data'):
            os.makedirs('data')
        dbfile='data%sstock.db'%os.path.sep
        if not os.path.exists(dbfile):
            self.dbtool = SQLLiteTool(dbfile)
            self.dbtool.updateDB('''create table stockvalue(date varchar(10), code varchar(16), rpt_date varchar(10), open float ,close float, high float, low float,
                ,volumn float,adj_close float   PRIMARY KEY(date,code))''')
        else:
            self.dbtool = SQLLiteTool(dbfile)

    def __del__(self):
        del self.dbtool

    # 获取指定股票的所有历史数据
    def download_stock_data(self,stock_list):
        for sid in stock_list:
            url = "http://table.finance.yahoo.com/table.csv?s=" + sid
            frame = sid + ".csv"
            print("downloading %s from %s" % (frame, url))
            urllib.request.urlretrieve(url, frame)


    # 获取某个时间段指定股票数据
    def download_stock_data_in_period(self,stock_list, start, end):
        for sid in stock_list:
            params = {"a": start.month - 1, "b": start.day, "c": start.year,
                  "d": end.month - 1, "e": end.day, "f": end.year, "s": sid}
            url = "http://table.finance.yahoo.com/table.csv?" + urllib.parse.urlencode(params)
            frame = "%s_%d%d%d_%d%d%d.csv" % (sid, start.year, start.month, start.day,
                                          end.year, end.month, end.day)
            print("downloading %s from %s" % (frame, url))
            urllib.request.urlretrieve(url, frame)


    def load_stock_data_to_db(self,stock_list, start, end):
        url = "http://table.finance.yahoo.com/table.csv"
        for sid in stock_list:
            params = {"a": start.month - 1, "b": start.day, "c": start.year,
                  "d": end.month - 1, "e": end.day, "f": end.year, "s": sid}
            data = urllib.parse.urlencode(params)
            try:
                # req=urllib.request.urlopen(url,data.encode('utf-8'))
                req = urllib.request.urlopen(url + '?' + data)
                line = req.readline().decode('utf-8')
                while line:
                    line = req.readline().decode('utf-8')
                    if line != '':
                        cols = line[0:-1].split(',')
                        print(cols)
                        sql = "INSERT INTO stock_price(date,stock_no,open,high,low,close,volumn,adj_close) VALUES ('" + \
                          cols[0] + "','" + sid + "'," + cols[1] + "," + cols[2] + "," + cols[3] + "," + cols[4] + "," + \
                          cols[5] + "," + cols[6] + ")"
                        self.dbtool.updateDB(sql)


            except HTTPError as e:
                print(e)


def main():
    stock=StockValue()

    stock_list = ["300001.sz"]
    start = datetime.date(year=2021, month=1, day=1)
    end = datetime.date(year=2023, month=12, day=31)
    # download_stock_data(stock_list)
    # download_stock_data_in_period(stock_list, start, end)
    stock.load_stock_data_to_db(stock_list, start, end)


if __name__ == "__main__":
    main()
