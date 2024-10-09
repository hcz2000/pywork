import sqlite3
import akshare
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import pandas
import matplotlib.pyplot as plt

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



def main():
    hist_df = akshare.stock_zh_a_hist(symbol='601398', period='daily', start_date='20230101', end_date='20231231',
                                      adjust='qfq')
    hist_df['日期']=pandas.to_datetime(hist_df['日期'])
    hist_df.set_index('日期',inplace=True)
    features=hist_df[['开盘','最高','最低','成交量']]
    target=hist_df['收盘']
    X_train,X_test,y_train,y_test=train_test_split(features,target,test_size=0.2,random_state=42)
    model=RandomForestRegressor(n_estimators=100,random_state=42)
    model.fit(X_train,y_train)
    predictions=model.predict(X_test)
    mse=mean_squared_error(y_test,predictions)
    print(f"均方误差：{mse}")

    hist_df['收盘'].plot(title='收盘价走势',xlabel='Date',ylabel='Price')
    font = {'family': 'SimHei', 'weight': 'normal', 'size': 8}
    plt.legend(prop=font)
    plt.show()



if __name__ == "__main__":
    main()
