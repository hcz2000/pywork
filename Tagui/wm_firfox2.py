from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.request import urlopen
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import *
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage,PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
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


class Amdbocwmvalue(WmValue):
    def __init__(self,driver):
        super().__init__(driver)
        self.products = self.config['amdbocwm']['products']

    def getNetValue(self, code, url):
        net_values=[]
        last_sync_date = self.getLastSyncDate(code)
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

        while True:
            reversed_list = outputList[::-1]
            for row in reversed_list:
                cols=row.find_elements(By.TAG_NAME, 'td')
                rpt_date = cols[-1].text
                cols[1].click()
                self.driver.switch_to.window(self.driver.window_handles[1])
                time.sleep(1)
                filelink=self.driver.find_element(By.XPATH,"//ul[@class='zzpl_down']/li[@class='a_left']/a")
                fileurl=filelink.get_attribute('href')
                print(fileurl)
                if fileurl.split('.')[-1]=='pdf':
                    #filelink.click()
                    pdf = urlopen(fileurl)
                    tempfile = open('report.pdf', 'wb')
                    CHUNK_SIZE=1024*16
                    while True:
                        chunk = pdf.read(CHUNK_SIZE)  # 读取网页内容
                        if chunk:
                            tempfile.write(chunk)
                        else:
                            break
                    tempfile.close()

                    with open('report.pdf','rb') as pdffile:
                        parser = PDFParser(pdffile)
                        docx = PDFDocument(parser=parser)
                        #parser.set_document(docx)
                        docx.set_parser(parser)
                        docx.initialize()
                        resource = PDFResourceManager()
                        laparams = LAParams()
                        device = PDFPageAggregator(resource, laparams=laparams)
                        interpreter = PDFPageInterpreter(resource, device)

                        for page in docx.get_pages():
                            # 使用页面解释器来读取
                            interpreter.process_page(page=page)
                            # 使用聚合器来获取页面内容 ,接受该页面的LTPage对象
                            layout = device.get_result()
                            # 这里layout是一个LTPage对象 里面存放着这个page解析出的各种对象
                            # 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等
                            # 想要获取文本就获得对象的text属性
                            for out in layout:
                                print(out.text)


                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                #net_value= cols[1].text
                #if rpt_date > last_sync_date:
                #    net_values.append((rpt_date, net_value))

            pagediv = self.driver.find_element(By.XPATH,"//div[@id='page']")
            current_page = pagediv.find_element(By.XPATH,"//ul/li[@class='active']/a").text
            print(current_page)
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

        #self.write2CsvFile(code, net_values)


if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        amdboc = Amdbocwmvalue(driver)
        amdboc.refresh()

