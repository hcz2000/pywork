from selenium import webdriver
from urllib.request import urlretrieve
from datetime import datetime,timedelta
import os
import sys

from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import re

class Mail():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)
        chrome_options = Options()
        #chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome('D:/Program Files/python37/chromedriver.exe',options=chrome_options)
        self.driver.implicitly_wait(5)

    def login(self):
        self.driver.get('https://web.mail.bank-of-china.com/webmail/login/login.do')
        self.driver.find_element_by_id('usernumber').send_keys('6726600')
        self.driver.find_element_by_id('password').send_keys('Huang056!')
        self.driver.find_element_by_id('login_otp').click()
        #print(self.driver.current_url)

    def receive(self):
        #item = self.driver.find_element_by_id("btn_all_mails")
        sidebar=self.driver.find_element_by_id('sidebar')
        item=sidebar.find_elements_by_xpath("//ul[@class='receiveCompose']/li[@class='receive']/a")[0]
        item.click()
        time.sleep(2)

    def go2LastPage(self):
        paginationDiv= self.driver.find_element_by_class_name('pagination')
        if paginationDiv:
            #print(paginationDiv.get_attribute("innerHTML"))
            total_text = paginationDiv.find_element_by_class_name('total').text
            inputElement = paginationDiv.find_element_by_tag_name("input")
            pattern = re.compile(r'(\d+)')
            result = re.search(pattern, total_text)
            if result:
                total_page = result.group(0)
                print('共有%s页邮件，由远至近删除上上月之前邮件'%total_page)
                inputElement.send_keys(total_page)
                inputElement.send_keys(Keys.RETURN)
                time.sleep(2)
        else:
            self.driver.close()
            print("Error:pagination element not found!")
            sys.exit()


    def deleteOldMail(self):
        while True:
            try:
                contentDiv = self.driver.find_element_by_id("content")
                listDiv = contentDiv.find_element_by_id('listBody_sys1')
                tableBody=listDiv.find_element_by_xpath('//table/tbody')
                #print(tableBody.get_attribute('innerHTML'))
                table_data=[]
                rows=tableBody.find_elements_by_tag_name('tr')
                for row in rows:
                    cols=row.find_elements_by_tag_name('td')
                    row_data=[cols[2].text,cols[3].text,cols[5].text]
                    table_data.append(row_data)
                    #print(row_data)

                now = datetime.now()
                delete_months = []
                first_day_of_previous_2_month = (
                    (now.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1)
                delete_months.append(first_day_of_previous_2_month.strftime('%Y-%m-%d')[5:7])
                delete_months.append((first_day_of_previous_2_month - timedelta(days=1)).strftime('%Y-%m-%d')[5:7])
                newest_month= table_data[0][2][0:2]
                if newest_month in delete_months:
                    checkbox=contentDiv.find_element_by_id('checkbox_sys1_all')
                    checkbox.click()
                    time.sleep(1)
                    menuDiv=contentDiv.find_element_by_id('divToolbar_sys1')
                    delete_menu=menuDiv.find_element_by_link_text('彻底删除')
                    #print(delete_menu.get_attribute('innerHTML'))
                    delete_menu.click()
                    time.sleep(1)
                    confirm=self.driver.find_element_by_id('divDialogCloseconfirmbtn_0')
                    confirm.click()
                    time.sleep(1)
                else:
                    break
            except:
                self.driver.refresh()
                time.sleep(5)
                self.go2LastPage()

        self.driver.close()


if __name__ == '__main__':
    tool = Mail()
    tool.login()
    tool.receive()
    tool.go2LastPage()
    tool.deleteOldMail()
    #time.sleep(2)