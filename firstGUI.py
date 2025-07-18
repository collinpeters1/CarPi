import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton

class MyApp():

	def __init__(self):
	
		app = QApplication(sys.argv)
		win = QMainWindow()
		win.setFixedSize(100,300)
		win.setWindowTitle("Da First window")
		
		button = QPushButton("click me hard",win)
		button.resize(50,50)
		button.move(50,150)
		button.setStyleSheet("background-color:blue;")
		
		win.show()
		sys.exit(app.exec())
		
MyApp()