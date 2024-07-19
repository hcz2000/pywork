from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib
import pdfplumber
import os
import yaml
from datetime import datetime,timedelta
import time
import sqlite3

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
        if not os.path.exists('data'):
            os.makedirs('data')
        dbfile='data%swm.db'%os.path.sep
        if not os.path.exists(dbfile):
            self.dbtool = SQLLiteTool(dbfile)
            self.dbtool.updateDB("create table netvalue(code varchar(16), rpt_date varchar(10), value float , PRIMARY KEY(code,rpt_date))")
        else:
            self.dbtool = SQLLiteTool(dbfile)


    def getLastRecord(self, code):
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
    def write2DB(self, code, net_values):
        for row in net_values:
            self.dbtool.updateDB("insert into netvalue values('%s','%s', %s)" % (code, row[0], row[1]))

    def refresh(self):
        for product in self.products:
            self.getNetValue(product)

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

        while True:
            oldest_report = outputList[-1]
            oldest_release_date = oldest_report.find_element(By.CLASS_NAME, 'myDate').get_attribute('innerHTML')
            if oldest_release_date >= last_sync_date:
                next_button=self.driver.find_element(By.XPATH,"//button[@class='btn-next']")
                if next_button.is_enabled():
                    next_button.click()
                    time.sleep(2)
                    outputList = self.driver.find_elements(By.XPATH, "//div[@class='outList']")
                    continue
            break

        while True:
            reversed_list=outputList[::-1]
            for row in reversed_list:
                title=row.find_element(By.XPATH,"./div[@class='myTitleTwo']/span[1]").get_attribute('innerHTML')
                catalog=row.find_element(By.XPATH,"./div[@class='myTitleTwo']/span[2]").get_attribute('innerHTML')
                if not catalog.startswith('净值公告'):
                    continue
                release_date=row.find_element(By.CLASS_NAME,'myDate').get_attribute('innerHTML')
                if release_date>last_sync_date:
                    #last_sync_date=release_date
                    row.click()
                    time.sleep(1)
                    (rpt_date,net_value)=self.parseNetValue()
                    if rpt_date>last_sync_date:
                        net_values.append((rpt_date,net_value))
                    self.driver.back()
                    time.sleep(1)

            prev_button=self.driver.find_element(By.XPATH,"//button[@class='btn-prev']")
            if prev_button.is_enabled():
                prev_button.click()
                time.sleep(2)
                outputList = self.driver.find_elements(By.XPATH, "//div[@class='outList']")
            else:
                break

        self.write2DB(code, net_values)
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
        net_values=[]
        last_record=self.getLastRecord(code)
        last_sync_date = last_record[0]
        self.driver.implicitly_wait(30)
        self.driver.get(url)
        contentDiv=self.driver.find_element(By.ID,'content')
        rows = contentDiv.find_elements(By.XPATH,"//table[@class='layui-table']/tbody/tr")

        if value_type=='net_value':
            for row in rows:
                cols=row.find_elements(By.TAG_NAME,'td')
                (rpt_date, net_value)=(cols[6].text,cols[2].text)
                if rpt_date > last_sync_date:
                    net_values.append((rpt_date, net_value))
                else:
                    break
            net_values=net_values[::-1]
        else:
            revenues=[]
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                (rpt_date, revenue) = (cols[6].text, float(cols[4].text) / 10000)
                if rpt_date > last_sync_date:
                    revenues.append((rpt_date, revenue))
                else:
                    break

            last_net_value=float(last_record[1])
            accumulated_revenue=last_net_value-1.00
            for row in revenues[::-1]:
                accumulated_revenue=accumulated_revenue+(1.0+accumulated_revenue)*row[1]
                (rpt_date,net_value)=(row[0],1.0+accumulated_revenue)
                net_values.append((rpt_date, net_value))

            #print(cols[0].text,cols[1].text,cols[2].text,cols[4].text,cols[6].text)

        self.write2DB(code, net_values)

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

        self.write2DB(code, net_values[::-1])

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
        value_link=self.driver.find_element(By.LINK_TEXT,'产品净值')
        if value_link:
            value_link.click()
            time.sleep(2)
            sub_menuList = self.driver.find_elements(By.XPATH, "//label[@role='radio']")
            sub_menu=sub_menuList[-1].find_element(By.TAG_NAME,'span')
            sub_menu.click()
            time.sleep(2)

        outputList = self.driver.find_elements(By.XPATH, "//table[@class='table2']//tr")[1:]
        newest_report = outputList[0]
        #print(newest_report.get_attribute('innerHTML'))
        newest_release_date = newest_report.find_elements(By.TAG_NAME, 'td')[0].text
        if newest_release_date <= last_sync_date:
            print('No new release:', last_sync_date)
            return

        while True:
            oldest_report = outputList[-1]
            oldest_release_date = oldest_report.find_elements(By.TAG_NAME, 'td')[0].text
            if oldest_release_date >= last_sync_date:
                pagediv=self.driver.find_element(By.XPATH,"//div[@class='fy-cont']")
                current_page=pagediv.get_attribute('current-page')
                page_size=pagediv.get_attribute('page-size')
                total=pagediv.get_attribute('total')
                if int(current_page)*int(page_size)<int(total):
                    next_link= self.driver.find_element(By.LINK_TEXT,'下一页')
                    if next_link:
                        next_link.click()
                        time.sleep(2)
                        outputList = self.driver.find_elements(By.XPATH, "//table[@class='table2']//tr")[1:]
                    else:
                        break
                else:
                    break
            else:
                break

        while True:
            reversed_list = outputList[::-1]
            for row in reversed_list:
                cols=row.find_elements(By.TAG_NAME, 'td')
                rpt_date = cols[0].text
                net_value= cols[1].text
                if rpt_date > last_sync_date:
                    net_values.append((rpt_date, net_value))

            pagediv = self.driver.find_element(By.XPATH, "//div[@class='fy-cont']")
            current_page = pagediv.get_attribute('current-page')
            #print(current_page)
            if current_page=='1':
                break
            prev_link = self.driver.find_element(By.LINK_TEXT,'上一页')
            if prev_link:
                prev_link.click()
                time.sleep(2)
                outputList = self.driver.find_elements(By.XPATH, "//table[@class='table2']//tr")[1:]
            else:
                break

        self.write2DB(code, net_values)


