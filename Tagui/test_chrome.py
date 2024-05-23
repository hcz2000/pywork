from selenium import webdriver
from urllib.request import urlretrieve
import os
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class DownloadInfo():

    def __init__(self):
        self.url = 'http://music.163.com/#/artist/album?id=101988&limit=120&offset=0'
        self.basePath = os.path.dirname(__file__)

    def makedir(self, name):
        path = os.path.join(self.basePath, name)
        isExist = os.path.exists(path)
        if not isExist:
            os.makedirs(path)
            print('The file is created now.')
        else:
            print('The file existed.')
        #切换到该目录下
        os.chdir(path)
        return path

    def connect(self, url):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome('D:/Program Files/python37/chromedriver.exe',options=chrome_options)
        driver.get(url)
        return driver

    def getFileNames(self, path):
        pic_names = os.listdir(path)
        return pic_names

    def getInfo(self):
        driver = self.connect(self.url)
        driver.switch_to.frame('g_iframe')
        path = self.makedir('Infos')
        pic_names = self.getFileNames(path)
        imgs = driver.find_elements_by_xpath("//div[@class='u-cover u-cover-alb3']/img")
        titles = driver.find_elements_by_xpath("//li/p[@class='dec dec-1 f-thide2 f-pre']/a")
        dates = driver.find_elements_by_xpath("//span[@class='s-fc3']")
        count = 0
        for img in imgs:
            album_name = titles[count].text
            count += 1
            photo_name = album_name.replace('/', '') + '.jpg'
            print(photo_name)
            if photo_name in pic_names:
                print('图片已下载。')
            else:
                urlretrieve(img.get_attribute('src'), photo_name)
        for title in titles:
            print(title.text)
        for date in dates:
            print(date.text)

if __name__ == '__main__':
    obj = DownloadInfo()
    obj.getInfo()