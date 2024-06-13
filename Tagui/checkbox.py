import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import yaml


class CheckBoxDemo(QWidget):

  def __init__(self, parent=None):
    super(CheckBoxDemo, self).__init__(parent)

    with open('wm.yaml', 'r') as file:
      config = yaml.safe_load(file)
    self.products = []
    for product in config['cgbwm']['products']:
      self.products.append(product)

    #创建一个GroupBox组
    groupBox = QGroupBox("Checkboxes")
    groupBox.setFlat(False)

    self.checkboxes=[]

    #水平布局
    layout = QHBoxLayout()

    checkbox = QCheckBox('全选')
    checkbox.stateChanged.connect(lambda: self.all_selected())
    self.con_checkbox=checkbox
    layout.addWidget(checkbox)
    for product in self.products:
      checkbox=QCheckBox(product['desc'])
      checkbox.stateChanged.connect(lambda: print(self.get_selected()))
      self.checkboxes.append(checkbox)
      layout.addWidget(checkbox)

    #设置QGroupBox组的布局方式
    groupBox.setLayout(layout)

    #设置主界面布局垂直布局
    mainLayout = QVBoxLayout()
    #QgroupBox的控件添加到主界面布局中
    mainLayout.addWidget(groupBox)

    #设置主界面布局
    self.setLayout(mainLayout)
    #设置主界面标题
    self.setWindowTitle("checkbox demo")

  def all_selected(self):
    print('全选:',checkbox.isChecked())
    if self.con_checkbox.isChecked():
      for checkbox in self.checkboxes:
        checkbox.setChecked(True)
    else:
      for checkbox in self.checkboxes:
        checkbox.setChecked(False)

  def get_selected(self):
    checked=[]
    for checkbox in self.checkboxes:
      if checkbox.isChecked():
        checked.append(checkbox.text())
    return checked



if __name__ == '__main__':
  app = QApplication(sys.argv)
  checkboxDemo = CheckBoxDemo()
  checkboxDemo.show()
  sys.exit(app.exec())