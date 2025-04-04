from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import urllib
import pdfplumber
import os
import yaml
from datetime import datetime,timedelta
import time
import sqlite3
import csv

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

class WmValue():
    def __init__(self,driver):
        with open('wm.yaml', 'r', encoding='utf-8') as file:
            self.config=yaml.safe_load(file)
        self.driver=driver
        self.basePath = os.path.dirname(__file__)
        #self.persistentStorage='file'
        self.persistentStorage = self.config['wm']['storage']
        if not os.path.exists('data'):
            os.makedirs('data')
        dbfile='data%swm.db'%os.path.sep
        if not os.path.exists(dbfile):
            self.dbtool = SQLLiteTool(dbfile)
            self.dbtool.updateDB("create table netvalue(code varchar(16), rpt_date varchar(10), value float , PRIMARY KEY(code,rpt_date))")
        else:
            self.dbtool = SQLLiteTool(dbfile)

    def __del__(self):
        del self.dbtool

    def getLastRecordFromDB(self, code):
        rows=self.dbtool.queryDB("select rpt_date,value from netvalue where code='%s' order by rpt_date desc" % code)
        if rows and rows[0]:
            last_sync_date = rows[0][0]
            last_value=rows[0][1]
            print(code,'LAST_SYNC_DATE:',last_sync_date)
        else:
            last_sync_date=datetime.now() - timedelta(days=365*2)
            last_sync_date=last_sync_date.replace(month=12,day=31).strftime('%Y-%m-%d')
            last_value= str(1.0000)
            #print(last_sync_date)
        return (last_sync_date,last_value)

    def getLastRecordFromCsvFile(self, code):
        filename='./data/%s.csv' % code
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as datafile:
                datafile.seek(0,2)
                position = datafile.tell()
                position=position-3
                while position>=0:
                    datafile.seek(position)
                    last_char=datafile.read(1)
                    if last_char == '\n':
                        break
                    position -= 1

                last_line=datafile.readline()
                last_sync_date = last_line.split(',')[0].strip()
                last_value=last_line.split(',')[1].strip()
                print(code,'LAST_SYNC_DATE:',last_sync_date)
        else:
            last_sync_date=datetime.now() - timedelta(days=365*2)
            last_sync_date=last_sync_date.replace(month=12,day=31).strftime('%Y-%m-%d')
            last_value= str(1.0000)
            #print(last_sync_date)
        return (last_sync_date,last_value)

    def getLastRecord(self, code):
        if self.persistentStorage=='file':
            return self.getLastRecordFromCsvFile(code)
        else:
            return self.getLastRecordFromDB(code)

    def write2DB(self, code, net_values):
        for row in net_values:
            self.dbtool.updateDB("insert into netvalue values('%s','%s', %s)" % (code, row[0], row[1]))

    def write2CsvFile(self,code,net_values):
        with open('./data/%s.csv' % code, 'a', encoding='utf-8', newline='') as datafile:
            writer = csv.writer(datafile)
            for row in net_values:
                writer.writerow(row)

    def writeRecords(self,code,net_values):
        if self.persistentStorage=='file':
            self.write2CsvFile(code,net_values)
        else:
            self.write2DB(code,net_values)

    def refresh(self):
        for product in self.products:
            self.getNetValue(product)
            time.sleep(2)

