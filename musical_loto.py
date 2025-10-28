from __future__ import annotations
import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional
from PyQt6 import QtCore, QtGui, QtWidgets

APP_NAME = "SHISH LOTO"
NUM_TILES = 50
GRID_COLS = 10


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


@dataclass
class Track:
    title: str = ""
    url: str = ""
    image_path: str = ""


class Storage:
    def __init__(self):
        self.app_dir = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.StandardLocation.AppDataLocation
        )
        if not self.app_dir:
            self.app_dir = os.path.join(os.path.expanduser("~"), f".{APP_NAME}")
        os.makedirs(self.app_dir, exist_ok=True)
        self.json_path = os.path.join(self.app_dir, "tracks.json")

    def load_tracks(self) -> List[Track]:
        if not os.path.exists(self.json_path):
            tracks = [Track(title=f"Трек {i+1}") for i in range(NUM_TILES)]
            self.save_tracks(tracks)
            return tracks
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            tracks = [Track(**item) for item in data]
            if len(tracks) < NUM_TILES:
                tracks += [Track(title=f"Трек {i+1}") for i in range(len(tracks), NUM_TILES)]
            elif len(tracks) > NUM_TILES:
                tracks = tracks[:NUM_TILES]
            return tracks

    def save_tracks(self, tracks: List[Track]):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump([asdict(t) for t in tracks], f, ensure_ascii=False, indent=2)


class BarrelButton(QtWidgets.QPushButton):
    clicked_with_index = QtCore.pyqtSignal(int)

    def __init__(self, index: int, track: Track, parent=None, barrel_size=320):
        super().__init__(parent)
        self.index = index
        self.track = track
        self.crossed = False
        self.barrel_size = barrel_size
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setCheckable(True)
        self.setMinimumSize(50, 50)
        self.setMaximumSize(800, 800)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        self._apply_style()
        self._set_icon()
        self.clicked.connect(self._on_clicked)

    def resizeEvent(self, event):
        self._set_icon()
        super().resizeEvent(event)

    def _set_icon(self):
        barrel_icon_path = resource_path("resources/barrel.png")
        size = min(self.width(), self.height(), self.barrel_size)
        if os.path.exists(barrel_icon_path):
            pix = QtGui.QPixmap(barrel_icon_path)
            pix = pix.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                             QtCore.Qt.TransformationMode.SmoothTransformation)
            painter = QtGui.QPainter(pix)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            font = QtGui.QFont("Sans Serif")
            font.setBold(True)
            font.setPointSize(int(size / 8))
            painter.setFont(font)
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
            painter.drawText(pix.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, str(self.index + 1))
            painter.end()
            self.setIcon(QtGui.QIcon(pix))
            self.setIconSize(pix.size())
            return

        pm = QtGui.QPixmap(size, size)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.setBrush(QtGui.QBrush(QtGui.QColor(216, 168, 110)))
        p.setPen(QtGui.QPen(QtGui.QColor(120, 85, 50), 4))
        p.drawRoundedRect(QtCore.QRectF(0, 0, size, size), 28, 28)
        font = QtGui.QFont("Arial")
        font.setBold(False)
        font.setPointSize(int(size / 4))
        p.setFont(font)
        p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        p.drawText(pm.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, str(self.index + 1))
        p.end()
        self.setIcon(QtGui.QIcon(pm))
        self.setIconSize(pm.size())

    def _apply_style(self):
        self.setStyleSheet(
            """
            QPushButton { border: none; border-radius: 20px; background: rgba(255,255,255,180); }
            QPushButton:checked { background: rgba(220,235,255,220); }
            """
        )

    def _on_clicked(self):
        self.crossed = True
        self.update()
        self.clicked_with_index.emit(self.index)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.crossed:
            p = QtGui.QPainter(self)
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            pen = QtGui.QPen(QtGui.QColor(200, 0, 0), 6)
            p.setPen(pen)
            r = self.rect().adjusted(10, 10, -10, -10)
            p.drawLine(r.topLeft(), r.bottomRight())
            p.drawLine(r.topRight(), r.bottomLeft())
            p.end()

    def animate_pop_visual(self):
        r = self.geometry()
        anim = QtCore.QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        anim.setStartValue(r)
        anim.setEndValue(QtCore.QRect(r.x(), r.y() - 8, r.width(), r.height()))
        anim.finished.connect(lambda: QtCore.QTimer.singleShot(160, lambda: self.setGeometry(r)))
        anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


