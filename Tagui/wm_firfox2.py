from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import yaml
from datetime import datetime,timedelta
import time
import csv

class WmValue():

    def __init__(self,driver):
        with open('wm.yaml', 'r', encoding='utf-8') as file:
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


class Cibwmvalue(WmValue):
    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['cibwm']['products']

    def getNetValue(self, code, url):
        net_values=[]
        last_sync_date = self.getLastSyncDate(code)
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
        print(newest_report.get_attribute('innerHTML'))
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
            print(current_page)
            if current_page=='1':
                break
            prev_link = self.driver.find_element(By.LINK_TEXT,'上一页')
            if prev_link:
                prev_link.click()
                time.sleep(2)
                outputList = self.driver.find_elements(By.XPATH, "//table[@class='table2']//tr")[1:]
            else:
                break

        self.write2CsvFile(code, net_values)


if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        cib = Cibwmvalue(driver)
        cib.refresh()