class CgbwmValue(WmValue):
    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['cgbwm']['products']

    def getNetValue(self, product):
        code=product['code']
        url = product['url']
        net_values=[]
        last_sync_date = self.getLastRecord(code)[0]
        self.driver.implicitly_wait(30)
        self.driver.get(url)
        menus = self.driver.find_elements(By.XPATH, "//li[@class='parentMenuItem']/span")
        for menu in menus:
            if '信息披露'==menu.text:
                if menu.get_attribute('class').endswith('has-child-down'):
                    menu.click()
                    time.sleep(2)

        sub_menus = self.driver.find_elements(By.XPATH, "//li[@class='childMenuItem']/span")
        for sub_menu in sub_menus:
            if '产品公告搜索' == sub_menu.text:
                search_menu=sub_menu
                if sub_menu.get_attribute('class').endswith('has-child-up2'):
                    sub_menu.click()
                    time.sleep(2)
                else:
                    sub_menu.click()
                    time.sleep(2)
                    sub_menu.click()
                    time.sleep(2)
                break

        search_input = self.driver.find_element(By.XPATH, "//input[@class='el-input__inner']")
        search_input.clear()
        search_input.send_keys(code)
        search_button = self.driver.find_element(By.XPATH,"//div[@class='el-input-group__append']/button")
        search_button.click()
        time.sleep(2)

        outputList = self.driver.find_elements(By.XPATH, "//div[@class='outList']")
        newest_report = outputList[0]
        newest_release_date = newest_report.find_element(By.CLASS_NAME, 'myDate').get_attribute('innerHTML')
        if newest_release_date <= last_sync_date:
            print('No new release:',last_sync_date)
            return

        stop=False
        while stop==False:
            for row in outputList:
                spanElements=row.find_elements(By.XPATH,"./div[@class='myTitleTwo']/span")
                if len(spanElements)<2:
                    continue
                title=spanElements[0].get_attribute('innerHTML')
                catalog=spanElements[1].get_attribute('innerHTML')
                if not catalog.startswith('净值公告'):
                    continue
                release_date=row.find_element(By.CLASS_NAME,'myDate').get_attribute('innerHTML')
                if release_date > last_sync_date:
                    self.driver.execute_script("arguments[0].click()", row)
                    time.sleep(1)
                    (rpt_date, net_value) = self.parseNetValue()
                    if rpt_date > last_sync_date:
                        net_values.append((rpt_date, net_value))
                    self.driver.back()
                    time.sleep(1)
                else:
                    stop=True
                    break
            if not stop:
                next_button = self.driver.find_element(By.XPATH, "//button[@class='btn-next']")
                if next_button.is_enabled():
                    next_button = self.driver.find_element(By.XPATH, "//button[@class='btn-next']")
                    if next_button.is_enabled():
                        self.driver.execute_script("arguments[0].click()", next_button)
                        time.sleep(2)
                        outputList = self.driver.find_elements(By.XPATH, "//div[@class='outList']")
                        continue
                else:
                    break

        self.writeRecords(code, net_values[::-1])

    def parseNetValue(self):
        cols=self.driver.find_elements(By.XPATH,"//div[@id='news_content_id']/table/tbody/tr[2]/td/span")
        code=cols[0].text
        net_value=cols[4].text
        rpt_date=cols[6].text
        print(code,rpt_date,net_value)
        return rpt_date,net_value


class BocwmValue(WmValue):

    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['bocwm']['products']

    def getNetValue(self, product):
        code = product['code']
        url = product['url']
        value_type=product['value_type']
        last_record=self.getLastRecord(code)
        last_sync_date = last_record[0]
        self.driver.implicitly_wait(30)
        self.driver.get(url)
        contentDiv=self.driver.find_element(By.ID,'content')
        rows = contentDiv.find_elements(By.XPATH,"//table[@class='layui-table']/tbody/tr")

        net_values = []
        revenues = []
        stop=False
        while stop==False:
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if value_type=='net_value':
                    (rpt_date, net_value) = (cols[6].text, cols[2].text)
                    if rpt_date > last_sync_date:
                        net_values.append((rpt_date, net_value))
                    else:
                        stop=True
                        break
                else:
                    (rpt_date, revenue) = (cols[6].text, float(cols[4].text) / 10000)
                    if rpt_date > last_sync_date:
                        revenues.append((rpt_date, revenue))
                    else:
                        stop=True
                        break
            if not stop:
                next_button = self.driver.find_element(By.XPATH, "//button[@class='btn-next']")
                if next_button.is_enabled():
                    self.driver.execute_script("arguments[0].click()",next_button)
                    time.sleep(2)
                    rows = contentDiv.find_elements(By.XPATH, "//table[@class='layui-table']/tbody/tr")
                    continue
                else:
                    break


        if value_type=='net_value':
            net_values=net_values[::-1]
        else:
            last_net_value=float(last_record[1])
            accumulated_revenue=last_net_value-1.00
            for item in revenues[::-1]:
                accumulated_revenue=accumulated_revenue+(1.0+accumulated_revenue)*item[1]
                (rpt_date,net_value)=(item[0],1.0+accumulated_revenue)
                net_values.append((rpt_date, net_value))

            #print(cols[0].text,cols[1].text,cols[2].text,cols[4].text,cols[6].text)

        self.writeRecords(code, net_values)


class CmbwmValue(WmValue):
    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['cmbwm']['products']

    def getNetValue(self, product):
        code = product['code']
        url = product['url']
        net_values=[]
        last_sync_date = self.getLastRecord(code)[0]
        self.driver.implicitly_wait(30)
        self.driver.get(url+'?prodTradeCode=%s&prodClcMode=01&finType=P'%code)
        contentDiv=self.driver.find_element(By.CLASS_NAME,'proTabList')
        #print(contentDiv.get_attribute('innerHTML'))
        menuList=contentDiv.find_elements(By.CSS_SELECTOR,'.item.text-14.flex')
        for menu in menuList:
            cmd=menu.text
            if menu.text=='产品净值':
                menu.click()
                time.sleep(2)
                sub_menuList = self.driver.find_elements(By.CSS_SELECTOR, '.proValue_btn.text-14')
                for sub_menu in sub_menuList:
                    if sub_menu.text=='近3年':
                        sub_menu.click()
                        #print(contentDiv.get_attribute('innerHTML'))
                        time.sleep(2)
                        break

        rows=contentDiv.find_elements(By.XPATH,"//table[@class='el-table__body']/tbody/tr")
        for row in rows:
            cols=row.find_elements(By.TAG_NAME,"td")
            rpt_date= (cols[0].find_element(By.TAG_NAME,'div')).text
            net_value=(cols[1].find_element(By.TAG_NAME,'div')).text
            if rpt_date > last_sync_date:
                net_values.append((rpt_date, net_value))
                print(rpt_date,net_value)
            else:
                break

        self.writeRecords(code, net_values[::-1])

