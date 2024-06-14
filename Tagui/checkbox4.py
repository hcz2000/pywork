import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import yaml
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FC
import numpy as np

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
    try:
      ax = self.fig.add_subplot(111)
      x = np.linspace(0, 100, 100)
      y = np.random.random(100)
      ax.clear()
      ax.plot(x, y)
      self.canvas.draw()
    except Exception as e:
      print(e)



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