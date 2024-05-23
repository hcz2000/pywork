from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import yaml
from datetime import datetime,timedelta
import csv

class BocwmValue():

    def __init__(self):
        with open('wm.yaml', 'r') as file:
            config=yaml.safe_load(file)
        self.products = config['bocwm']['products']
        self.basePath = os.path.dirname(__file__)

    def getNetValue(self, code, url):
        net_values=[]
        last_sync_date = self.getLastSyncDate(code)
        with webdriver.Firefox() as driver:
            driver.implicitly_wait(30)
            driver.get(url)
            contentDiv=driver.find_element(By.ID,'content')
            rows = contentDiv.find_elements(By.XPATH,"//table[@class='layui-table']/tbody/tr")
            for row in rows:
                cols=row.find_elements(By.TAG_NAME,'td')
                (rpt_date, net_value)=(cols[6].text,cols[2].text)
                if rpt_date > last_sync_date:
                    net_values.append((rpt_date, net_value))
                #print(cols[0].text,cols[1].text,cols[2].text,cols[6].text)

            with open('./data/%s.csv' % code, 'a', encoding='utf-8', newline='') as datafile:
                writer = csv.writer(datafile)
                for row in net_values:
                    writer.writerow(row)

    def getLastSyncDate(self, code):
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
                # print(last_line)
                last_sync_date = last_line.split(',')[0].strip()
                print(code, 'LAST_SYNC_DATE:', last_sync_date)
        else:
            last_sync_date = datetime.now() - timedelta(days=365 * 2)
            last_sync_date = last_sync_date.replace(month=12, day=31).strftime('%Y-%m-%d')
            # print(last_sync_date)
        return last_sync_date

    def refresh(self):
        for product in self.products:
            #(code,url)=url_str.split(':')
            code=product['code']
            url=product['url']
            print(code,url)
            self.getNetValue(code,url)

if __name__ == '__main__':
    obj = BocwmValue()
    obj.refresh()