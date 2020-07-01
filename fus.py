#!/usr/bin/python3

import sys

from PyQt5 import QtCore
from PyQt5 import QtGui

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, Q_ARG, QAbstractItemModel,
        QFileInfo, qFuzzyCompare, QMetaObject, QModelIndex, QObject, Qt,
        QThread, QTime, QUrl, QPoint)

from PyQt5.QtGui import QColor, qGray, QImage, QPainter, QPalette, QIcon
from PyQt5.QtMultimedia import (QAbstractVideoBuffer, QMediaContent,
        QMediaMetaData, QMediaPlayer, QMediaPlaylist, QVideoFrame, QVideoProbe)

from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QFileDialog,
        QFormLayout, QHBoxLayout, QLabel, QListView, QMessageBox, QPushButton,
        QSizePolicy, QSlider, QStyle, QToolButton, QVBoxLayout, QWidget)


class VideoWidget(QVideoWidget):

    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        p = self.palette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)

        self.setAttribute(Qt.WA_OpaquePaintEvent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.setFullScreen(False)
            event.accept()
        elif event.key() == Qt.Key_Enter and event.modifiers() & Qt.Key_Alt:
            self.setFullScreen(not self.isFullScreen())
            event.accept()
        else:
            super(VideoWidget, self).keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.setFullScreen(not self.isFullScreen())
        event.accept()


class PlaylistModel(QAbstractItemModel):

    Title, ColumnCount = range(2)

    def __init__(self, parent=None):
        super(PlaylistModel, self).__init__(parent)

        self.m_playlist = None

    def rowCount(self, parent=QModelIndex()):
        return self.m_playlist.mediaCount() if self.m_playlist is not None and not parent.isValid() else 0

    def columnCount(self, parent=QModelIndex()):
        return self.ColumnCount if not parent.isValid() else 0

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column) if self.m_playlist is not None and not parent.isValid() and row >= 0 and row < self.m_playlist.mediaCount() and column >= 0 and column < self.ColumnCount else QModelIndex()

    def parent(self, child):
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            if index.column() == self.Title:
                location = self.m_playlist.media(index.row()).canonicalUrl()
                return QFileInfo(location.path()).fileName()

            return self.m_data[index]

        return None

    def playlist(self):
        return self.m_playlist

    def setPlaylist(self, playlist):
        if self.m_playlist is not None:
            self.m_playlist.mediaAboutToBeInserted.disconnect(
                    self.beginInsertItems)
            self.m_playlist.mediaInserted.disconnect(self.endInsertItems)
            self.m_playlist.mediaAboutToBeRemoved.disconnect(
                    self.beginRemoveItems)
            self.m_playlist.mediaRemoved.disconnect(self.endRemoveItems)
            self.m_playlist.mediaChanged.disconnect(self.changeItems)

        self.beginResetModel()
        self.m_playlist = playlist

        if self.m_playlist is not None:
            self.m_playlist.mediaAboutToBeInserted.connect(
                    self.beginInsertItems)
            self.m_playlist.mediaInserted.connect(self.endInsertItems)
            self.m_playlist.mediaAboutToBeRemoved.connect(
                    self.beginRemoveItems)
            self.m_playlist.mediaRemoved.connect(self.endRemoveItems)
            self.m_playlist.mediaChanged.connect(self.changeItems)

        self.endResetModel()

    def beginInsertItems(self, start, end):
        self.beginInsertRows(QModelIndex(), start, end)

    def endInsertItems(self):
        self.endInsertRows()

    def beginRemoveItems(self, start, end):
        self.beginRemoveRows(QModelIndex(), start, end)

    def endRemoveItems(self):
        self.endRemoveRows()

    def changeItems(self, start, end):
        self.dataChanged.emit(self.index(start, 0),
                self.index(end, self.ColumnCount))


