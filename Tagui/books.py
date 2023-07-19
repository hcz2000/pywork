from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.request import urlretrieve
import os
from bs4 import BeautifulSoup
import time
class BookInfo():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)


    def connect(self, url):
        opts = webdriver.FirefoxOptions()
        opts.add_argument('-headless')
        driver = webdriver.Firefox(options=opts);
        driver.get(url)
        return driver

    def getInfo(self,bookno):
        url="https://m.23sk.net/files/article/html/"+bookno[:-len(bookno)+3]+"/"+bookno+"/"
        print(url)
        driver = self.connect(url)
        elements= driver.find_elements(By.XPATH, "//div[@class='block_txt2']/p")
        author = elements[2]
        print(author.text)
        type = elements[3]
        print(type.text)
        update = elements[5]
        print(update.text)
        name = driver.find_element(By.XPATH, "//h2")
        print(name.text)
        info = driver.find_element(By.XPATH, "//div[@class='intro_info']")
        print(info.text)

if __name__ == '__main__':
    obj = BookInfo()
    obj.getInfo('127418')