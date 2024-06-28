from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib
import pdfplumber
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

    def getLastRecord(self, code):
        filename = './data/%s.csv' % code
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as datafile:
                datafile.seek(0, 2)
                position = datafile.tell()
                position = position - 3
                while position >= 0:
                    datafile.seek(position)
                    last_char = datafile.read(1)
                    if last_char == '\n':
                        break
                    position -= 1

                last_line = datafile.readline()
                last_sync_date = last_line.split(',')[0].strip()
                last_value = last_line.split(',')[1].strip()
                print(code, 'LAST_SYNC_DATE:', last_sync_date)
        else:
            last_sync_date = datetime.now() - timedelta(days=365 * 2)
            last_sync_date = last_sync_date.replace(month=12, day=31).strftime('%Y-%m-%d')
            last_value = str(1.0000)
            # print(last_sync_date)
        return (last_sync_date, last_value)
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
            self.getNetValue(product)


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
            reversed_list = outputList[::-1]
            for row in reversed_list:
                cols = row.find_elements(By.TAG_NAME, 'td')
                release_date = cols[1].text
                if release_date < last_sync_date:
                    break

                time.sleep(1)

                if value_type == 'net_value':
                    rpt_date = cols[1].text
                    net_value = cols[2].text
                    print(rpt_date,net_value)
                    if rpt_date > last_sync_date:
                        net_values.append((rpt_date, net_value))
                else:
                    revenues = []
                    for row in reversed_list:
                        cols = row.find_elements(By.TAG_NAME, 'td')
                        (rpt_date, revenue) = (cols[1].text, float(cols[2].text) / 10000)
                        if rpt_date > last_sync_date:
                            revenues.append((rpt_date, revenue))
                        else:
                            break

                    for row in revenues[::-1]:
                        accumulated_revenue = accumulated_revenue + (1.0 + accumulated_revenue) * row[1]
                        (rpt_date, net_value) = (row[0], 1.0 + accumulated_revenue)
                        print(rpt_date, net_value)
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

        self.write2CsvFile(code, net_values)


if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        amdboc = Pinganwmvalue(driver)
        amdboc.refresh()

