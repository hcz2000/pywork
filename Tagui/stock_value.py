import urllib.request
from urllib.error import HTTPError
from datetime import datetime
import os
import sqlite3
import yaml
import akshare

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
        print(dbfile)
        if not os.path.exists(dbfile):
            self.dbtool = SQLLiteTool(dbfile)
            self.dbtool.updateDB('''create table stock_value( rpt_date varchar(10), code varchar(16), open float ,close float, high float, low float,
                volumn float,amplitude float, change_percent, turnover_ratio float  PRIMARY KEY(rpt_date,code))''')
            print('''create table stock_value( rpt_date varchar(10), code varchar(16), open float ,close float, high float, low float,
                volumn float,amplitude float, change_percent, turnover_ratio float  PRIMARY KEY(rpt_date,code))''')
        else:
            self.dbtool = SQLLiteTool(dbfile)

    def __del__(self):
        del self.dbtool


    def load_stock_data_to_db(self,stock_list, start, end):
        for sid in stock_list:
            try:
                hist_df=akshare.stock_zh_a_hist(symbol=sid,period='daily',start_date=start,end_date=end,adjust='hfq')
                print(hist_df)
                for line in hist_df.itertuples():
                    sql = "INSERT INTO stock_value(rpt_date,stock_no,open,high,low,close,volumn,amplitude,change_percent，turnover_ratio) VALUES ('" + \
                          datetime.strftime(line.日期, '%Y-%m-%d') + "','" + line.股票代码 + "'," + str(line.开盘) +"," + str(line.收盘) + "," + str(line.最高) + "," + str(line.最低) + "," + \
                          str(line.成交量) + "," + str(line.振幅) + ","+ str(line.涨跌幅) + "," + str(line.换手率) + " )"
                    print(sql)
                    self.dbtool.updateDB(sql)
            except HTTPError as e:
                print(e)



def main():
    stock=StockValue()

    stock_list = ["000858"]


    stock.load_stock_data_to_db(stock_list, '20210101', '20240930')


if __name__ == "__main__":
    main()
