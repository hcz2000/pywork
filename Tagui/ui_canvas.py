import sys
from PyQt6.QtWidgets import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FC
import numpy as np
import yaml


class QtDraw(QMainWindow):

  def __init__(self):
    super(QtDraw, self).__init__()
    self.resize(2048,1536)
    self.setWindowTitle('PyQt Draw')
    self.fig=plt.Figure()
    self.canvas=FC(self.fig)
    button=QPushButton(self)
    button.setFixedSize(100, 25)
    button.setText('draw')
    button.clicked.connect(self.on_click)
    central_widget=QWidget()
    layout=QVBoxLayout()
    layout.addWidget(self.canvas)
    layout.addWidget(button)
    central_widget.setLayout(layout)
    self.setCentralWidget(central_widget)


  def on_click(self):
    try:
      ax=self.fig.add_subplot(111)
      x=np.linspace(0,100,100)
      y=np.random.random(100)
      ax.clear()
      ax.plot(x,y)
      self.canvas.draw()
    except Exception as e:
      print(e)



if __name__ == '__main__':
  app = QApplication(sys.argv)
  w=QtDraw()
  w.show()
  sys.exit(app.exec())