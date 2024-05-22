from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import yaml

class BocwmValue():

    def __init__(self):
        with open('wm.yaml', 'r') as file:
            config=yaml.safe_load(file)
        self.products = config['bocwm']['products']
        self.basePath = os.path.dirname(__file__)

    def getNetValue(self, url):
        with webdriver.Firefox() as driver:
            driver.implicitly_wait(30)
            driver.get(url)
            contentDiv=driver.find_element(By.ID,'content')
            rows = contentDiv.find_elements(By.XPATH,"//table[@class='layui-table']/tbody/tr")
            for row in rows:
                cols=row.find_elements(By.TAG_NAME,'td')
                print(cols[0].text,cols[1].text,cols[2].text,cols[6].text)

    def refresh(self):
        for product in self.products:
            #(code,url)=url_str.split(':')
            code=product['code']
            url=product['url']
            print(code,url)
            self.getNetValue(url)

if __name__ == '__main__':
    obj = BocwmValue()
    obj.refresh()