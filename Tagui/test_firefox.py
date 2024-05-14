from selenium import webdriver
from urllib.request import urlretrieve
import os
from bs4 import BeautifulSoup

class BocwmValue():

    def __init__(self):
        self.url = 'https://www.bocwm.cn/html/1//netWorth/4149.html'
        self.basePath = os.path.dirname(__file__)


    def connect(self, url):
        driver = webdriver.Firefox()
        driver.get(url)
        return driver


    def getInfo(self):
        driver = self.connect(self.url)
        rows = driver.find_elements_by_xpath("//table[@class='layui-table']/tbody/tr")

        for row in rows:
            print(row.get_attribute('innerHTML'))

if __name__ == '__main__':
    obj = BocwmValue()
    obj.getInfo()