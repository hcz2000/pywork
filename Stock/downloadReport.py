import qstock as qs
import pymysql
import numpy as np
import time

def download_basics(today, stock_name):
    stock_df=qs.stock_basics(stock_name)
    print(stock_df.columns)
    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='root', db='stock')
    for rowindex, row in stock_df.iterrows():
        stock_code=row['代码']
        report_date=today
        cur = conn.cursor()
        sql= "select * from stock.basics where stat_date='%s' and code='%s'"%(report_date,stock_code)
        cur.execute(sql)
        result=cur.fetchall()
        if result and result[0]:
            cur.close()
            continue
        else:
            cur.close()
            cur=conn.cursor()
            sql = "INSERT INTO stock.basics(stat_date,code,name,industry,revenue,market_value,circulation_market_value,pe_ratio,pb_ratio,roe,gross_profit_ratio,net_profit_ratio) VALUES ('"  \
                 + report_date + "','" + stock_code + "','"+ row['名称']+ "','" + row['所处行业']+ "'," + str(row['净利润']) + "," + str(row['总市值'])+ "," + str(row['流通市值']) +"," \
                 + str(row['市盈率(动)'])+","  + str(row['市净率'])+"," + str(row['ROE'])+"," + str(row['毛利率'])+"," + str(row['净利率'])+ ")"
            print(sql)
            sta = cur.execute(sql)
            cur.close()
    conn.commit()
    conn.close()

def download_top20_holder(stock_name):
    stock_df=qs.stock_holder_top10(stock_name,n=2)
    print(stock_df.columns)
    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='root', db='stock')
    for rowindex, row in stock_df.iterrows():
        stock_code = row['代码']
        report_date = row['日期']
        cur = conn.cursor()
        sql = "select * from stock.top20 where stat_date='%s' and code='%s'" % (report_date, stock_code)
        cur.execute(sql)
        result = cur.fetchall()
        if result and result[0]:
            cur.close()
            continue
        else:
            cur.close()
            cur = conn.cursor()
            sql = "INSERT INTO stock.top20(stat_date,code,seqno,holder,shares,percent,up_and_down,ud_percent) VALUES ('" + \
                 report_date + "','" + stock_code + "',"+str(rowindex+1)+",'" + row['股东名称'] + "'," + str(row['持股数(亿)']) + "," + str(row[
                      '持股比例(%)'])+ ",'" + row['增减'] +"'," + str(row['变动率(%)']) + ")"
            print(sql)
            sta = cur.execute(sql)
            cur.close()
    conn.commit()
    conn.close()

def download_performace_rpt(report_date):
    stock_df = qs.financial_statement('业绩报表', date=report_date)
    print(stock_df.columns)
    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='root', db='stock')
    for rowindex, orginalrow in stock_df.iterrows():
        row=orginalrow.fillna(0.00)
        if row['行业']==0.00:
            industry=''
        else:
            industry= row['行业']
        stock_code=row['代码']
        report_date=row['最新公告日']
        cur = conn.cursor()
        sql= "select * from stock.performance_rpt where stat_date='%s' and code='%s'"%(report_date,stock_code)
        cur.execute(sql)
        result=cur.fetchall()
        if result and result[0]:
            cur.close()
            continue
        else:
            cur.close()
            cur=conn.cursor()
            sql = "INSERT INTO stock.performance_rpt(stat_date,code,name,industry,earnings_per_share,operating_revenue,operating_revenue_yearly_growth,operating_revenue_quarterly_growth,net_profit,net_profit_yearly_growth,net_profit_quarterly_growth,net_asset_per_share,ROE,cash_flow_per_share,gross_profit_margin) VALUES ('"  \
                 + report_date + "','" + stock_code + "','"+ row['简称']+ "','" + industry + "'," + str(row['每股收益'])+ "," + str(row['营业收入']) + "," + str(row['营业收入同比'])+ "," + str(row['营业收入季度环比']) +"," \
                 + str(row['净利润'])+","  + str(row['净利润同比'])+"," + str(row['净利润季度环比'])+"," + str(row['每股净资产'])+"," + str(row['净资产收益率'])+"," + str(row['每股经营现金流量'])+"," + str(row['销售毛利率'])+ ")"
            print(sql)
            sta = cur.execute(sql)
            cur.close()
    conn.commit()
    conn.close()

def download_balance_rpt():
    stock_df = qs.financial_statement('资产负债表')
    print(stock_df.columns)
    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='root', db='stock')
    for rowindex, orginrow in stock_df.iterrows():
        row=orginrow.fillna(0.00)
        stock_code=row['代码']
        report_date=str(row['公告日'])
        cur = conn.cursor()
        sql= "select * from stock.balance_sheet where stat_date='%s' and code='%s'"%(report_date,stock_code)
        cur.execute(sql)
        result=cur.fetchall()
        if result and result[0]:
            cur.close()
            continue
        else:
            cur.close()
            cur=conn.cursor()
            cur = conn.cursor()
            sql = "INSERT INTO stock.balance_sheet(stat_date,code,name,cash,receivable,inventory,asset,asset_yearly_growth,payable,receive_in_advance,debt,debt_yearly_growth,debt_asset_ratio,holder_equity) VALUES ('"  \
                 +  report_date + "','" + stock_code + "','"+ row['简称']+"'," + str(row['货币资金'])+ "," + str(row['应收账款']) + "," + str(row['存货'])+ "," + str(row['总资产']) +"," \
                 + str(row['总资产同比'])+","  + str(row['应付账款'])+"," + str(row['预收账款'])+"," + str(row['总负债'])+"," + str(row['总负债同比'])+"," + str(row['资产负债率'])+"," + str(row['股东权益'])+ ")"
            print(sql)
            sta = cur.execute(sql)
            cur.close()
    conn.commit()
    conn.close()

def download_profit_rpt():
    stock_df = qs.financial_statement('利润表')
    print(stock_df.columns)
    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='root', db='stock')
    for rowindex, orginrow in stock_df.iterrows():
        row=orginrow.fillna(0.00)
        stock_code=row['代码']
        report_date=str(row['公告日'])
        cur = conn.cursor()
        sql= "select * from stock.profit_statement where stat_date='%s' and code='%s'"%(report_date,stock_code)
        cur.execute(sql)
        result=cur.fetchall()
        if result and result[0]:
            cur.close()
            continue
        else:
            cur.close()
            cur=conn.cursor()
            cur = conn.cursor()

            sql = "INSERT INTO stock.profit_statement(stat_date,code,name,net_profit,net_profit_yearly_growth,operating_revenue,operating_revenue_yearly_growth,operating_expense,sale_expense,administration_expense,financial_expense,total_expense,operating_profit,total_profit) VALUES ('"  \
                 +  report_date + "','" + stock_code + "','"+ row['简称']+"'," + str(row['净利润'])+ "," + str(row['净利润同比']) + "," + str(row['营业总收入'])+ "," + str(row['营业总收入同比']) +"," \
                 + str(row['营业支出'])+","  + str(row['销售费用'])+"," + str(row['管理费用'])+"," + str(row['财务费用'])+"," + str(row['营业总支出'])+"," + str(row['营业利润'])+"," + str(row['利润总额'])+ ")"
            print(sql)
            sta = cur.execute(sql)
            cur.close()
    conn.commit()
    conn.close()

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
    today=time.strftime("%Y-%m-%d", time.localtime())
    download_basics(today, '上海电气')
    download_top20_holder('上海电气')
    download_performace_rpt('20220930')
    download_balance_rpt()
    download_profit_rpt()
    download_cashflow_rpt()



if __name__ == "__main__":
    main()