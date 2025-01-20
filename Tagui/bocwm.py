from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import urllib
import pdfplumber
import os
import yaml
from datetime import datetime,timedelta
import time
import sqlite3
import csv

class SQLLiteTool:
    def __init__(self,dbfile):
        self.conn=sqlite3.connect(dbfile)

    def __del__(self):
        self.conn.close()

    def queryDB(self,sql):
        try:
            cur=self.conn.cursor()
            cur.execute(sql)
            result=cur.fetchall()
            cur.close()
            return result
        except Exception as e:
            print(e)

    def updateDB(self,sql):
        try:
            cur=self.conn.cursor()
            cur.execute(sql)
            self.conn.commit()
            return
        except Exception as e:
            print(e)




class BocwmValue():

    def __init__(self,driver):
        self.driver = driver

    def getUrl(self, code):
        self.driver.implicitly_wait(30)
        url="https://www.bocwm.cn/html/1//189/index.html?data="+code+"&type=all"
        self.driver.get(url)
        #self.driver.get('https://www.bocwm.cn/')
        #inputElement=self.driver.find_element(By.ID,'textgj')
        #inputElement.clear()
        #inputElement.send_keys(code)
        #serarchElement = self.driver.find_element(By.XPATH,"//div[@class='new-scope']/div[2]")
        #driver.execute_script("arguments[0].click();", serarchElement)
        #time.sleep(2)
        noticeList=self.driver.find_elements(By.XPATH,"//ul[@class='notice']/li/a")
        for noticeElement in noticeList:
            displayText=noticeElement.text
            if code in displayText  and '产品说明书' not in displayText:
                print(noticeElement.get_attribute("href"),displayText)


if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        boc = BocwmValue(driver)
        boc.getUrl('CYQ368DCZA')
        del boc


