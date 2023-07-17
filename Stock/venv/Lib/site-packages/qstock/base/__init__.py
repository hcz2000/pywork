#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：python_project 
@File    ：__init__.py.py
@IDE     ：PyCharm 
@Author  ：Jinyi Zhang 
@Date    ：2022/9/29 20:22 
'''
import os
import json
import requests
import pandas as pd
from sqlalchemy import create_engine

sql_path='sqlite:///'
def sql_engine(my_path='c:\\zjy\\Mystock',db_name='stock_data.db'):
    if not os.path.exists(my_path):
        os.makedirs(my_path)
    file_path=os.path.join(my_path,db_name)
    file_path=os.path.abspath(file_path)
    db_path=sql_path+file_path
    engine = create_engine(db_path)
    return engine

def cut_data(data, cut_points, labels=None):
    min_num = data.min()
    max_num = data.max()
    break_points = [min_num] + cut_points + [max_num]
    if not labels:
        labels = range(len(cut_points)+1)
    else:
        labels=[labels[i] for i in range(len(cut_points)+1)]
    dataBin = pd.cut(data,bins=break_points,
        labels=labels,include_lowest=True)
    return dataBin

def send_wechat(corpid,agentid,secret,title="提示信息",content=None):
    #发送请求
    s = requests.session()
    #获取token
    url1=f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={secret}"
    rep = s.get(url1)
    if rep.status_code != 200:
        print("request failed.")
    else:
        token=json.loads(rep.content)['access_token']
    #发送信息设置
    url2 = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + token
    header = {"Content-Type": "application/json"}
    #设置发送信息内容格式
    form_data = {"touser": "@all","toparty": " PartyID1 | PartyID2 ",
             "totag": " TagID1 | TagID2 ","msgtype": "textcard",
             "agentid": agentid,"textcard": {
             "title": title,"description": content,
             "url": "https://www.zhihu.com/people/tkfy920","btntxt": "更多"},"safe": 0}
    rep2 = s.post(url2, data=json.dumps(form_data).encode('utf-8'), headers=header)
    if rep2.status_code != 200:
        print("request failed.")
        return
    return json.loads(rep2.content)