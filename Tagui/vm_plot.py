import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import yaml
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FC
import numpy as np
from datetime import datetime, timedelta
import subprocess
import sqlite3
import os
import math

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

class QtDemo(QWidget):

  def __init__(self, products,parent=None):
    super(QtDemo, self).__init__(parent)
    with open('wm.yaml', 'r', encoding='utf-8') as file:
      config = yaml.safe_load(file)
      self.persistentStorage = config['wm']['storage']
      if self.persistentStorage=='db':
        dbfile = 'data%swm.db' % os.path.sep
        self.dbtool = SQLLiteTool(dbfile)
    resolution=QApplication.primaryScreen().geometry()
    self.resolution=resolution
    #print(resolution.width(),resolution.height())

    #设置导航窗垂直布局
    leftLayout = QVBoxLayout()
    self.checkboxes = {}
    self.con_checkbox= {}
    self.group_selected={}
    for k,v in products.items():
      groupBox = QGroupBox(k)
      groupBox.setFlat(False)
      grid_layout = QGridLayout()
      checkboxes=[]
      checkbox = QCheckBox('全选')
      font = QFont('Arial', 6)
      checkbox.setFont(font)
      checkbox.stateChanged.connect(lambda: self.all_selected())
      self.con_checkbox[k]=checkbox
      self.group_selected[k]=False
      grid_layout.addWidget(checkbox,0,0)
      cnt=0
      for product in v:
        cnt=cnt+1
        checkbox=QCheckBox(product['desc'])
        font = QFont('Arial', 6)
        checkbox.setFont(font)
        #checkbox.stateChanged.connect(lambda: print(self.get_selected()))
        checkboxes.append(checkbox)
        grid_layout.addWidget(checkbox,cnt//2,cnt%2)
      self.checkboxes[k]=checkboxes
      groupBox.setLayout(grid_layout)
      leftLayout.addWidget(groupBox)
    leftFrame = QFrame()
    leftFrame.setLayout(leftLayout)
    leftFrame.setFrameShape(QFrame.Shape.StyledPanel)
    leftFrame.setMaximumWidth(resolution.width()//5)
    self.leftFrame=leftFrame
    self.leftFrameHide=False

    button1 = QPushButton('绘图')
    button1.setFixedSize(80,25)
    button1.clicked.connect(self.plot)
    button2 = QPushButton('更新')
    button2.setFixedSize(80,25)
    button2.clicked.connect(self.run_command)
    button3 = QPushButton('隐藏边框')
    button3.setFixedSize(80,25)
    button3.clicked.connect(self.switch)
    self.switchButton=button3

    command_layout = QHBoxLayout()
    command_layout.addWidget(button1)
    command_layout.addWidget(button2)
    command_layout.addWidget(button3)
    groupBox = QGroupBox('')
    groupBox.setFlat(False)
    groupBox.setLayout(command_layout)
    rightUpperLayout = QVBoxLayout()
    rightUpperLayout.addWidget(groupBox)

    rightUpperFrame = QFrame()
    rightUpperFrame.setMaximumHeight(math.floor(resolution.height() * 0.08))
    rightUpperFrame.setLayout(rightUpperLayout)

    rightMiddleLayout=QVBoxLayout()
    rightLowerLayout=QVBoxLayout()
    rightMiddleFrame = QFrame()
    rightLowerFrame = QFrame()
    rightMiddleFrame.setLayout(rightMiddleLayout)
    rightMiddleFrame.setMaximumHeight(math.floor(resolution.height() * 0.45))
    rightLowerFrame.setLayout(rightLowerLayout)
    rightLowerFrame.setMaximumHeight(math.floor(resolution.height() * 0.45))
    right_splitter = QSplitter(Qt.Orientation.Vertical)
    right_splitter.addWidget(rightUpperFrame)
    right_splitter.addWidget(rightMiddleFrame)
    right_splitter.addWidget(rightLowerFrame)

    self.upperFig=plt.Figure()
    self.upperCanvas=FC(self.upperFig)
    self.lowerFig=plt.Figure()
    self.lowerCanvas=FC(self.lowerFig)
    rightMiddleLayout.addWidget(self.upperCanvas)
    rightLowerLayout.addWidget(self.lowerCanvas)
    rightLayout = QVBoxLayout()
    #rightLayout.addWidget(self.canvas)
    rightLayout.addWidget(right_splitter)

    rightFrame = QFrame()
    rightFrame.setLayout(rightLayout)
    rightFrame.setFrameShape(QFrame.Shape.StyledPanel)
    mainSplitter = QSplitter(Qt.Orientation.Horizontal)
    mainSplitter.addWidget(leftFrame)
    mainSplitter.addWidget(rightFrame)

    mainLayout = QHBoxLayout()
    mainLayout.addWidget(mainSplitter)

    #设置主界面布局
    self.setLayout(mainLayout)
    self.setGeometry(0, 0, resolution.width(), resolution.height())
    self.setWindowTitle("金融助手")
    self.products=products
    self.display_products=[]
    self.net_value_data = {}

  def __del__(self):
    if self.persistentStorage == 'db':
      del self.dbtool

  def all_selected(self):
    for k,con_checkbox in self.con_checkbox.items():
      if con_checkbox.isChecked()!=self.group_selected[k]:
        group=k
        self.group_selected[k]=con_checkbox.isChecked()
        break

    con_checkbox = self.con_checkbox[group]
    if con_checkbox.isChecked():
      for checkbox in self.checkboxes[group]:
        checkbox.setChecked(True)
    else:
      for checkbox in self.checkboxes[group]:
        checkbox.setChecked(False)

  def get_selected(self):
    checked=[]
    for key, checkboxes in self.checkboxes.items():
      for checkbox in checkboxes:
        if checkbox.isChecked():
          checked.append(checkbox.text())
    return checked

  def plot(self):
    self.display_products=[]
    select_products=self.get_selected()
    for k,products in self.products.items():
      for product in products:
        if product['desc'] in select_products:
          self.display_products.append(product)
    self.rewrite()
    self.draw()

  def run_command(self):
    result=subprocess.run(["python","wm_firefox.py"],capture_output=True)
    print(result.stdout,result.returncode)
    QMessageBox.information(self, '处理结果', '返回码:%d'%result.returncode, QMessageBox.Ok)

  def switch(self):
    if self.leftFrameHide:
      self.leftFrame.setMaximumWidth(self.resolution.width()//5)
      self.leftFrameHide = False
      self.switchButton.setText('隐藏边框')
    else:
      self.leftFrame.setMaximumWidth(0)
      self.leftFrameHide=True
      self.switchButton.setText('显示边框')

  def rewrite(self):
    for product in self.display_products:
      code = product['code']
      desc = product['desc']
      #print(code, desc)
      if self.persistentStorage == 'file':
        fname = './data/%s.csv' % code
        dt = [('date', 'U16'), ('netvalue', 'f4')]
        net_values = np.loadtxt(fname, dt, delimiter=',')
        xdata = [datetime.strptime(date, '%Y-%m-%d').date() for date in net_values['date']]
        ydata = net_values['netvalue']
      else:
        rows = self.dbtool.queryDB("select rpt_date,value from netvalue where code='%s' order by rpt_date asc" % code)
        xdata = [datetime.strptime(onerow[0], '%Y-%m-%d').date() for onerow in rows]
        ydata = [onerow[1] for onerow in rows]
      rewritten_xdata = []
      rewritten_ydata = []
      if len(xdata) == 0:
        return
      prev_date = xdata[0]
      prev_value = ydata[0]
      rewritten_xdata.append(xdata[0])
      rewritten_ydata.append(ydata[0])
      for i in range(1, len(xdata)):
        next_date = xdata[i]
        next_value = ydata[i]
        date_interval = int((next_date - prev_date) / timedelta(days=1))
        for cnt in range(1, date_interval):
          rewritten_xdata.append(prev_date + timedelta(days=cnt))
          rewritten_ydata.append(prev_value + (next_value - prev_value) / date_interval * cnt)
        rewritten_xdata.append(next_date)
        rewritten_ydata.append(next_value)
        prev_date = next_date
        prev_value = next_value

      self.net_value_data[code] = (np.array(rewritten_xdata), np.array(rewritten_ydata))

  def draw(self):
    self.upperFig.clear()
    ax1a = self.upperFig.add_subplot(121)
    self.draw_subplot(ax1a, (datetime.now() - timedelta(days=365 + 1)).date())
    ax1b = self.upperFig.add_subplot(122)
    self.draw_subplot(ax1b, (datetime.now() - timedelta(days=180 + 1)).date())
    self.upperCanvas.draw()

    self.lowerFig.clear()
    ax2a = self.lowerFig.add_subplot(121)
    self.draw_subplot(ax2a, (datetime.now() - timedelta(days=60 + 1)).date())
    ax2b = self.lowerFig.add_subplot(122)
    self.draw_subplot(ax2b, (datetime.now() - timedelta(days=30 + 1)).date())
    self.lowerCanvas.draw()

  def draw_subplot(self, ax, start_date):
    if (datetime.now() - timedelta(days=60)).date() <= start_date:
      ax.xaxis.set_major_locator(dates.DayLocator(interval=5))
      ax.xaxis.set_major_formatter(dates.DateFormatter('%m-%d'))
    else:
      ax.xaxis.set_major_locator(dates.MonthLocator())
      ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m'))
      ax.xaxis.set_minor_locator(dates.DayLocator(interval=1))
    font = {'family': 'SimHei', 'weight': 'normal', 'size': 8}
    ax.set_ylabel('净值', font)
    ax.set_xlabel('时间', font)
    ax.set_title('理财产品净值', font)
    for product in self.display_products:
      code = product['code']
      desc = product['desc']
      xdata = self.net_value_data[code][0]
      ydata = self.net_value_data[code][1]
      disp_xdata = xdata[xdata >= start_date]
      if len(disp_xdata)==0:
        continue
      disp_ydata = ydata[xdata >= start_date]
      disp_ydata = disp_ydata / disp_ydata[0]
      if desc.startswith('中银'):
        line, = ax.plot(disp_xdata, disp_ydata, lw=2, label=desc, linestyle='-')
      else:
        line, = ax.plot(disp_xdata, disp_ydata, lw=2, label=desc, linestyle='--')
      #for label in ax.get_xticklabels():
      #  label.set_rotation(10)
      plt.setp(ax.get_xticklabels(), fontsize=8)
      plt.setp(ax.get_yticklabels(), fontsize=8)
      plt.subplots_adjust(left=0.0,right=1.0)
      end_date = (datetime.now() - timedelta(days=1)).date()
      base_rate0 = 0
      base_rate1 = (end_date - start_date) / timedelta(days=360) * 0.01
      base_rate2 = (end_date - start_date) / timedelta(days=360) * 0.02
      base_rate3 = (end_date - start_date) / timedelta(days=360) * 0.03
      base_rate4 = (end_date - start_date) / timedelta(days=360) * 0.04
      base_rate5 = (end_date - start_date) / timedelta(days=360) * 0.05
      ax.plot([start_date, end_date], [1, 1 + base_rate0], lw=1, linestyle='dotted', color='grey')
      ax.plot([start_date, end_date], [1, 1 + base_rate1], lw=1, linestyle='dotted', color='grey')
      ax.plot([start_date, end_date], [1, 1 + base_rate2], lw=1, linestyle='dotted', color='grey')
      ax.plot([start_date, end_date], [1, 1 + base_rate3], lw=1, linestyle='dotted', color='grey')
      ax.plot([start_date, end_date], [1, 1 + base_rate4], lw=1, linestyle='dotted', color='grey')
      ax.plot([start_date, end_date], [1, 1 + base_rate5], lw=1, linestyle='dotted', color='grey')
    ax.legend(prop={'family': 'SimHei', 'size': 10})


if __name__ == '__main__':
  app = QApplication(sys.argv)
  with open('wm.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)
  products={}
  for key, _ in config.items():
    if key!='wm':
      catalog=config[key]['catalog']
      products[catalog]=[]
  for key, _ in config.items():
    if key != 'wm':
      catalog=config[key]['catalog']
      products[catalog].extend(config[key]['products'])
  demo = QtDemo(products)
  demo.show()
  del demo
  sys.exit(app.exec())