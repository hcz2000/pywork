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
import psycopg2

class Mail():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)
        chrome_options = Options()
        #chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome('D:/Program Files/python37/chromedriver.exe',options=chrome_options)
        self.driver.implicitly_wait(5)
        self.conn = psycopg2.connect(host='22.136.69.142',port=5432,dbname='cfss',user='cfss',password='openGauss!')
        result = self.queryDB('select msg_id,sync_mail_time from mail.track')
        if not result or not result[0]:
            self.sync_msg_id='00000000000'
            self.sync_mail_time='2024-01-01 00:00:00'
        else:
            self.sync_msg_id=result[0][0]
            self.sync_mail_time=result[0][1]

    def __del__(self):
        self.conn.close()
        self.driver.close()

    def queryDB(self, sql):
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            #result=[r for r in cur]
            result = cur.fetchall()
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

    def batchUpdateDB(self,statements):
        try:
            cur=self.conn.cursor()
            for sql in statements:
                cur.execute(sql)
            self.conn.commit()
            return
        except Exception as e:
            print('batchUpdateDB Error',e)


    def updateTrack(self,sync_msg_id,sync_mail_time):
        self.updateDB("update mail.track set msg_id='%s',sync_mail_time='%s"%(sync_msg_id,sync_mail_time))

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

    def go2SyncPointPage(self):
        sync_time = self.sync_mail_time[5:16]
        while True:
            try:
                contentDiv = self.driver.find_element_by_id("content")
                listDiv = contentDiv.find_element_by_id('listBody_sys1')
                rows = listDiv.find_elements_by_xpath('//table/tbody/tr')
                earlest_row = rows[-1]
                earlest_msg_id = earlest_row.get_attribute('data-mid')
                cols = earlest_row.find_elements_by_tag_name('td')
                earlist_mail_time = cols[5]
                if sync_time < earlist_mail_time.text:
                    paginationDiv = self.driver.find_element_by_class_name('pagination')
                    nextPageLink=paginationDiv.find_element_by_link_text('下一页')
                    if nextPageLink:
                        if nextPageLink.get_attribute('onClick'):
                            nextPageLink.click()
                            time.sleep(2)
                            continue
                        else:
                            break
                    else:
                        break
                else:
                    break;
            except BaseException as e:
                print(e)
                self.driver.refresh()
                time.sleep(2)

    def traverseSuitablePages(self):
        while True:
            try:
                self.traverseOnePage()
                paginationDiv = self.driver.find_element_by_class_name('pagination')
                previousPageLink = paginationDiv.find_element_by_link_text('上一页')
                if previousPageLink.get_attribute('onClick'):
                    previousPageLink.click()
                    time.sleep(5)
                else:
                    break
            except BaseException as e:
                print(e)
                self.driver.refresh()
                time.sleep(5)


    def traverseOnePage(self):
        try:
            #sync_date = datetime.now().strftime('%Y-%m-%d')[5:10]
           # sync_date=self.sync_mail_time[5:10]
            sync_time = self.sync_mail_time[5:16]
            contentDiv = self.driver.find_element_by_id("content")
            listDiv = contentDiv.find_element_by_id('listBody_sys1')
            rows = listDiv.find_elements_by_xpath('//table/tbody/tr')
            table_data=[]
            for row in rows:
                msg_id=row.get_attribute('data-mid')
                cols=row.find_elements_by_tag_name('td')
                #mail_date = cols[5].text[0:5]
                mail_time=cols[5].text
                #if sync_date==mail_date:
                if sync_time < mail_time:
                    table_data.append([row,msg_id,cols[2].text,cols[3].text,cols[5].text])

            reversed_data=table_data[::-1]
            for row_data in reversed_data:
                self.readMail(contentDiv,row_data[0],row_data[1],row_data[3])
        except BaseException as e:
            print(e)
            self.driver.refresh()
            time.sleep(5)



    def readMail(self,contentDiv,row,msg_id,title):
        link = row.find_element_by_link_text(title)
        link.click()
        time.sleep(2)
        readDiv=contentDiv.find_element_by_id('tab_b_readMail'+msg_id)
        iframe=readDiv.find_element_by_id('ifrmReadmail_Content_readMail'+msg_id)
        main_frame=self.driver.switch_to.frame(iframe)
        time.sleep(1)

        sender_str=''
        mailHeadDiv=self.driver.find_element_by_id('mailhead')
        senderName=mailHeadDiv.find_element_by_class_name('gAddrN').text
        senderBox=mailHeadDiv.find_element_by_class_name('gAddrE').text
        sender_str=senderName.strip()+senderBox.strip()
        print('Sender:',sender_str)

        receiver_str=''
        #receivers=mailHeadDiv.find_element_by_id('readMail'+msg_id+'to')
        receivers=mailHeadDiv.find_elements_by_class_name('card_contact_t')
        for receiver in receivers:
            receiver_name=receiver.find_element_by_tag_name('input').get_attribute('value')
            receiver_box=receiver.find_element_by_class_name('card_contact_p').get_attribute('innerHTML')
            receiver_str=receiver_str+'"'+receiver_name+'"<'+receiver_box+'>;'
        receiver_str=receiver_str.rstrip(':')
        print('Receiver:',receiver_str)

        mail_time=''
        mailInfoDiv=mailHeadDiv.find_element_by_id('readMailInfo')
        sub_divs=mailInfoDiv.find_elements_by_class_name('rMList')
        for sub_div in sub_divs:
            sub_title=(sub_div.find_element_by_tag_name('span').get_attribute('innerHTML'))
            if sub_title=='时　间：':
                mail_time=sub_div.find_element_by_tag_name('div').get_attribute('innerHTML')
        print("Time:",mail_time)

        copyto_str=''
        try:
            copyto_div = mailInfoDiv.find_element_by_id('readMail'+msg_id+'cc')
            if copyto_div:
                copyto_spans=copyto_div.find_elements_by_tag_name('span')
                for copyto_span in copyto_spans:
                    copyto_str=copyto_str+copyto_span.get_attribute('innerHTML').replace('&nbsp;&lt;','<').replace('&gt;','>')+';'
        except BaseException as e:
            print('No copy to section')
        copyto_str=copyto_str.rstrip(';')
        print('CopyTo:',copyto_str)

        attach_filenames=[]
        file_names= mailHeadDiv.find_elements_by_class_name("download-fileName")
        for file_name in file_names:
            attach_filenames.append(file_name.get_attribute('title').replace(u'\xa0',u' '))
        attach_filename_str=''
        for attach_filename in attach_filenames:
            attach_filename_str=attach_filename_str+attach_filename+';'
        attach_filename_str=attach_filename_str.rstrip(';')
        print('Attachments:',attach_filename_str)

        download_links=mailHeadDiv.find_elements_by_link_text('下载')
        for download_link in download_links:
            download_link.click()
            time.sleep(2)

        images=[]
        for filename in attach_filenames:
            data=open('C:/Users/6726600/Downloads/'+filename,'rb').read()
            images.append(psycopg2.Binary(data))

        image1= images[0] if len(images)>0 else 'NULL'
        image2= images[1] if len(images)>1 else 'NULL'
        image3= images[1] if len(images)>1 else 'NULL'

        mail_title=mailHeadDiv.find_element_by_class_name('hTitle').text
        print('Title:',mail_title)

        contentFrame=self.driver.find_element_by_id('mailContent')
        self.driver.switch_to.frame(contentFrame)
        mail_text=self.driver.find_element_by_tag_name('body').text
        #print("Content:",mail_text)

        sqls=[]
        sqls.append('''insert into mail.mailbox(msg_id,receive_time,sender,receiver,copy_to,mail_title,mail_text,attach_filenames,attach_img1,attach_img2,attach_img3)
                  values('%s','%s','%s','%s','%s','%s','%s','%s',%s,%s,%s)'''
                    %(msg_id,mail_time,sender_str,receiver_str,copyto_str,mail_title,mail_text,attach_filename_str,image1,image2,image3));
        self.batchUpdateDB(sqls)

        print('-------------------------------------------------------------')


        self.driver.switch_to.frame(main_frame)
        page_tab=self.driver.find_element_by_id('tab_h_readMail'+msg_id)
        page_tab.find_element_by_tag_name('a').click()
        time.sleep(2)

if __name__ == '__main__':
    tool = Mail()
    tool.login()
    tool.receive()
    tool.go2SyncPointPage()
    tool.traverseSuitablePages()
    #time.sleep(2)