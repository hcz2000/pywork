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
        self.driver.get('https://www.bocwm.cn/')
        contentDiv=self.driver.find_element(By.ID,'textgj')
        control = contentDiv.find_element(By.XPATH,"//div[@class='new-scope']/div[2]")
        control.click()




if __name__ == '__main__':
    with webdriver.Firefox() as driver:
        boc = BocwmValue(driver)
        boc.getUrl('CYQESGGS30D2A')
        del boc


