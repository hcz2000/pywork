from selenium import webdriver
from urllib.request import urlretrieve
import os
from bs4 import BeautifulSoup
import time
class BookInfo():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)


    def connect(self, url):
        driver = webdriver.Firefox();
        driver.get(url)
        return driver

    def getInfo(self,bookno):
        url="https://m.23sk.net/files/article/html/"+bookno[-2:]+"/"+bookno+"/"
        driver = self.connect(url)
        titles = driver.find_element("//div[@class='block_txt2']/p/a")
        for title in titles:
            print('title')
            print(title.text)


if __name__ == '__main__':
    obj = BookInfo()
    obj.getInfo('127418')