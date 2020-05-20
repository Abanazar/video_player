import sys

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QStyle, QSizePolicy, QFileDialog
from PyQt5 import QtCore
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QPoint


class Example(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(400, 100, 700, 450)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.press = False
        self.last_pos = QPoint(0, 0)
        #объект QMediaPLayer
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        #и тута объект виджета видоса
        videowidget = QVideoWidget()
     
        openBtn = QPushButton('Browse')
        openBtn.setStyleSheet("background-color: #2a091b;"
        "color: #ffffff")
        openBtn.clicked.connect(self.open_file)
     
        self.playBtn = QPushButton()
        self.playBtn.setStyleSheet("background-color: #2a091b;"
        "color: #ffffff")
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)
     
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0,0)
        self.slider.sliderMoved.connect(self.set_position)
     
        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
     
        hboxLayout = QHBoxLayout()
        hboxLayout.setContentsMargins(0,0,0,0)
        hboxLayout.addWidget(openBtn)
        hboxLayout.addWidget(self.playBtn)
        hboxLayout.addWidget(self.slider)
     
        vboxLayout = QVBoxLayout()
        vboxLayout.addWidget(videowidget)
        vboxLayout.addLayout(hboxLayout)
        vboxLayout.addWidget(self.label)
    
        self.setLayout(vboxLayout)
        self.mediaPlayer.setVideoOutput(videowidget)
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)
     
    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Choice video file:")
        if filename != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.playBtn.setEnabled(True)
     
    def play_video(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()
     
    def mediastate_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
     
    def position_changed(self, position):
        self.slider.setValue(position)
     
    def duration_changed(self, duration):
        self.slider.setRange(0, duration)
     
    def set_position(self, position):
        self.mediaPlayer.setPosition(position)
     
    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

    def mouseMoveEvent(self, event):
        if self.press:
            self.move(event.globalPos() - self.last_pos)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press = True
            self.last_pos = event.pos()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press = False
    
    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(Qt.white, 5))
        painter.drawRect(self.rect())

    def keyReleaseEvent(self, event):
        #закрываю на кнопку ESC
        if event.key() == Qt.Key_Escape:
            self.close()
    
     

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Example()
    w.show()
    sys.exit(app.exec_())