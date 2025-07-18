# simple_buttons.py
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Print numbers straight to terminal")
        self.setFixedSize(500,500)

        layout = QVBoxLayout()

        # testing the use of the .connect(lambda:) stuff. it seems very powerful and will let us link any python function to a 
        # button click 


        # prints 1 straight to console
        btn_one = QPushButton("Print 1")
        btn_one.clicked.connect(lambda: print(1))

        # prints 0 straight to console 
        btn_zero = QPushButton("Print 0")
        btn_zero.clicked.connect(lambda: print(0))
        
        btn_ten = QPushButton("Print 10")
        btn_ten.clicked.connect(lambda: print(10))
        btn_ten.setStyleSheet("background-color:blue;")
        
        layout.addWidget(btn_one)
        layout.addWidget(btn_zero)
        layout.addWidget(btn_ten)

        # https://doc.qt.io/qt-6/layout.html
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)   # Every Qt app needs exactly one QApplication
    window = MainWindow()          # Create our window
    window.show()                  # Make it visible
    sys.exit(app.exec())           # Start the Qt event loop