class PlayerControls(QWidget):

    play = pyqtSignal()
    pause = pyqtSignal()
    stop = pyqtSignal()
    next = pyqtSignal()
    previous = pyqtSignal()
    changeVolume = pyqtSignal(int)
    changeMuting = pyqtSignal(bool)
    changeRate = pyqtSignal(float)

    def __init__(self, parent=None):
        super(PlayerControls, self).__init__(parent)

        self.playerState = QMediaPlayer.StoppedState
        self.playerMuted = False

        self.playButton = QToolButton(clicked=self.playClicked)
        self.playButton.setStyleSheet("QToolButton{\n"
                            "color: #00ff00;\n"
                            "background-color: #id004c;\n"
                        	"color: #00ff00;\n"
                        	"border: 3px outset #270066;\n"
                        	"border-radius: 10px;"
                        	"width: 20px;"
                            "}\n"
                            "QToolButton:pressed{\n"
                            "border: 3px inset #270066;\n"
                            "}")
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.stopButton = QToolButton(clicked=self.stop)
        self.stopButton.setStyleSheet("QToolButton{\n"
                                	"background-color: #id004c;\n"
                                	"color: #00ff00;\n"
                                    "border: 3px outset #270066;\n"
                                	"border-radius: 10px;"
                                	"width: 20px;"
                                    "}\n"
                                    "QToolButton:pressed{\n"
                                	"border: 3px inset #270066;\n"
                                    "}")
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopButton.setEnabled(False)
        
        self.nextButton = QToolButton(clicked=self.next)
        self.nextButton.setStyleSheet("QToolButton{\n"
                                	"background-color: #id004c;\n"
                                	"color: #00ff00;\n"
                                	"border: 3px outset #270066;\n"
                                	"border-radius: 10px;"
                                	"width: 20px;"
                                    "}\n"
                                    "QToolButton:pressed{\n"
                                	"border: 3px inset #270066;\n"
                                    "}")
        self.nextButton.setIcon(
        self.style().standardIcon(QStyle.SP_MediaSkipForward))

        self.previousButton = QToolButton(clicked=self.previous)
        self.previousButton.setStyleSheet("QToolButton{\n"
                        	"background-color: #id004c;\n"
                        	"color: #00ff00;\n"
                        	"border: 3px outset #270066;\n"
                        	"border-radius: 10px;"
                        	"width: 20px;"
                            "}\n"
                            "QToolButton:pressed{\n"
                        	"border: 3px inset #270066;\n"
                            "}")
        self.previousButton.setIcon(
        self.style().standardIcon(QStyle.SP_MediaSkipBackward))

        self.muteButton = QToolButton(clicked=self.muteClicked)
        self.muteButton.setStyleSheet("QToolButton{\n"
                                	"background-color: #id004c;\n"
                                	"color: #00ff00;\n"
                                    "border: 3px outset #270066;\n"
                                	"border-radius: 10px;"
                                	"width: 20px;"
                                    "}\n"
                                    "QToolButton:pressed{\n"
                                	"border: 3px inset #270066;\n"
                                    "}")
        self.muteButton.setIcon(
        self.style().standardIcon(QStyle.SP_MediaVolume))

        self.volumeSlider = QSlider(Qt.Horizontal,
        sliderMoved=self.changeVolume)
        self.volumeSlider.setRange(0, 100)


        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stopButton)
        layout.addWidget(self.previousButton)
        layout.addWidget(self.playButton)
        layout.addWidget(self.nextButton)
        layout.addWidget(self.muteButton)
        layout.addWidget(self.volumeSlider)
        self.setLayout(layout)


    def state(self):
        return self.playerState

    def setState(self,state):
        if state != self.playerState:
            self.playerState = state

            if state == QMediaPlayer.StoppedState:
                self.stopButton.setEnabled(False)
                self.playButton.setIcon(
                        self.style().standardIcon(QStyle.SP_MediaPlay))
            elif state == QMediaPlayer.PlayingState:
                self.stopButton.setEnabled(True)
                self.playButton.setIcon(
                        self.style().standardIcon(QStyle.SP_MediaPause))
            elif state == QMediaPlayer.PausedState:
                self.stopButton.setEnabled(True)
                self.playButton.setIcon(
                        self.style().standardIcon(QStyle.SP_MediaPlay))

    def volume(self):
        return self.volumeSlider.value()

    def setVolume(self, volume):
        self.volumeSlider.setValue(volume)

    def isMuted(self):
        return self.playerMuted

    def setMuted(self, muted):
        if muted != self.playerMuted:
            self.playerMuted = muted

            self.muteButton.setIcon(
                    self.style().standardIcon(
                            QStyle.SP_MediaVolumeMuted if muted else QStyle.SP_MediaVolume))

    def playClicked(self):
        if self.playerState in (QMediaPlayer.StoppedState, QMediaPlayer.PausedState):
            self.play.emit()
        elif self.playerState == QMediaPlayer.PlayingState:
            self.pause.emit()

    def muteClicked(self):
        self.changeMuting.emit(not self.playerMuted)

    def playbackRate(self):
        return self.rateBox.itemData(self.rateBox.currentIndex())

    def setPlaybackRate(self, rate):
        for i in range(self.rateBox.count()):
            if qFuzzyCompare(rate, self.rateBox.itemData(i)):
                self.rateBox.setCurrentIndex(i)
                return

        self.rateBox.addItem("%dx" % rate, rate)
        self.rateBox.setCurrentIndex(self.rateBox.count() - 1)



