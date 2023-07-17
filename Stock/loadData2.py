import qstock as qs
import pymysql
import datetime


def download_cashflow_rpt():
    stock_df = qs.financial_statement('现金流量表')
    print(stock_df.columns)
    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='root', db='stock')
    for rowindex, orginrow in stock_df.iterrows():
        row=orginrow.fillna(0.00)
        stock_code=row['代码']
        report_date=str(row['公告日'])
        cur = conn.cursor()
        sql= "select * from stock.cashflow_statement where stat_date='%s' and code='%s'"%(report_date,stock_code)
        cur.execute(sql)
        result=cur.fetchall()
        if result and result[0]:
            cur.close()
            continue
        else:
            cur.close()
            cur=conn.cursor()
            cur = conn.cursor()
            sql = "INSERT INTO stock.cashflow_statement(stat_date,code,name,net_cashflow,net_cashflow_yearly_growth,operating_cashflow,operating_cashflow_proportion,investment_cashflow,investment_cashflow_proportion,financial_cashflow,financial_cashflow_proportion) VALUES ('"  \
                 +  report_date + "','" + stock_code + "','"+ row['简称']+"'," + str(row['净现金流'])+ "," + str(row['净现金流同比增长']) + "," + str(row['经营性现金流量净额'])+ "," + str(row['经营性净现金流占比']) +"," \
                 + str(row['投资性现金流量净额'])+","  + str(row['投资性净现金流占比'])+"," + str(row['融资性现金流量净额'])+"," + str(row['融资性净现金流占比'])+ ")"
            print(sql)
            sta = cur.execute(sql)
            cur.close()
    conn.commit()
    conn.close()

def main():
    download_cashflow_rpt()


if __name__ == "__main__":
    main()
