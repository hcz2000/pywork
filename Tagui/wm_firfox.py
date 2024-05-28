from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import yaml
from datetime import datetime,timedelta
import time
import csv

class WmValue():

    def __init__(self,driver):
        with open('wm.yaml', 'r') as file:
            self.config=yaml.safe_load(file)
        self.driver=driver
        self.basePath = os.path.dirname(__file__)
        if not os.path.exists('data'):
            os.makedirs('data')


    def getLastSyncDate(self,code):
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
                #print(last_line)
                last_sync_date = last_line.split(',')[0].strip()
                print(code,'LAST_SYNC_DATE:',last_sync_date)
        else:
            last_sync_date=datetime.now() - timedelta(days=365*2)
            last_sync_date=last_sync_date.replace(month=12,day=31).strftime('%Y-%m-%d')
            #print(last_sync_date)
        return last_sync_date
    def write2CsvFile(self,code,net_values):
        with open('./data/%s.csv' % code, 'a', encoding='utf-8', newline='') as datafile:
            writer = csv.writer(datafile)
            for row in net_values:
                writer.writerow(row)

    def refresh(self):
        for product in self.products:
            code=product['code']
            url=product['url']
            print(code,url)
            self.getNetValue(code, url)

class CgbwmValue(WmValue):
    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['cgbwm']['products']

    def getNetValue(self, code, url):
        net_values=[]
        last_sync_date = self.getLastSyncDate(code)
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
                    last_sync_date=release_date
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

        self.write2CsvFile(code,net_values)
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

    def getNetValue(self, code, url):
        net_values=[]
        last_sync_date = self.getLastSyncDate(code)
        self.driver.implicitly_wait(30)
        self.driver.get(url)
        contentDiv=self.driver.find_element(By.ID,'content')
        rows = contentDiv.find_elements(By.XPATH,"//table[@class='layui-table']/tbody/tr")
        for row in rows:
            cols=row.find_elements(By.TAG_NAME,'td')
            (rpt_date, net_value)=(cols[6].text,cols[2].text)
            if rpt_date > last_sync_date:
                net_values.append((rpt_date, net_value))
            #print(cols[0].text,cols[1].text,cols[2].text,cols[6].text)

        with open('./data/%s.csv' % code, 'a', encoding='utf-8', newline='') as datafile:
            writer = csv.writer(datafile)
            for row in net_values[::-1]:
                writer.writerow(row)


if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        cgb = CgbwmValue(driver)
        cgb.refresh()
        boc = BocwmValue(driver)
        boc.refresh()