class Player(QWidget):

    fullScreenChanged = pyqtSignal(bool)

    def __init__(self, playlist, parent=None):
        super(Player, self).__init__(parent)
        self.setGeometry(400, 100, 700, 450)
        self.setStyleSheet("background-color: #090019;"
        "color: #ffffff")

        self.colorDialog = None
        self.trackInfo = ""
        self.statusInfo = ""
        self.duration = 0

        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)

        self.player.durationChanged.connect(self.durationChanged)
        self.player.positionChanged.connect(self.positionChanged)
        self.player.metaDataChanged.connect(self.metaDataChanged)
        self.playlist.currentIndexChanged.connect(self.playlistPositionChanged)
        self.player.mediaStatusChanged.connect(self.statusChanged)
        self.player.bufferStatusChanged.connect(self.bufferingProgress)
        self.player.videoAvailableChanged.connect(self.videoAvailableChanged)
        self.player.error.connect(self.displayErrorMessage)

        self.videoWidget = VideoWidget()
        self.player.setVideoOutput(self.videoWidget)

        self.playlistModel = PlaylistModel()
        self.playlistModel.setPlaylist(self.playlist)

        self.playlistView = QListView()
        self.playlistView.setStyleSheet("background-color: #090019;\n"
        "color: #e300ff;\n"
        "font-size: 14px;")
        self.playlistView.setModel(self.playlistModel)
        self.playlistView.setCurrentIndex(
                self.playlistModel.index(self.playlist.currentIndex(), 0))

        self.playlistView.activated.connect(self.jump)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, self.player.duration() / 1000)

        self.labelDuration = QLabel()
        self.labelDuration.setStyleSheet("color: #ffffff")
        self.slider.sliderMoved.connect(self.seek)


        openButton = QPushButton("Open", clicked=self.open)
        openButton.setStyleSheet("QPushButton{\n"
                	"background-color: #id004c;\n"
                	"color: #e300ff;\n"
                	"border: 3px outset #270066;\n"
                	"font-size: 14px;"
                	"width: 100px;"
                    "}\n"
                    "QPushButton:pressed{\n"
                	"border: 3px inset #270066;\n"
                    "}")
        controls = PlayerControls()
        controls.setState(self.player.state())
        controls.setVolume(self.player.volume())
        controls.setMuted(controls.isMuted())

        controls.play.connect(self.player.play)
        controls.pause.connect(self.player.pause)
        controls.stop.connect(self.player.stop)
        controls.next.connect(self.playlist.next)
        controls.previous.connect(self.previousClicked)
        controls.changeVolume.connect(self.player.setVolume)
        controls.changeMuting.connect(self.player.setMuted)
        controls.changeRate.connect(self.player.setPlaybackRate)
        controls.stop.connect(self.videoWidget.update)

        self.player.stateChanged.connect(controls.setState)
        self.player.volumeChanged.connect(controls.setVolume)
        self.player.mutedChanged.connect(controls.setMuted)

        self.fullScreenButton = QPushButton("Full Screen")
        self.fullScreenButton.setStyleSheet("QPushButton{\n"
                        	"background-color: #id004c;\n"
                        	"color: #e300ff;\n"
                        	"border: 3px outset #270066;\n"
                        	"font-size: 14px;"
                        	"width: 100px;"
                            "}\n"
                            "QPushButton:pressed{\n"
                        	"border: 3px inset #270066;\n"
                            "}")
        self.fullScreenButton.setCheckable(True)

        self.colorButton = QPushButton("Options")
        self.colorButton.setStyleSheet("QPushButton{\n"
                        	"background-color: #id004c;\n"
                        	"color: #e300ff;\n"
                        	"border: 3px outset #270066;\n"
                        	"font-size: 14px;"
                        	"width: 100px;"
                            "}\n"
                            "QPushButton:pressed{\n"
                        	"border: 3px inset #270066;\n"
                            "}")
        self.colorButton.setEnabled(False)
        self.colorButton.clicked.connect(self.showColorDialog)

        self.invButton = QPushButton("<")
        self.invButton.setStyleSheet("QPushButton{\n"
                        	"background-color: #id004c;\n"
                        	"color: #00ff00;\n"
                        	"border: 3px outset #270066;\n"
                        	"font-size: 14px;"
                        	"width: 30px;"
                            "}\n"
                            "QPushButton:pressed{\n"
                        	"border: 3px inset #270066;\n"
                            "}")
        self.invButton.clicked.connect(self.aninvise)

        self.anButton = QPushButton(">")
        self.anButton.setStyleSheet("QPushButton{\n"
                                    "background-color: #id004c;\n"
                                	"color: #00ff00;\n"
                                    "border: 3px outset #270066;\n"
                                	"font-size: 14px;"
                                	"width: 30px;"
                                    "}\n"
                                    "QPushButton:pressed{\n"
                                	"border: 3px inset #270066;\n"
                                    "}")
        self.anButton.clicked.connect(self.invise)
        
        displayLayout = QHBoxLayout()
        displayLayout.addWidget(self.videoWidget, 2)
        displayLayout.addWidget(self.playlistView)

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(openButton)
        controlLayout.addStretch(1)
        controlLayout.addWidget(controls)
        controlLayout.addStretch(1)
        #controlLayout.addWidget(self.fullScreenButton)
        controlLayout.addWidget(self.invButton)
        controlLayout.addWidget(self.anButton)
        controlLayout.addWidget(self.colorButton)

        layout = QVBoxLayout()
        layout.addLayout(displayLayout)
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.slider)
        hLayout.addWidget(self.labelDuration)
        layout.addLayout(hLayout)
        layout.addLayout(controlLayout)

        self.setLayout(layout)
        self.metaDataChanged()
        self.addToPlaylist(playlist)


    def mouseMoveEvent(self, event):
        if self.press:
            self.move(event.globalPos() - self.last_pos)

    def aninvise(self):
        self.playlistView.show()

    def invise(self):
        self.playlistView.hide()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press = True
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press = False

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(Qt.red, 5))
        painter.drawRect(self.rect())

    def keyReleaseEvent(self, event):
        #закрываю на кнопку ESC
        if event.key() == Qt.Key_Escape:
            self.close()

    def open(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Open Files")
        self.addToPlaylist(fileNames)

    def addToPlaylist(self, fileNames):
        for name in fileNames:
            fileInfo = QFileInfo(name)
            if fileInfo.exists():
                url = QUrl.fromLocalFile(fileInfo.absoluteFilePath())
                if fileInfo.suffix().lower() == 'm3u':
                    self.playlist.load(url)
                else:
                    self.playlist.addMedia(QMediaContent(url))
            else:
                url = QUrl(name)
                if url.isValid():
                    self.playlist.addMedia(QMediaContent(url))

    def durationChanged(self, duration):
        duration /= 1000

        self.duration = duration
        self.slider.setMaximum(duration)

    def positionChanged(self, progress):
        progress /= 1000

        if not self.slider.isSliderDown():
            self.slider.setValue(progress)

        self.updateDurationInfo(progress)

    def metaDataChanged(self):
        if self.player.isMetaDataAvailable():
            self.setTrackInfo("%s - %s" % (
                    self.player.metaData(QMediaMetaData.AlbumArtist),
                    self.player.metaData(QMediaMetaData.Title)))

    def previousClicked(self):
        if self.player.position() <= 5000:
            self.playlist.previous()
        else:
            self.player.setPosition(0)

    def jump(self, index):
        if index.isValid():
            self.playlist.setCurrentIndex(index.row())
            self.player.play()

    def playlistPositionChanged(self, position):
        self.playlistView.setCurrentIndex(
                self.playlistModel.index(position, 0))

    def seek(self, seconds):
        self.player.setPosition(seconds * 1000)

    def statusChanged(self, status):
        self.handleCursor(status)

        if status == QMediaPlayer.LoadingMedia:
            self.setStatusInfo("Loading...")
        elif status == QMediaPlayer.StalledMedia:
            self.setStatusInfo("Media Stalled")
        elif status == QMediaPlayer.EndOfMedia:
            QApplication.alert(self)
        elif status == QMediaPlayer.InvalidMedia:
            self.displayErrorMessage()
        else:
            self.setStatusInfo("")

    def handleCursor(self, status):
        if status in (QMediaPlayer.LoadingMedia, QMediaPlayer.BufferingMedia, QMediaPlayer.StalledMedia):
            self.setCursor(Qt.BusyCursor)
        else:
            self.unsetCursor()

    def bufferingProgress(self, progress):
        self.setStatusInfo("Buffering %d%" % progress)

    def videoAvailableChanged(self, available):
        if available:
            self.fullScreenButton.clicked.connect(
                    self.videoWidget.setFullScreen)
            self.videoWidget.fullScreenChanged.connect(
                    self.fullScreenButton.setChecked)

            if self.fullScreenButton.isChecked():
                self.videoWidget.setFullScreen(True)
        else:
            self.fullScreenButton.clicked.disconnect(
                    self.videoWidget.setFullScreen)
            self.videoWidget.fullScreenChanged.disconnect(
                    self.fullScreenButton.setChecked)

            self.videoWidget.setFullScreen(False)

        self.colorButton.setEnabled(available)

    def setTrackInfo(self, info):
        self.trackInfo = info

        if self.statusInfo != "":
            self.setWindowTitle("%s | %s" % (self.trackInfo, self.statusInfo))
        else:
            self.setWindowTitle(self.trackInfo)

    def setStatusInfo(self, info):
        self.statusInfo = info

        if self.statusInfo != "":
            self.setWindowTitle("%s | %s" % (self.trackInfo, self.statusInfo))
        else:
            self.setWindowTitle(self.trackInfo)

    def displayErrorMessage(self):
        self.setStatusInfo(self.player.errorString())

    def updateDurationInfo(self, currentInfo):
        duration = self.duration
        if currentInfo or duration:
            currentTime = QTime((currentInfo/3600)%60, (currentInfo/60)%60,
                    currentInfo%60, (currentInfo*1000)%1000)
            totalTime = QTime((duration/3600)%60, (duration/60)%60,
                    duration%60, (duration*1000)%1000);

            format = 'hh:mm:ss' if duration > 3600 else 'mm:ss'
            tStr = currentTime.toString(format) + " / " + totalTime.toString(format)
        else:
            tStr = ""

        self.labelDuration.setText(tStr)

    def showColorDialog(self):
        if self.colorDialog is None:
            brightnessSlider = QSlider(Qt.Horizontal)
            brightnessSlider.setRange(-100, 100)
            brightnessSlider.setValue(self.videoWidget.brightness())
            brightnessSlider.sliderMoved.connect(
                    self.videoWidget.setBrightness)
            self.videoWidget.brightnessChanged.connect(
                    brightnessSlider.setValue)

            contrastSlider = QSlider(Qt.Horizontal)
            contrastSlider.setRange(-100, 100)
            contrastSlider.setValue(self.videoWidget.contrast())
            contrastSlider.sliderMoved.connect(self.videoWidget.setContrast)
            self.videoWidget.contrastChanged.connect(contrastSlider.setValue)

            hueSlider = QSlider(Qt.Horizontal)
            hueSlider.setRange(-100, 100)
            hueSlider.setValue(self.videoWidget.hue())
            hueSlider.sliderMoved.connect(self.videoWidget.setHue)
            self.videoWidget.hueChanged.connect(hueSlider.setValue)

            saturationSlider = QSlider(Qt.Horizontal)
            saturationSlider.setRange(-100, 100)
            saturationSlider.setValue(self.videoWidget.saturation())
            saturationSlider.sliderMoved.connect(
                    self.videoWidget.setSaturation)
            self.videoWidget.saturationChanged.connect(
                    saturationSlider.setValue)

            layout = QFormLayout()
            layout.addRow("Brightness", brightnessSlider)
            layout.addRow("Contrast", contrastSlider)
            layout.addRow("Hue", hueSlider)
            layout.addRow("Saturation", saturationSlider)

            button = QPushButton("Close")
            button.setStyleSheet("QPushButton{\n"
                    	"background-color: #id400c;\n"
                    	"color: #e300ff;\n"
                    	"border: 3px outset #270066;\n"
                        "}\n"
                        "QPushButton:pressed{\n"
                    	"border: 3px inset #270066;\n"
                        "}")
            layout.addRow(button)

            self.colorDialog = QDialog(self)
            self.colorDialog.setStyleSheet("background-color: #id004c;\n"
            "color: #e300ff;\n")
            self.colorDialog.setWindowTitle("Color Options")
            self.colorDialog.setLayout(layout)

            button.clicked.connect(self.colorDialog.close)

        self.colorDialog.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = Player(sys.argv[1:])
    player.show()
    sys.exit(app.exec_())