class TrackWindow(QtWidgets.QWidget):
    def __init__(self, track: Track, parent=None, start_rect: Optional[QtCore.QRect] = None):
        super().__init__(parent)
        self.track = track
        self.start_rect_global = start_rect
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Dialog |
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QtWidgets.QHBoxLayout()
        header.addStretch()
        close_btn = QtWidgets.QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(
            "QPushButton {color: black; background: rgba(200,0,0,180); border:none; border-radius:15px; font-weight:bold;}"
            "QPushButton:hover {background: rgba(255,0,0,220);}"
        )
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        label = QtWidgets.QLabel(track.title)
        font = QtGui.QFont()
        font.setPointSize(72)
        font.setBold(True)
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color:##6A5ACD;")
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

        self.effect = QtWidgets.QGraphicsDropShadowEffect(self)
        self.effect.setBlurRadius(25)
        self.effect.setXOffset(0)
        self.effect.setYOffset(4)
        self.effect.setColor(QtGui.QColor(100, 0, 255, 200))
        self.setGraphicsEffect(self.effect)

        self.resize(600, 400)
        if parent:
            parent_rect = parent.geometry()
            center = parent_rect.center()
            self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)
        self._animate()

    def _animate(self):
        self.setWindowOpacity(0)
        anim_opacity = QtCore.QPropertyAnimation(self, b"windowOpacity")
        anim_opacity.setDuration(400)
        anim_opacity.setStartValue(0.1)
        anim_opacity.setEndValue(1)
        anim_geo = QtCore.QPropertyAnimation(self, b"geometry")
        anim_geo.setDuration(600)
        end_rect = self.geometry()
        if self.start_rect_global:
            parent = self.parent() or self.window()
            start_top_left = parent.mapFromGlobal(self.start_rect_global.topLeft())
            start_rect_local = QtCore.QRect(start_top_left, self.start_rect_global.size())
            anim_geo.setStartValue(start_rect_local)
        else:
            anim_geo.setStartValue(QtCore.QRect(end_rect.center().x(), end_rect.center().y(), 0, 0))
        anim_geo.setEndValue(end_rect)
        group = QtCore.QParallelAnimationGroup(self)
        group.addAnimation(anim_opacity)
        group.addAnimation(anim_geo)
        group.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


