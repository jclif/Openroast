import datetime
import matplotlib
import threading
import time
matplotlib.use('Qt5Agg')
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.dates import MinuteLocator, DateFormatter
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from ..roaster_libraries.FreshRoastSR700 import FreshRoastSR700

class RoastTab(QWidget):
    def __init__(self):
        super(RoastTab, self).__init__()

        # Class variables.
        self.graphXValueList = []
        self.graphYValueList = []
        self.counter = 0
        self.roaster = FreshRoastSR700()
        self.timeSliderPressed = False
        self.tempSliderPressed = False

        # Create the tab ui.
        self.create_ui()

        # Create thread to update gui data.
        self.dataThread = threading.Thread(target=self.update_data, args=(4,))
        self.dataThread.daemon = True
        self.dataThread.start()

    def create_ui(self):
        # Create the main layout for the roast tab.
        self.layout = QGridLayout()

        # Create graph widget.
        self.create_graph()
        self.layout.addWidget(self.graphWidget, 0, 0)
        self.layout.setColumnStretch(0, 1)

        # Create right pane.
        self.rightPane = self.create_right_pane()
        self.layout.addLayout(self.rightPane, 0, 1)

        # Create not connected label.
        self.connectionStatusLabel = QLabel("Please connect your roaster.")
        self.connectionStatusLabel.setObjectName("connectionStatus")
        self.connectionStatusLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.connectionStatusLabel, 0, 0)

        # Set main layout for widget.
        self.setLayout(self.layout)

    def create_graph(self):
        # Create the graph widget.
        self.graphWidget = QWidget(self)
        self.graphWidget.setObjectName("graph")

        # Style attributes of matplotlib.
        plt.rcParams['lines.linewidth'] = 3
        plt.rcParams['lines.color'] = '#2a2a2a'
        plt.rcParams['font.size'] = 10.

        self.graphFigure = plt.figure(facecolor='#444952')
        self.graphCanvas = FigureCanvas(self.graphFigure)

        # Add graph widgets to layout for graph.
        graphVerticalBox = QVBoxLayout()
        graphVerticalBox.addWidget(self.graphCanvas)
        self.graphWidget.setLayout(graphVerticalBox)

        # Animate the the graph with new data
        animateGraph = animation.FuncAnimation(self.graphFigure, self.graph_draw, interval=1000)

    def graph_draw(self, *args, **kwargs):
        # Start graphing the roast if the roast has started.
        if (self.roaster.get_current_status() == 1 or self.roaster.get_current_status() == 2):
            self.graph_get_data()

        self.graphAxes = self.graphFigure.add_subplot(111)
        self.graphAxes.plot_date(self.graphXValueList, self.graphYValueList, '#85b63f')

        # Add formatting to the graphs.
        self.graphAxes.set_ylabel('TEMPERATURE (°F)')
        self.graphAxes.set_xlabel('TIME')
        self.graphFigure.subplots_adjust(bottom=0.2)

        ax = self.graphAxes.get_axes()
        ax.xaxis.set_major_formatter(DateFormatter('%M:%S'))
        ax.set_axis_bgcolor('#23252a')

        self.graphCanvas.draw()

    def graph_get_data(self):
        self.counter += 1
        currentTime = datetime.datetime.fromtimestamp(self.counter)
        self.graphXValueList.append(matplotlib.dates.date2num(currentTime))
        self.graphYValueList.append(self.roaster.get_current_temp())

    def update_data(self, threadNum):
        # Update the gui data on thread start.
        self.update_section_time()
        self.update_total_time()

        while(True):
            time.sleep(1)
            self.currentTempLabel.setText(str(self.roaster.get_current_temp()))
            if (self.roaster.get_current_status() == 1 or self.roaster.get_current_status() == 2):
                self.update_section_time()
                self.update_total_time()

            # Check connection status of the roaster.
            if (self.roaster.get_connection_status()):
                self.connectionStatusLabel.setHidden(True)
                self.setEnabled(True)
            else:
                self.connectionStatusLabel.setHidden(False)
                self.setEnabled(False)

    def create_right_pane(self):
        rightPane = QVBoxLayout()

        # Create guage window.
        guageWindow = self.create_gauge_window()
        rightPane.addLayout(guageWindow)

        # Create button panel.
        buttonPanel = self.create_button_panel()
        rightPane.addLayout(buttonPanel)

        # Create sliders.
        sliderPanel = self.create_slider_panel()
        rightPane.addLayout(sliderPanel)

        # Add a bottom spacer to keep sizing.
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        rightPane.addWidget(spacer)

        return rightPane

    def create_gauge_window(self):
        guageWindow = QGridLayout()

        # Create current temp gauge.
        self.currentTempLabel = QLabel()
        currentTemp = self.create_info_box("CURRENT TEMP", "tempGuage", self.currentTempLabel)
        guageWindow.addLayout(currentTemp, 0, 0)

        # Create target temp gauge.
        self.targetTempLabel = QLabel()
        targetTemp = self.create_info_box("TARGET TEMP", "tempGuage", self.targetTempLabel)
        guageWindow.addLayout(targetTemp, 0, 1)

        # Create current time.
        self.sectionTimeLabel = QLabel()
        currentTime = self.create_info_box("CURRENT SECTION TIME", "timeWindow", self.sectionTimeLabel)
        guageWindow.addLayout(currentTime, 1, 0)

        # Create totalTime.
        self.totalTimeLabel = QLabel()
        totalTime = self.create_info_box("TOTAL TIME", "timeWindow", self.totalTimeLabel)
        guageWindow.addLayout(totalTime, 1, 1)

        return guageWindow

    def create_button_panel(self):
        buttonPanel = QGridLayout()

        # Create start roast button.
        self.startButton = QPushButton("START")
        self.startButton.setObjectName("mainButton")
        self.startButton.clicked.connect(self.roaster.roast)
        buttonPanel.addWidget(self.startButton, 0, 0)

        # Create stop roast button.
        self.stopButton = QPushButton("STOP")
        self.stopButton.setObjectName("mainButton")
        self.stopButton.clicked.connect(self.roaster.idle)
        buttonPanel.addWidget(self.stopButton, 0, 1)

        # Create fan label.
        fanLabel = QLabel("FAN SPEED")
        fanLabel.setAlignment(Qt.AlignCenter)
        buttonPanel.addWidget(fanLabel, 0, 2)

        # Create cool button.
        self.coolButton = QPushButton("COOL")
        self.coolButton.setObjectName("mainButton")
        self.coolButton.clicked.connect(self.cooling_phase)
        buttonPanel.addWidget(self.coolButton, 1, 0)

        # Create next button.
        self.nextButton = QPushButton("NEXT")
        self.nextButton.setObjectName("mainButton")
        buttonPanel.addWidget(self.nextButton, 1, 1)

        # Create fan speed spin box.
        self.fanSpeedSpinBox = QSpinBox()
        self.fanSpeedSpinBox.setRange(1, 9)
        self.fanSpeedSpinBox.setFocusPolicy(Qt.NoFocus)
        self.fanSpeedSpinBox.setAlignment(Qt.AlignCenter)
        self.fanSpeedSpinBox.lineEdit().setReadOnly(True)
        self.fanSpeedSpinBox.lineEdit().deselect()
        self.fanSpeedSpinBox.valueChanged.connect(self.change_fan_speed)
        buttonPanel.addWidget(self.fanSpeedSpinBox, 1, 2)

        return buttonPanel

    def create_slider_panel(self):
        sliderPanel = QGridLayout()

        # Create temperature slider label.
        tempSliderLabel = QLabel("ADJUST TARGET TEMP")
        sliderPanel.addWidget(tempSliderLabel, 0, 0)

        # Create temperature slider.
        self.tempSlider = QSlider(Qt.Horizontal)
        self.tempSlider.setRange(150, 600)
        self.tempSlider.sliderMoved.connect(self.change_target_temp)
        self.tempSlider.sliderPressed.connect(self.toggle_temp_slider_status)
        self.tempSlider.sliderReleased.connect(self.toggle_temp_slider_status)
        self.change_target_temp()
        sliderPanel.addWidget(self.tempSlider, 1, 0)

        # Create timer slider.
        timeSliderLabel = QLabel("ADJUST SECTION TIME")
        sliderPanel.addWidget(timeSliderLabel, 2, 0)

        # Create timer slider.
        self.timeSlider = QSlider(Qt.Horizontal)
        self.timeSlider.setObjectName("inverted")
        self.timeSlider.setInvertedAppearance(True)
        self.timeSlider.setInvertedControls(True)
        self.timeSlider.setRange(0, 720)
        self.timeSlider.sliderMoved.connect(self.set_section_time)
        self.timeSlider.sliderPressed.connect(self.toggle_time_slider_status)
        self.timeSlider.sliderReleased.connect(self.toggle_time_slider_status)
        sliderPanel.addWidget(self.timeSlider, 3, 0)

        return sliderPanel

    def create_info_box(self, labelText, objectName, valueLabel):
        # Create temp/time info boxes.
        infoBox = QVBoxLayout()
        infoBox.setSpacing(0)
        label = QLabel(labelText)
        label.setObjectName("label")
        valueLabel.setAlignment(Qt.AlignCenter)
        valueLabel.setObjectName(objectName)
        infoBox.addWidget(label)
        infoBox.addWidget(valueLabel)
        return infoBox

    def change_target_temp(self):
        self.targetTempLabel.setText(str(self.tempSlider.value()))
        self.roaster.set_target_temp(self.tempSlider.value())

    def change_target_temp_slider(self, temp):
        self.tempSlider.setValue(temp)

    def change_fan_speed(self):
        self.roaster.set_fan_speed(self.fanSpeedSpinBox.value())

    def set_section_time(self):
        self.sectionTimeLabel.setText(time.strftime("%M:%S", time.gmtime(self.timeSlider.value())))
        self.roaster.set_section_time(self.timeSlider.value())

    def update_section_time(self):
        self.timeSlider.setValue(self.roaster.get_section_time())
        self.sectionTimeLabel.setText(str(time.strftime("%M:%S", time.gmtime(self.roaster.get_section_time()))))

    def update_total_time(self):
        self.totalTimeLabel.setText(str(time.strftime("%M:%S", time.gmtime(self.roaster.get_total_time()))))

    def cooling_phase(self):
        self.roaster.cooling_phase()

    def toggle_temp_slider_status(self):
        self.tempSliderPressed = not self.tempSliderPressed

    def toggle_time_slider_status(self):
        self.timeSliderPressed = not self.timeSliderPressed

    def connect_roaster(self):
        self.roaster.run()
