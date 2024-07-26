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


class Amdbocwmvalue(WmValue):
    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['amdbocwm']['products']

    def getNetValue(self, product):
        code = product['code']
        url = product['url']
        net_values=[]
        last_sync_date = self.getLastRecord(code)[0]
        self.driver.implicitly_wait(10)
        print(datetime.now(),'访问',url)
        self.driver.get(url)
        print(datetime.now(),'get(url)返回')

        report_type=self.driver.find_element(By.XPATH, "//dl[@id='bglxspan_box']/dd")
        print(datetime.now(),'0001')
        report_type.find_element(By.LINK_TEXT,'净值报告').click()
        time.sleep(5)
        print(datetime.now(),'0002')
        search_input = self.driver.find_element(By.XPATH, "//div[@class='zzpl_search']/div[1]/ul/li[last()]/input")
        search_input.clear()
        search_input.send_keys(code)
        print(datetime.now(),'0003')
        search_button = self.driver.find_element(By.XPATH,"//div[@class='zzpl_search']/div[last()]/a[1]")
        search_button.click()
        time.sleep(2)
        print(datetime.now(),'0004')

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

        self.write2CsvFile(code, net_values)


if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        amdboc = Amdbocwmvalue(driver)
        amdboc.refresh()