class TracksDialog(QtWidgets.QDialog):
    """Диалог редактирования названий треков"""
    def __init__(self, tracks: List[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор треков")
        self.tracks = tracks
        self.resize(400, 600)
        layout = QtWidgets.QVBoxLayout(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(container)

        self.line_edits: List[QtWidgets.QLineEdit] = []
        for i, track in enumerate(tracks):
            le = QtWidgets.QLineEdit(track.title)
            le.setPlaceholderText(f"Трек {i+1}")
            scroll_layout.addWidget(le)
            self.line_edits.append(le)

        container.setLayout(scroll_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_save = QtWidgets.QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_tracks)
        layout.addWidget(btn_save)

    def save_tracks(self):
        for i, le in enumerate(self.line_edits):
            self.tracks[i].title = le.text() if le.text() else f"Трек {i+1}"
        self.accept()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_track_window = None
        self.current_track_index = None
        self.undo_stack: List[int] = []

        self.setWindowTitle("ШИИИШЬ ЛОТО🎵")
        self.resize(600, 600)

        self.storage = Storage()
        self.tracks: List[Track] = self.storage.load_tracks()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        self.stacked = QtWidgets.QStackedWidget()
        layout.addWidget(self.stacked)

        self.game_page = QtWidgets.QWidget()
        game_layout = QtWidgets.QVBoxLayout(self.game_page)

        top = QtWidgets.QHBoxLayout()
        self.timer_label = QtWidgets.QLabel("00:00")
        font = self.timer_label.font()
        font.setPointSize(40)
        font.setBold(True)
        self.timer_label.setFont(font)

        btn_style = """
        QPushButton {
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 #6a11cb, stop:1 #2575fc);
            color: white; border: none; border-radius: 12px;
            padding: 10px 20px; font-size: 16px; font-weight: bold;
        }
        QPushButton:hover {
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 #7d2ae8, stop:1 #3b82f6);
        }
        QPushButton:pressed { background-color: #1e40af; }
        """

        self.start_btn = QtWidgets.QPushButton("▶ Старт/Пауза")
        self.start_btn.setStyleSheet(btn_style)

        self.reset_btn = QtWidgets.QPushButton("🔄 Сброс всех бочонков")
        self.reset_btn.setStyleSheet(btn_style.replace("#6a11cb", "#f43f5e").replace("#2575fc", "#ef4444"))

        self.settings_btn = QtWidgets.QPushButton("🎶 Треки...")
        self.settings_btn.setStyleSheet(btn_style.replace("#6a11cb", "#22c55e").replace("#2575fc", "#16a34a"))
        self.settings_btn.clicked.connect(self.open_tracks_editor)

        self.undo_btn = QtWidgets.QPushButton("↩ Назад")
        self.undo_btn.setStyleSheet(btn_style.replace("#6a11cb", "#eab308").replace("#2575fc", "#ca8a04"))

        top.addWidget(self.timer_label)
        top.addStretch()
        top.addWidget(self.start_btn)
        top.addWidget(self.reset_btn)
        top.addWidget(self.settings_btn)
        top.addWidget(self.undo_btn)
        game_layout.addLayout(top)

        # Сетка бочонков без рамок
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        self.grid_container = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(5)
        scroll.setWidget(self.grid_container)
        game_layout.addWidget(scroll)

        self.stacked.addWidget(self.game_page)

        self.start_btn.clicked.connect(self.toggle_timer)
        self.reset_btn.clicked.connect(self.reset_game)
        self.undo_btn.clicked.connect(self.undo_action)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._elapsed = 0

        self.buttons: List[Optional[BarrelButton]] = []
        self._build_grid()

    def _build_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        self.buttons = []

        for i in range(NUM_TILES):
            btn = BarrelButton(i, self.tracks[i], parent=self.grid_container)
            btn.clicked_with_index.connect(self.on_barrel_clicked)
            r, c = divmod(i, GRID_COLS)
            self.grid_layout.addWidget(btn, r, c)
            self.buttons.append(btn)

        # --- Анимация появления бочонков ---
        start_geom = QtCore.QRect(btn.x(), btn.y() - 150, btn.width(), btn.height())
        end_geom = btn.geometry()
        btn.setGeometry(start_geom)

        anim = QtCore.QPropertyAnimation(btn, b"geometry")
        anim.setDuration(500 + (i % GRID_COLS) * 50)  # небольшой сдвиг по колонкам для эффекта волны
        anim.setStartValue(start_geom)
        anim.setEndValue(end_geom)
        anim.setEasingCurve(QtCore.QEasingCurve.Type.OutBounce)  # подпрыгивание
        anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def toggle_timer(self):
        if self._timer.isActive():
            self._timer.stop()
        else:
            self._timer.start()

    def reset_timer(self):
        self._timer.stop()
        self._elapsed = 0
        self._render_time()

    def _tick(self):
        self._elapsed += 1
        self._render_time()

    def _render_time(self):
        m, s = divmod(self._elapsed, 60)
        self.timer_label.setText(f"{m:02d}:{s:02d}")

    def reset_game(self):
        self.undo_stack.clear()
        self.reset_timer()
        for btn in self.buttons:
            btn.setChecked(False)
            btn.crossed = False
            btn._set_icon()
            btn.update()

    def undo_action(self):
        if self.current_track_window:
            self.current_track_window.close()
            self.current_track_window = None
            self.current_track_index = None
        if not self.undo_stack:
            return
        index = self.undo_stack.pop()
        btn = self.buttons[index]
        if btn:
            btn.setChecked(False)
            btn.crossed = False
            btn._set_icon()
            btn.update()

    def on_barrel_clicked(self, index: int):
        btn = self.buttons[index]
        if not btn:
            return
        try:
            btn.animate_pop_visual()
        except Exception:
            pass
        self.undo_stack.append(index)
        btn_rect_local = btn.geometry()
        btn_top_left_global = btn.mapToGlobal(QtCore.QPoint(0, 0))
        start_rect_global = QtCore.QRect(btn_top_left_global, btn_rect_local.size())
        if self.current_track_window:
            self.current_track_window.close()
        self.current_track_window = TrackWindow(self.tracks[index], parent=self, start_rect=start_rect_global)
        self.current_track_window.show()
        self.current_track_index = index

    def mousePressEvent(self, event):
        widget = self.childAt(event.position().toPoint())
        if self.current_track_window and not isinstance(widget, BarrelButton):
            self.current_track_window.close()
            self.current_track_window = None
            self.current_track_index = None
        super().mousePressEvent(event)

    def adapt_fullscreen(self):
        self.showMaximized()

    def open_tracks_editor(self):
        dlg = TracksDialog(self.tracks, self)
        if dlg.exec():
            for btn in self.buttons:
                btn._set_icon()
                btn.update()
            self.storage.save_tracks(self.tracks)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path("resources/app_icon.ico")))
     # Splash Screen
    splash_pix = QtGui.QPixmap(resource_path("resources/splash.png"))
    splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowType.FramelessWindowHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    QtWidgets.QApplication.processEvents()
    QtCore.QTimer.singleShot(1000, splash.close)  # 2 секунды

    window = MainWindow()
    QtCore.QTimer.singleShot(2000, window.show)  # показать после закрытия сплэш

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