class Cibwmvalue(WmValue):
    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['cibwm']['products']

    def getNetValue(self, product):
        code = product['code']
        url = product['url']
        net_values=[]
        last_sync_date = self.getLastRecord(code)[0]
        self.driver.implicitly_wait(30)
        self.driver.get(url)
        value_link=self.driver.find_element(By.XPATH,"//div[@id='louti-yj-area']/div[@class='guide-box']/ul/li[2]")
        if value_link:
            value_link.click()
            time.sleep(2)

        outputList = self.driver.find_elements(By.XPATH, "//div[@class='yj-info-box']/ul[@class='info']/li")
        rpt_date = outputList[0].find_element(By.XPATH, "//span[@class='value']").text
        if rpt_date <= last_sync_date:
            print('No new release:', last_sync_date)
            return
        else:
            net_value=outputList[1].find_element(By.XPATH, "//span[@class='value']").text
            net_values.append((rpt_date, net_value))
            self.writeRecords(code, net_values)

class Pinganwmvalue(WmValue):
    def __init__(self, driver):
        super().__init__(driver)
        self.products = self.config['pinganwm']['products']

    def getNetValue(self, product):
        code = product['code']
        url = product['url']
        value_type=product['value_type']
        last_record=self.getLastRecord(code)
        last_sync_date = last_record[0]
        last_net_value = float(last_record[1])
        self.driver.implicitly_wait(30)
        self.driver.get(url)

        tabs = self.driver.find_elements(By.XPATH, "//div[@role='tab']")
        tabs[2].click()
        time.sleep(2)

        tbody = self.driver.find_element(By.XPATH, "//div[@class='ant-table-body']/table/tbody")
        outputList = tbody.find_elements(By.TAG_NAME, 'tr')
        newest_report = outputList[0]
        newest_release_date = newest_report.find_elements(By.TAG_NAME, 'td')[1].text
        if newest_release_date <= last_sync_date:
            print('No new release:', last_sync_date)
            return

        net_values = []
        revenues = []
        stop = False
        while stop == False:
            for row in outputList:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if value_type == 'net_value':
                    (rpt_date, net_value) = (cols[1].text, cols[2].text)
                    if rpt_date > last_sync_date:
                        net_values.append((rpt_date, net_value))
                    else:
                        stop = True
                        break
                else:
                    (rpt_date, revenue) = (cols[1].text, float(cols[2].text) / 10000)
                    if rpt_date > last_sync_date:
                        revenues.append((rpt_date, revenue))
                    else:
                        stop = True
                        break
            if not stop:
                pagediv = self.driver.find_element(By.XPATH, "//div[@class='ant-spin-container']")
                next_page = pagediv.find_element(By.XPATH, "//li[@title='下一页']")
                if next_page.get_attribute('aria-disabled') == 'true':
                    break
                else:
                    next_link = next_page.find_element(By.TAG_NAME, "a")
                    self.driver.execute_script("arguments[0].click()", next_link)
                    time.sleep(2)
                    tbody = self.driver.find_element(By.XPATH, "//div[@class='ant-table-body']/table/tbody")
                    outputList = tbody.find_elements(By.TAG_NAME, 'tr')
                    continue


        if value_type == 'net_value':
            net_values = net_values[::-1]
        else:
            last_net_value = float(last_record[1])
            accumulated_revenue = last_net_value - 1.00
            for item in revenues[::-1]:
                accumulated_revenue = accumulated_revenue + (1.0 + accumulated_revenue) * item[1]
                (rpt_date, net_value) = (item[0], 1.0 + accumulated_revenue)
                net_values.append((rpt_date, net_value))

        self.writeRecords(code, net_values)

if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        cgb = CgbwmValue(driver)
        cgb.refresh()
        del cgb
        boc = BocwmValue(driver)
        boc.refresh()
        del boc
        cmb = CmbwmValue(driver)
        cmb.refresh()
        del cmb
        pingan = Pinganwmvalue(driver)
        pingan.refresh()
        del pingan
        cib = Cibwmvalue(driver)
        cib.refresh()
        del cib




