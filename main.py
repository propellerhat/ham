from PyQt6.QtWidgets import (
	QApplication,
	QWidget,
	QLabel,
	QVBoxLayout,
	QHBoxLayout,
	QGridLayout,
	QPushButton,
	QLineEdit,
	QTableWidget,
	QTableWidgetItem,
	QCheckBox
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QTimer, Qt
import sys
from pota_client import POTAClient
from dx_summit_client import DXSummitClient

class Window(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowTitle('Ham')

		main_layout = QVBoxLayout()

		pota_layout = QHBoxLayout()
		self.pota_user = QLineEdit()
		pota_layout.addWidget(QLabel('POTA Username'))
		pota_layout.addWidget(self.pota_user)

		self.pota_pw = QLineEdit()
		self.pota_pw.setEchoMode(QLineEdit.EchoMode.Password)
		pota_layout.addWidget(QLabel('POTA Password'))
		pota_layout.addWidget(self.pota_pw)

		login_btn = QPushButton('POTA Login')
		login_btn.clicked.connect(self.pota_login)
		pota_layout.addWidget(login_btn)

		self.pota_login_status = QLabel()
		pota_layout.addWidget(self.pota_login_status)

		main_layout.addLayout(pota_layout)

		self.filters = []
		self.filters_hbox = QHBoxLayout()
		self.show_all = QCheckBox('All')
		self.show_all.stateChanged.connect(self.toggle_all_filter)
		self.show_cw = QCheckBox('CW')
		self.show_cw.stateChanged.connect(self.toggle_cw_filter)
		self.show_dx = QCheckBox('DX')
		self.show_dx.stateChanged.connect(self.toggle_dx_filter)
		self.show_qrt = QCheckBox('QRT')
		self.show_qrt.stateChanged.connect(self.toggle_qrt_filter)
		self.filters_hbox.addWidget(QLabel('Show:'))
		self.filters_hbox.addWidget(self.show_all)
		self.filters_hbox.addWidget(self.show_cw)
		self.filters_hbox.addWidget(self.show_dx)
		self.filters_hbox.addWidget(self.show_qrt)
		main_layout.addLayout(self.filters_hbox)

		self.spots_view = QTableWidget()
		self.spots_view.setRowCount(0)
		self.spots_view.setColumnCount(6)

		self.spots_view.setHorizontalHeaderItem(0, QTableWidgetItem('State'))
		self.spots_view.setHorizontalHeaderItem(1, QTableWidgetItem('kHz'))
		self.spots_view.setHorizontalHeaderItem(2, QTableWidgetItem('Call'))
		self.spots_view.setHorizontalHeaderItem(3, QTableWidgetItem('Comment'))
		self.spots_view.setHorizontalHeaderItem(4, QTableWidgetItem('Park'))
		self.spots_view.setHorizontalHeaderItem(5, QTableWidgetItem('Time'))

		main_layout.addWidget(self.spots_view)

		self.setLayout(main_layout)

		self.pota = POTAClient()
		self.dxs = DXSummitClient()
		self.timer = QTimer()
		self.timer.timeout.connect(self.refresh_spots)
		self.timer.start(69000)
		self.counter = 0

		self.spots = []
		self.show_all.setCheckState(Qt.CheckState.Checked)
		self.refresh_spots()

	def pota_login(self):
		self.pota.login(self.pota_user.text(), self.pota_pw.text())
		self.pota_login_status.setText('Logged In')
		self.show_worked_states = QCheckBox('Worked States')
		self.show_worked_states.stateChanged.connect(self.toggle_worked_states_filter)
		self.show_worked_states.setCheckState(Qt.CheckState.Checked)
		self.filters_hbox.addWidget(self.show_worked_states)

	def toggle_cw_filter(self):
		if self.show_cw.isChecked():
			self.filters.append('CW')
		else:
			self.filters.remove('CW')
		self.update_spots_view()

	def toggle_qrt_filter(self):
		if self.show_qrt.isChecked():
			self.filters.append('QRT')
		else:
			self.filters.remove('QRT')
		self.update_spots_view()

	def toggle_dx_filter(self):
		if self.show_dx.isChecked():
			self.filters.append('DX')
		else:
			self.filters.remove('DX')
		self.update_spots_view()

	def toggle_worked_states_filter(self):
		if self.show_worked_states.isChecked():
			self.filters.append('Worked States')
		else:
			self.filters.remove('Worked States')
		self.update_spots_view()

	def toggle_all_filter(self):
		if self.show_all.isChecked():
			self.filters.append('All')
		else:
			self.filters.remove('All')
		self.update_spots_view()

	def filtered_spots(self):
		results = self.spots

		if 'All' in self.filters:
			return results
		
		if 'CW' in self.filters:
			results = list(filter(lambda x: (x['mode'] == 'CW'), results))
		if 'DX' not in self.filters:
			results = list(filter(lambda x: (x['locationDesc'].startswith('US')), results))
		if 'Worked States' not in self.filters:
			results = list(filter(lambda x: (x['locationDesc'] not in self.pota.hunted_states), results))
		if 'QRT' not in self.filters:
			results = list(filter(lambda x: (x['comments'].upper().find('QRT') == -1), results))

		return results

	def needed_state(self):
		pass

	def update_spots_view(self):
		self.spots_view.setRowCount(0)
		for spot in self.filtered_spots():
			row_cursor = self.spots_view.rowCount()
			self.spots_view.insertRow(row_cursor)
			self.spots_view.setItem(row_cursor, 0, QTableWidgetItem(spot['locationDesc']))
			self.spots_view.setItem(row_cursor, 1, QTableWidgetItem(spot['frequency']))
			self.spots_view.setItem(row_cursor, 2, QTableWidgetItem(spot['activator']))
			self.spots_view.setItem(row_cursor, 3, QTableWidgetItem(spot['comments']))
			self.spots_view.setItem(row_cursor, 4, QTableWidgetItem(spot['reference']))
			self.spots_view.setItem(row_cursor, 5, QTableWidgetItem(spot['spotTime'].split('T')[1]))

	def refresh_spots(self):
		self.spots = self.pota.fetch_spots()
		self.update_spots_view()
		

app = QApplication([])
window = Window()
window.show()
sys.exit(app.exec())