from selenium import webdriver
from urllib.request import urlretrieve
import os
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
class DownloadInfo():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)



    def connect(self, url):
        #driver = webdriver.PhantomJS()
        #opts = Options()
        #opts.add_argument('--headless')
        #driver = webdriver.Chrome('D:/Program Files/python37/chromedriver.exe',options=opts)
        caps={"browserName":"MicrosoftEdge","version":"","platform":"WINDOWS",
              "ms:edgeOptions":{"extensions":[],"args":["--headless"]}
              }
        driver = webdriver.Edge('D:/Program Files/python37/msedgedriver.exe',capabilities=caps)
        driver.get(url)
        return driver

    def getInfo(self):
        driver = self.connect('https://www.cnblogs.com/lizhanglongceshi/p/12803148.html')
        print('downloading...')
        titles = driver.find_elements_by_xpath("//div[@id='comment_nav']/a")
        #titles = driver.find_elements_by_xpath("//a[@id='blog_nav_sitehome']")
        for title in titles:
            print('title')
            print(title.text)
        time.sleep(10)


if __name__ == '__main__':
    obj = DownloadInfo()
    obj.getInfo()