class Amdbocwmvalue(WmValue):
    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['amdbocwm']['products']

    def getNetValue(self, product):
        code = product['code']
        url = product['url']
        net_values=[]
        last_sync_date = self.getLastRecord(code)[0]
        self.driver.implicitly_wait(30)
        self.driver.get(url)

        report_type=self.driver.find_element(By.XPATH, "//dl[@id='bglxspan_box']/dd")
        report_type.find_element(By.LINK_TEXT,'净值报告').click()
        time.sleep(5)

        search_input = self.driver.find_element(By.XPATH, "//div[@class='zzpl_search']/div[1]/ul/li[last()]/input")
        search_input.clear()
        search_input.send_keys(code)
        search_button = self.driver.find_element(By.XPATH,"//div[@class='zzpl_search']/div[last()]/a[1]")
        search_button.click()
        time.sleep(2)

        tbody=self.driver.find_element(By.XPATH, "//div[@id='pro_list']/table/tbody[last()]")
        outputList = tbody.find_elements(By.TAG_NAME, 'tr')
        newest_report = outputList[0]
        newest_release_date = newest_report.find_elements(By.TAG_NAME, 'td')[-1].text
        if newest_release_date <= last_sync_date:
            print('No new release:', last_sync_date)
            return

        while True:
            oldest_report = outputList[-1]
            oldest_release_date = oldest_report.find_elements(By.TAG_NAME, 'td')[-1].text
            if oldest_release_date >= last_sync_date:
                pagediv=self.driver.find_element(By.XPATH,"//div[@id='page']")
                current_page=pagediv.find_element(By.XPATH,"//ul/li[@class='active']/a").text
                last_page=pagediv.find_element(By.XPATH,"//ul/li[last()-1]/a").text
                if int(current_page)<int(last_page):
                    next_link= pagediv.find_element(By.XPATH,"//ul/li[last()]/a")
                    if next_link:
                        next_link.click()
                        time.sleep(2)
                        tbody = self.driver.find_element(By.XPATH, "//div[@id='pro_list']/table/tbody[last()]")
                        outputList = tbody.find_elements(By.TAG_NAME, 'tr')
                    else:
                        break
                else:
                    break
            else:
                break

        while True:
            page_records=[]
            for row in outputList:
                cols=row.find_elements(By.TAG_NAME, 'td')
                release_date = cols[-1].text
                if release_date < last_sync_date:
                    break
                #cols[1].click()
                self.driver.execute_script("arguments[0].click();", cols[1].find_element(By.TAG_NAME, 'a'))
                self.driver.switch_to.window(self.driver.window_handles[1])
                time.sleep(1)
                filelink=self.driver.find_element(By.XPATH,"//ul[@class='zzpl_down']/li[@class='a_left']/a")
                fileurl=filelink.get_attribute('href')
                if fileurl.split('.')[-1]=='pdf':
                    #filelink.click()
                    header = {'Accept': 'text/html,application/xhtml+xml,application/xml',
                              'Accept-Language': 'zh-CN,zh;q=0.9',
                              'Connection': 'keep-alive',
                              'Cookie': 'uuid_tt_dd=10_35489889920-1563497330616-876822; ...... ',
                              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) Gecko/20100101 Firefox/38.0'}
                    request = urllib.request.Request(url=fileurl, headers=header)
                    response = urllib.request.urlopen(request)
                    pdfdata = response.read()  # 读取网页内容
                    with open('report.pdf', 'wb') as tempfile:
                        tempfile.write(pdfdata)
                        tempfile.close()

                    pdf = pdfplumber.open("report.pdf")
                    page = pdf.pages[0]
                    rows = page.extract_table()
                    rpt_date=rows[1][0].replace('/','-')
                    net_value=rows[1][2]
                    if rpt_date > last_sync_date:
                        page_records.append((rpt_date, net_value))

                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

            net_values.extend(page_records[::-1])
            pagediv = self.driver.find_element(By.XPATH,"//div[@id='page']")
            current_page = pagediv.find_element(By.XPATH,"//ul/li[@class='active']/a").text
            if current_page=='1':
                break
            prev_link = pagediv.find_element(By.XPATH,"//ul/li[1]/a")
            if prev_link:
                prev_link.click()
                time.sleep(2)
                tbody = self.driver.find_element(By.XPATH, "//div[@id='pro_list']/table/tbody[last()]")
                outputList = tbody.find_elements(By.TAG_NAME, 'tr')
            else:
                break

        self.write2DB(code, net_values)

