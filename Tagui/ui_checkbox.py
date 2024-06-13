from PyQt6.QtWidgets import QComboBox,QLineEdit,QListWidgetItem,QListWidget,QCheckBox
from PyQt6.QtWidgets import QApplication,QVBoxLayout,QWidget
import sys

class ComboCheckBox(QComboBox):
    def  __init__(self,items:list):
        super(ComboCheckBox,self).__init__()
        self.items= ["全选"]+items
        self.box_list=[]
        self.text=QLineEdit()
        self.state=0
        q = QListWidget()

        for i in range(len(self.items)):
            self.box_list.append(QCheckBox())
            self.box_list[i].setText(self.items[i])
            item = QListWidgetItem(q)
            q.setItemWidget(item, self.box_list[i])
            if i == 0:
                self.box_list[i].stateChanged.connect(self.all_selected)
            else:
                self.box_list[i].stateChanged.connect(self.show_selected)
        q.setStyleSheet("font-size: 20px; font-weight: bold; height: 40px; margin-left: 5px")
        self.setStyleSheet("width: 300px; height: 50px; font-size: 21px; font-weight: bold")
        self.text.setReadOnly(True)
        self.setLineEdit(self.text)
        self.setModel(q.model())
        self.setView(q)

    def all_selected(self):
        if self.state == 0:
            self.state = 1
            for i in range(1, len(self.items)):
                self.box_list[i].setChecked(True)
        else:
            self.state = 0
            for i in range(1, len(self.items)):
                self.box_list[i].setChecked(False)

        self.show_selected()


    def get_selected(self) -> list:
        ret = []
        for i in range(1, len(self.items)):
            if self.box_list[i].isChecked():
                ret.append(self.box_list[i].text())
        return ret

    def show_selected(self):
        self.text.clear()
        ret = '; '.join(self.get_selected())
        self.text.setText(ret)


class UiMainWindow(QWidget):
    def __init__(self):
        super(UiMainWindow, self).__init__()
        self.setWindowTitle('Test')
        self.resize(600, 400)
        combo = ComboCheckBox(["Python", "Java", "Go", "C++", "JavaScript", "PHP"])
        layout = QVBoxLayout()
        layout.addWidget(combo)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = UiMainWindow()
    ui.show()
    sys.exit(app.exec())