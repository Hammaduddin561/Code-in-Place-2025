import sys
import os
import re
import requests
import pygame
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QSlider, QListWidget, QLineEdit, QSizePolicy
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent

def clean_song_title(title):
    return re.sub(r'\(.*?\)', '', title).replace("-", " ").strip()

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #151515; border-radius: 15px;")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        left_panel = QVBoxLayout()
        self.album_cover = QLabel(self)
        self.album_cover.setStyleSheet("border-radius: 25px; background-color: #222222;")
        self.set_default_album_art()
        self.album_cover.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.album_cover, alignment=Qt.AlignCenter)
        self.track_title = QLabel("No Track Selected", self)
        self.track_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        self.track_title.setAlignment(Qt.AlignCenter)
        self.track_artist = QLabel("Unknown Artist", self)
        self.track_artist.setStyleSheet("color: #aaaaaa; font-size: 16px;")
        self.track_artist.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.track_title)
        left_panel.addWidget(self.track_artist)
        control_layout = QHBoxLayout()
        self.prev_button = QPushButton("⏮")
        self.play_button = QPushButton("▶")
        self.pause_button = QPushButton("⏸")
        self.stop_button = QPushButton("⏹")
        self.next_button = QPushButton("⏭")
        for btn in [self.prev_button, self.play_button, self.pause_button, self.stop_button, self.next_button]:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setStyleSheet("QPushButton { background-color: #333333; color: white; border: none; border-radius: 12px; font-size: 18px; } QPushButton:hover { background-color: #444444; }")
            control_layout.addWidget(btn)
        left_panel.addLayout(control_layout)
        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.setStyleSheet("QSlider::groove:horizontal { height: 10px; background: #2e2e2e; border-radius: 4px; } QSlider::handle:horizontal { background: white; width: 16px; margin: -4px 0; border-radius: 8px; }")
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00", self)
        self.current_time_label.setStyleSheet("color: white; font-size: 16px;")
        self.total_time_label = QLabel("0:00", self)
        self.total_time_label.setStyleSheet("color: white; font-size: 16px;")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        volume_layout = QHBoxLayout()
        vol_label = QLabel("Volume:", self)
        vol_label.setStyleSheet("color: white; font-size: 16px;")
        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet("QSlider::groove:horizontal { height: 10px; background: #2e2e2e; border-radius: 4px; } QSlider::handle:horizontal { background: white; width: 16px; margin: -4px 0; border-radius: 8px; }")
        volume_layout.addWidget(vol_label)
        volume_layout.addWidget(self.volume_slider)
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addLayout(time_layout)
        progress_layout.addLayout(volume_layout)
        left_panel.addLayout(progress_layout)
        main_layout.addLayout(left_panel, 3)
        right_panel = QVBoxLayout()
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setStyleSheet("QLineEdit { border: 1px solid #444444; border-radius: 12px; padding: 12px; background-color: #1c1c1e; color: white; font-size: 16px; }")
        right_panel.addWidget(self.search_bar)
        self.playlist_view = QListWidget(self)
        self.playlist_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.playlist_view.setStyleSheet("QListWidget { background-color: #1e1e1e; color: white; border: none; font-size: 16px; } QListWidget::item:selected { background-color: #333333; border-radius: 8px; }")
        right_panel.addWidget(self.playlist_view, 1)
        playlist_control_layout = QHBoxLayout()
        self.add_button = QPushButton("➕ Add")
        self.remove_button = QPushButton("➖ Remove")
        for btn in [self.add_button, self.remove_button]:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setStyleSheet("QPushButton { background-color: #333333; color: white; border: none; border-radius: 10px; font-size: 16px; } QPushButton:hover { background-color: #444444; }")
            playlist_control_layout.addWidget(btn)
        right_panel.addLayout(playlist_control_layout)
        main_layout.addLayout(right_panel, 2)
        pygame.mixer.init()
        self.media_player = QMediaPlayer(self)
        self.playlist = QMediaPlaylist(self)
        self.media_player.setPlaylist(self.playlist)
        self.media_player.setVolume(50)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.progress_slider.sliderMoved.connect(self.media_player.setPosition)
        self.volume_slider.valueChanged.connect(self.media_player.setVolume)
        self.play_button.clicked.connect(self.media_player.play)
        self.pause_button.clicked.connect(self.media_player.pause)
        self.stop_button.clicked.connect(self.media_player.stop)
        self.prev_button.clicked.connect(self.playlist.previous)
        self.next_button.clicked.connect(self.playlist.next)
        self.add_button.clicked.connect(self.add_tracks)
        self.remove_button.clicked.connect(self.remove_selected_track)
        self.playlist_view.itemDoubleClicked.connect(self.playlist_item_double_clicked)
        self.media_player.currentMediaChanged.connect(self.on_media_changed)
    def update_position(self, position):
        self.progress_slider.setValue(position)
        self.current_time_label.setText(self.format_time(position))
    def update_duration(self, duration):
        self.progress_slider.setRange(0, duration)
        self.total_time_label.setText(self.format_time(duration))
    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    def add_tracks(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Music", "", "Audio Files (*.mp3 *.wav *.m4a)")
        if files:
            for file_path in files:
                url = QUrl.fromLocalFile(file_path)
                self.playlist.addMedia(QMediaContent(url))
                item_text = os.path.basename(file_path)
                self.playlist_view.addItem(item_text)
    def remove_selected_track(self):
        row = self.playlist_view.currentRow()
        if row >= 0:
            self.playlist.removeMedia(row)
            self.playlist_view.takeItem(row)
    def playlist_item_double_clicked(self, item):
        row = self.playlist_view.row(item)
        self.playlist.setCurrentIndex(row)
        self.media_player.play()
        self.on_media_changed(self.playlist.currentMedia())
    def on_media_changed(self, media):
        if media.isNull():
            self.track_title.setText("No Track Selected")
            self.track_artist.setText("Unknown Artist")
            return
        file_path = media.canonicalUrl().toLocalFile()
        base_name = os.path.basename(file_path)
        self.track_title.setText(base_name)
        self.track_artist.setText("Unknown Artist")
    def set_default_album_art(self):
        default_art = QPixmap(350, 350)
        default_art.fill(Qt.darkGray)
        self.album_cover.setPixmap(default_art)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())
