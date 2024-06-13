import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import yaml


class CheckBoxDemo(QWidget):

  def __init__(self, products,parent=None):
    super(CheckBoxDemo, self).__init__(parent)
    #设置主界面布局垂直布局
    mainLayout = QVBoxLayout()
    self.checkboxes = {}
    self.con_checkbox= {}
    for k,v in products.items():
      #创建一个GroupBox组
      groupBox = QGroupBox(k)
      groupBox.setFlat(False)
      #水平布局
      layout = QHBoxLayout()
      checkboxes=[]
      checkbox = QCheckBox('全选')
      checkbox.stateChanged.connect(lambda: self.all_selected())
      self.con_checkbox[k]=checkbox
      layout.addWidget(checkbox)
      for product in v:
        checkbox=QCheckBox(product['desc'])
        checkbox.stateChanged.connect(lambda: print(self.get_selected()))
        checkboxes.append(checkbox)
        layout.addWidget(checkbox)

      self.checkboxes[k]=checkboxes

      #设置QGroupBox组的布局方式
      groupBox.setLayout(layout)
      #QgroupBox的控件添加到主界面布局中
      mainLayout.addWidget(groupBox)

    #设置主界面布局
    self.setLayout(mainLayout)
    #设置主界面标题
    self.setWindowTitle("checkbox demo")

  def all_selected(self):
    for key,con_checkbox in self.con_checkbox.items():
      if con_checkbox.isChecked():
        for checkbox in self.checkboxes[key]:
          checkbox.setChecked(True)
      #else:
      #  for checkbox in self.checkboxes[key]:
      #    checkbox.setChecked(False)

  def get_selected(self):
    checked=[]
    for key, checkboxes in self.checkboxes.items():
      for checkbox in checkboxes:
        if checkbox.isChecked():
          checked.append(checkbox.text())
    return checked



if __name__ == '__main__':
  app = QApplication(sys.argv)
  with open('wm.yaml', 'r') as file:
    config = yaml.safe_load(file)

  # 设置主界面布局垂直布局
  mainLayout = QVBoxLayout()
  products={}
  products['中银']=config['bocwm']['products']
  products['广银']=config['cgbwm']['products']
  checkboxDemo = CheckBoxDemo(products)
  checkboxDemo.show()


  sys.exit(app.exec())