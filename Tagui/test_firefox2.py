from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import yaml
from datetime import datetime,timedelta
import time

class CgbwmValue():

    def __init__(self):
        with open('wm.yaml', 'r') as file:
            config=yaml.safe_load(file)
        self.products = config['cgbwm']['products']
        self.basePath = os.path.dirname(__file__)

    def getInfo(self,code,url):
        with webdriver.Firefox() as driver:
            driver.implicitly_wait(30)
            driver.get(url)
            menus = driver.find_elements(By.XPATH, "//li[@class='parentMenuItem']/span")
            for menu in menus:
                if '信息披露'==menu.text:
                    if menu.get_attribute('class').endswith('has-child-down'):
                        menu.click()
                        time.sleep(1)

            sub_menus = driver.find_elements(By.XPATH, "//li[@class='childMenuItem']/span")
            for sub_menu in sub_menus:
                if '产品公告搜索' == sub_menu.text:
                    if sub_menu.get_attribute('class').endswith('has-child-down2'):
                        sub_menu.click()
                        time.sleep(1)

            sub_menus = driver.find_elements(By.XPATH, "//li[@class='childMenuItem']/span")
            for sub_menu in sub_menus:
                if '运作公告' == sub_menu.text:
                    rpt_menu=sub_menu
                    rpt_menu.click()
                    time.sleep(1)

            input = driver.find_element(By.XPATH,"//input[@class='el-input__inner']")
            input.send_keys(code)
            button = driver.find_element(By.XPATH,"//div[@class='el-input-group__append']/button")
            button.click()
            time.sleep(1)

            last_sync = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            while True:
                outputList=driver.find_elements(By.XPATH,"//div[@class='outList']")
                latest_rpt=outputList[0]
                latest_rpt_date = latest_rpt.find_element(By.CLASS_NAME, 'myDate').get_attribute('innerHTML')
                if latest_rpt_date<=last_sync:
                    break;
                reversed_list=outputList[::-1]
                for row in reversed_list:
                    title=row.find_element(By.CLASS_NAME,'myTitle').get_attribute('innerHTML')
                    if title.endswith('报告'):
                        continue
                    report_date=row.find_element(By.CLASS_NAME,'myDate').get_attribute('innerHTML')
                    if report_date>last_sync:
                        last_sync=report_date
                        print(title, report_date)
                        row.click()
                        time.sleep(10)
                        rpt_menu.click()


    def refresh(self):
        for product in self.products:
            #(code,url)=url_str.split(':')
            code=product['code']
            url=product['url']
            print(code,url)
            self.getInfo(code,url)

if __name__ == '__main__':
    obj = CgbwmValue()
    obj.getInfo('XFLCXFTF0008','https://www.cgbwmc.com.cn/#/runningNotice')