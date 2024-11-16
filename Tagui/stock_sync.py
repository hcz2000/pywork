from urllib.error import HTTPError
from datetime import datetime,timedelta
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
        with open('stock.yaml', 'r', encoding='utf-8') as file:
            self.config=yaml.safe_load(file)
        self.basePath = os.path.dirname(__file__)
        if not os.path.exists('data'):
            os.makedirs('data')
        dbfile='data%sstock.db'%os.path.sep
        if not os.path.exists(dbfile):
            self.dbtool = SQLLiteTool(dbfile)
            self.dbtool.updateDB('''create table stock_value( tran_date varchar(10), code varchar(16), open float ,close float, high float, low float,
                volumn float,amplitude float, change_rate float, turnover_rate float, PRIMARY KEY(tran_date,code))''')
        else:
            self.dbtool = SQLLiteTool(dbfile)

    def __del__(self):
        del self.dbtool

    def getLastSyncDate(self, code):
        rows=self.dbtool.queryDB("select tran_date from stock_value where code='%s' order by tran_date desc" % code)
        if rows and rows[0]:
            last_sync_date = rows[0][0]
        else:
            last_sync_date = datetime.now() - timedelta(days=365*2)
            last_sync_date=last_sync_date.replace(month=1,day=1).strftime('%Y-%m-%d')
        print(code, 'LAST_SYNC_DATE:', last_sync_date)
        return (last_sync_date)

    def syncToDB(self):
        stock_list=self.config['stocks']
        for stock in stock_list:
            try:
                stock_code=stock['code']
                print(stock['desc'],'-',stock_code)
                last_sync_date=self.getLastSyncDate(stock_code)
                start=(datetime.strptime(last_sync_date,'%Y-%m-%d')+timedelta(days=1)).strftime('%Y%m%d')
                end=datetime.now().strftime('%Y%m%d')
                if start>end:
                    print('Already Synced')
                    continue
                hist_df = akshare.stock_zh_a_hist(symbol=str(stock_code),period='daily',start_date=start,end_date=end,adjust='hfq')

                print(hist_df)
                for line in hist_df.itertuples():
                    sql = "INSERT INTO stock_value(tran_date,code,open,high,low,close,volumn,amplitude,change_rate,turnover_rate) VALUES ('" + \
                          datetime.strftime(line.日期, '%Y-%m-%d') + "','" + line.股票代码 + "'," + str(line.开盘) +"," + str(line.收盘) + "," + str(line.最高) + "," + str(line.最低) + "," + \
                          str(line.成交量) + "," + str(line.振幅) + ","+ str(line.涨跌幅) + "," + str(line.换手率) + " )"
                    self.dbtool.updateDB(sql)
            except KeyError as e:
                print("股票代码%d不存在"%stock_code)
            except HTTPError as e:
                print(e)



def main():
    stock=StockValue()
    stock.syncToDB()


if __name__ == "__main__":
    main()