class Pinganwmvalue(WmValue):
    def __init__(self, driver):
        super().__init__(driver)
        self.products = self.config['pinganwm']['products']

    def getNetValue(self, product):
        code = product['code']
        url = product['url']
        value_type=product['value_type']
        net_values = []
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

        while True:
            oldest_report = outputList[-1]
            oldest_release_date = oldest_report.find_elements(By.TAG_NAME, 'td')[1].text
            if oldest_release_date >= last_sync_date:
                pagediv = self.driver.find_element(By.XPATH, "//div[@class='ant-spin-container']")
                next_page = pagediv.find_element(By.XPATH, "//li[@title='下一页']")
                if next_page.get_attribute('aria-disabled') == 'true':
                    break
                else:
                    next_link = next_page.find_element(By.TAG_NAME, "a")
                    if next_link:
                        next_link.click()
                        time.sleep(2)
                        tbody = self.driver.find_element(By.XPATH, "//div[@class='ant-table-body']/table/tbody")
                        outputList = tbody.find_elements(By.TAG_NAME, 'tr')
                    else:
                        break
            else:
                break

        accumulated_revenue = last_net_value - 1.00
        while True:
            revenues = []
            for row in outputList[::-1]:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if value_type == 'net_value':
                    rpt_date = cols[1].text
                    net_value = cols[2].text
                    #print(rpt_date,net_value)
                    if rpt_date > last_sync_date:
                        net_values.append((rpt_date, net_value))
                else:
                    (rpt_date, revenue) = (cols[1].text, float(cols[2].text) / 10000)
                    if rpt_date > last_sync_date:
                        revenues.append((rpt_date, revenue))

            if value_type == 'revenue':
                for row in revenues:
                    accumulated_revenue = accumulated_revenue + (1.0 + accumulated_revenue) * row[1]
                    (rpt_date, net_value) = (row[0], 1.0 + accumulated_revenue)
                    #print(rpt_date, net_value)
                    net_values.append((rpt_date, net_value))

            pagediv = self.driver.find_element(By.XPATH, "//div[@class='ant-spin-container']")
            prev_page = pagediv.find_element(By.XPATH, "//li[@title='上一页']")
            if prev_page.get_attribute('aria-disabled') == 'true':
                break
            else:
                prev_link = prev_page.find_element(By.TAG_NAME, "a")
                if prev_link:
                    prev_link.click()
                    time.sleep(2)
                    tbody = self.driver.find_element(By.XPATH, "//div[@class='ant-table-body']/table/tbody")
                    outputList = tbody.find_elements(By.TAG_NAME, 'tr')
                else:
                    break
        self.write2DB(code, net_values)

if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        #cgb = CgbwmValue(driver)
        #cgb.refresh()
        #boc = BocwmValue(driver)
        #boc.refresh()
        #cmb = CmbwmValue(driver)
        #cmb.refresh()
        cib = Cibwmvalue(driver)
        cib.refresh()
        #amdboc = Amdbocwmvalue(driver)
        #amdboc.refresh()
        pingan = Pinganwmvalue(driver)
        pingan.refresh()


