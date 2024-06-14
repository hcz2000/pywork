import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import yaml
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FC
import numpy as np
from datetime import datetime, timedelta

class CheckBoxDemo(QWidget):

  def __init__(self, products,parent=None):
    super(CheckBoxDemo, self).__init__(parent)
    #设置主界面布局垂直布局
    leftLayout = QVBoxLayout()
    self.checkboxes = {}
    self.con_checkbox= {}
    self.group_selected={}
    for k,v in products.items():
      groupBox = QGroupBox(k)
      groupBox.setFlat(False)
      layout = QGridLayout()
      checkboxes=[]
      checkbox = QCheckBox('全选')
      checkbox.stateChanged.connect(lambda: self.all_selected())
      self.con_checkbox[k]=checkbox
      self.group_selected[k]=False
      layout.addWidget(checkbox,0,0)
      cnt=0
      for product in v:
        cnt=cnt+1
        checkbox=QCheckBox(product['desc'])
        checkbox.stateChanged.connect(lambda: print(self.get_selected()))
        checkboxes.append(checkbox)
        layout.addWidget(checkbox,cnt//3,cnt%3)

      self.checkboxes[k]=checkboxes

      groupBox.setLayout(layout)
      leftLayout.addWidget(groupBox)

    button = QPushButton('确定')
    button.setFixedSize(100,25)
    button.clicked.connect(self.on_click)
    groupBox = QGroupBox('操作')
    groupBox.setFlat(False)
    layout = QHBoxLayout()
    layout.addWidget(button)
    groupBox.setLayout(layout)
    leftLayout.addWidget(groupBox)

    leftFrame = QFrame()
    leftFrame.setLayout(leftLayout)
    leftFrame.setFrameShape(QFrame.Shape.StyledPanel)

    self.fig=plt.Figure()
    self.canvas=FC(self.fig)
    rightLayout = QVBoxLayout()
    rightLayout.addWidget(self.canvas)

    rightFrame = QFrame()
    rightFrame.setLayout(rightLayout)
    rightFrame.setFrameShape(QFrame.Shape.StyledPanel)
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(leftFrame)
    splitter.addWidget(rightFrame)

    hbox = QHBoxLayout()
    hbox.addWidget(splitter)

    #设置主界面布局
    #self.setLayout(mainLayout)
    self.setLayout(hbox)
    self.setGeometry(0, 0, 2048, 1024)
    #设置主界面标题
    self.setWindowTitle("checkbox demo")

    #self.products=[]
    #for k,p in products.items():
    #  self.products.extend(p)
    self.products=products
    self.display_products=[]
    self.net_value_data = {}

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

  def on_click(self):
    self.display_products=[]
    select_products=self.get_selected()
    for k,products in self.products.items():
      for product in products:
        if product['desc'] in select_products:
          self.display_products.append(product)
    self.rewrite()
    self.draw()

  def rewrite(self):
    for product in self.display_products:
      code = product['code']
      desc = product['desc']
      print(code, desc)
      fname = './data/%s.csv' % code
      dt = [('date', 'U16'), ('netvalue', 'f4')]
      net_values = np.loadtxt(fname, dt, delimiter=',')
      xdata = [datetime.strptime(date, '%Y-%m-%d').date() for date in net_values['date']]
      ydata = net_values['netvalue']
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
    fig = self.fig
    fig.clear()
    ax1 = fig.add_subplot(211)
    self.draw_subplot(ax1, (datetime.now() - timedelta(days=365 + 1)).date())

    ax2 = fig.add_subplot(212)
    self.draw_subplot(ax2, (datetime.now() - timedelta(days=30 + 1)).date())

    #plt.show()
    self.canvas.draw()

  def draw_subplot(self, ax, start_date):
    if (datetime.now() - timedelta(days=60)).date() <= start_date:
      ax.xaxis.set_major_locator(dates.DayLocator(interval=1))
      ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m-%d'))
    else:
      ax.xaxis.set_major_locator(dates.MonthLocator())
      ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m'))
      ax.xaxis.set_minor_locator(dates.DayLocator(interval=1))
    font = {'family': 'SimHei', 'weight': 'normal', 'size': 16}
    ax.set_ylabel('净值', font)
    ax.set_xlabel('时间', font)
    ax.set_title('理财产品净值', font)
    for product in self.display_products:
      code = product['code']
      desc = product['desc']
      xdata = self.net_value_data[code][0]
      ydata = self.net_value_data[code][1]
      disp_xdata = xdata[xdata >= start_date]
      disp_ydata = ydata[xdata >= start_date]
      disp_ydata = disp_ydata / disp_ydata[0]
      if desc.startswith('中银'):
        line, = ax.plot(disp_xdata, disp_ydata, lw=3, label=desc, linestyle='-')
      else:
        line, = ax.plot(disp_xdata, disp_ydata, lw=3, label=desc, linestyle='--')
      for label in ax.get_xticklabels():
        label.set_rotation(30)
      end_date = (datetime.now() - timedelta(days=1)).date()
      base_rate0 = (end_date - start_date) / timedelta(days=360) * 0.02
      base_rate1 = (end_date - start_date) / timedelta(days=360) * 0.03
      base_rate2 = (end_date - start_date) / timedelta(days=360) * 0.04
      base_rate3 = (end_date - start_date) / timedelta(days=360) * 0.05
      ax.plot([start_date, end_date], [1, 1 + base_rate0], lw=1, linestyle='dotted', color='grey')
      ax.plot([start_date, end_date], [1, 1 + base_rate1], lw=1, linestyle='dotted', color='grey')
      ax.plot([start_date, end_date], [1, 1 + base_rate2], lw=1, linestyle='dotted', color='grey')
      ax.plot([start_date, end_date], [1, 1 + base_rate3], lw=1, linestyle='dotted', color='grey')
      # ax.plot([end_date, end_date], [0, 1 + base_rate3], lw=1, linestyle='-.', color='grey')
    plt.legend(prop={'family': 'SimHei', 'size': 14})



if __name__ == '__main__':
  app = QApplication(sys.argv)
  with open('wm.yaml', 'r') as file:
    config = yaml.safe_load(file)

  # 设置主界面布局垂直布局
  mainLayout = QVBoxLayout()
  products={}
  products['中银理财']=config['bocwm']['products']
  products['广银理财']=config['cgbwm']['products']
  products['招银理财']=config['cmbwm']['products']
  products['兴银理财']=config['cibwm']['products']
  checkboxDemo = CheckBoxDemo(products)
  checkboxDemo.show()


  sys.exit(app.exec())