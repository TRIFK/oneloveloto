# musical_loto.py
from __future__ import annotations
import json
import os
import sys
import shutil
from dataclasses import dataclass, asdict
from typing import List, Optional
from collections import Counter

from PyQt6 import QtCore, QtGui, QtWidgets

# Try to import Pillow for palette extraction (optional but recommended)
try:
    from PIL import Image
except Exception:
    Image = None

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
        size = min(self.width(), self.height(), self.barrel_size)
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtCore.Qt.GlobalColor.transparent)

        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Цвет обводки и заливки
        if self.isChecked():
            circle_color = QtGui.QColor(128, 0, 0)  # тёмный при выборе
            text_color = QtGui.QColor(200, 200, 200)
        else:
            circle_color = QtGui.QColor(135, 206, 250)  # полупрозрачная
            text_color = QtGui.QColor(255, 255, 255)

        # Рисуем круг
        circle_pen = QtGui.QPen(circle_color)
        circle_pen.setWidth(max(2, int(size / 25)))
        p.setPen(circle_pen)
        p.setBrush(QtGui.QBrush(QtCore.Qt.GlobalColor.transparent))
        radius = size * 0.45
        center = QtCore.QPointF(size / 2, size / 2)
        p.drawEllipse(center, radius, radius)

        # Рисуем цифру в центре
        font = QtGui.QFont("Poppins", max(10, int(size / 3.6)))
        font.setBold(True)
        p.setFont(font)

        # Тень текста
        shadow_pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 160))
        shadow_pen.setWidth(max(2, int(size / 50)))
        p.setPen(shadow_pen)
        p.drawText(pm.rect().adjusted(2, 2, 2, 2), QtCore.Qt.AlignmentFlag.AlignCenter, str(self.index + 1))

        # Основной текст
        p.setPen(QtGui.QPen(text_color))
        p.drawText(pm.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, str(self.index + 1))

        p.end()
        self.setIcon(QtGui.QIcon(pm))
        self.setIconSize(pm.size())

    def _apply_style(self):
        self.setStyleSheet(
            """
            QPushButton { border: none; border-radius: 20px; background: rgba(255,255,255,0); }
            QPushButton:checked { background: rgba(0,0,0,0); }  /* прозрачный фон, затемнение через _set_icon */
            """
        )

    def _on_clicked(self):
        self.update()  # перерисовать, чтобы _set_icon учёл isChecked()
        self._set_icon()
        self.clicked_with_index.emit(self.index)

    def animate_pop_visual(self):
        r = self.geometry()
        anim = QtCore.QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        anim.setStartValue(r)
        anim.setEndValue(QtCore.QRect(r.x(), r.y() - 8, r.width(), r.height()))
        anim.finished.connect(lambda: QtCore.QTimer.singleShot(160, lambda: self.setGeometry(r)))
        anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# --- TrackWindow: показывает картинку и название трека по центру приложения ---
class TrackWindow(QtWidgets.QWidget):
    def __init__(self, track: Track, parent=None, start_rect: Optional[QtCore.QRect] = None):
        super().__init__(parent)
        self.track = track

        # --- Окно без рамок и с прозрачностью ---
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Dialog |
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # --- Основной layout ---
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        frame = QtWidgets.QFrame()
        frame.setStyleSheet("background: rgba(255,255,255,245); border-radius:16px;")
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setContentsMargins(18, 18, 18, 18)
        vbox.setSpacing(12)

        # --- Кнопка закрытия ---
        close_btn = QtWidgets.QPushButton("✕")
        close_btn.setFixedSize(34, 34)
        close_btn.setStyleSheet(
            "QPushButton { background:#f43f5e; color:white; border:none; border-radius:17px; font-weight:bold; }"
            "QPushButton:hover { background:#ef4444; }"
        )
        close_btn.clicked.connect(self.close)
        h = QtWidgets.QHBoxLayout()
        h.addStretch()
        h.addWidget(close_btn)
        vbox.addLayout(h)

        # --- Картинка трека ---
        self.img_label = QtWidgets.QLabel()
        self.img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.img_label.setScaledContents(False)
        self.img_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                     QtWidgets.QSizePolicy.Policy.Expanding)
        if track.image_path and os.path.exists(track.image_path):
            pix = QtGui.QPixmap(track.image_path)
            max_w, max_h = 860, 620
            pix = pix.scaled(
                min(pix.width(), max_w),
                min(pix.height(), max_h),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation
            )
            self.img_label.setPixmap(pix)
        else:
            self.img_label.setText("🎵 Нет изображения")
            self.img_label.setStyleSheet("font-size:24px; color:#666;")

        # --- Название трека ---
        self.title_label = QtWidgets.QLabel(track.title)
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size:32px; font-weight:500; font-family:'Poppins'; color:#222;")

        vbox.addWidget(self.img_label)
        vbox.addWidget(self.title_label)
        main_layout.addWidget(frame)

        # --- Размеры и ограничения ---
        self.setMinimumSize(400, 300)
        self.setMaximumSize(1920, 1080)

# --- Автоматически делаем размер = 3/4 от родительского окна ---
        if parent:
            parent_rect = parent.geometry()
            new_w = int(parent_rect.width() * 0.75)
            new_h = int(parent_rect.height() * 0.75)
            self.resize(new_w, new_h)

        # Центрируем относительно родителя
            x = parent_rect.center().x() - new_w // 2
            y = parent_rect.center().y() - new_h // 2
            self.move(x, y)
        else:
    # если родителя нет (редкий случай)
            self.resize(900, 700)

        # --- Fade-in анимация ---
        self.setWindowOpacity(0)
        self._fade_anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(420)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()


# --- TracksDialog: теперь поддерживает загрузку изображений для каждого трека ---
class TracksDialog(QtWidgets.QDialog):
    """Диалог редактирования треков и загрузки картинок"""
    def __init__(self, tracks: List[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор треков и обложек")
        self.tracks = tracks
        self.resize(520, 720)
        layout = QtWidgets.QVBoxLayout(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(container)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.line_edits: List[QtWidgets.QLineEdit] = []
        self.image_labels: List[QtWidgets.QLabel] = []

        for i, track in enumerate(tracks):
            hbox = QtWidgets.QHBoxLayout()
            le = QtWidgets.QLineEdit(track.title)
            le.setPlaceholderText(f"Трек {i+1}")
            self.line_edits.append(le)

            img_label = QtWidgets.QLabel()
            img_label.setFixedSize(72, 72)
            img_label.setStyleSheet("border: 1px solid #ccc; border-radius:8px; background: rgba(0,0,0,0.03);")
            img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            img_label.setScaledContents(False)  # Важно: масштабируем вручную
            img_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
            if track.image_path and os.path.exists(track.image_path):
                pix = QtGui.QPixmap(track.image_path)
    # Ограничиваем размеры до макс 1920x1080
                max_w, max_h = 1920, 1080
                pix = pix.scaled(
                min(pix.width(), max_w),
                min(pix.height(), max_h),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation
            )
                img_label.setPixmap(pix)
            else:
                img_label.setText("🖼")
            self.image_labels.append(img_label)

            btn_load = QtWidgets.QPushButton("📂")
            btn_load.setToolTip("Загрузить картинку")
            btn_load.setFixedSize(40, 40)
            # use lambda capturing index
            btn_load.clicked.connect(lambda _, idx=i: self.load_image(idx))

            hbox.addWidget(le, 3)
            hbox.addWidget(img_label)
            hbox.addWidget(btn_load)
            form.addRow(f"{i+1}.", hbox)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_save = QtWidgets.QPushButton("💾 Сохранить изменения")
        btn_save.clicked.connect(self.save_tracks)
        layout.addWidget(btn_save)

    def load_image(self, index: int):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Изображения (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            # Скопировать в папку приложения, чтобы картинки оставались доступными при переносе
            parent = self.parent()
            if hasattr(parent, "storage"):
                dest_dir = parent.storage.app_dir
            else:
                dest_dir = os.path.join(os.path.expanduser("~"), f".{APP_NAME}")
            os.makedirs(dest_dir, exist_ok=True)
            basename = os.path.basename(file_path)
            dest_path = os.path.join(dest_dir, f"track_{index}_{basename}")
            try:
                shutil.copy(file_path, dest_path)
                self.tracks[index].image_path = dest_path
                pix = QtGui.QPixmap(dest_path).scaled(72, 72, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                                      QtCore.Qt.TransformationMode.SmoothTransformation)
                self.image_labels[index].setPixmap(pix)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изображение:\n{e}")

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

        self.setWindowTitle("1LoveLoto🎵")
        self.resize(1000, 760)  # увеличил окно по умолчанию для удобства

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
        # Таймер
        self.timer_label = QtWidgets.QLabel("00:00")
        font = QtGui.QFont("Poppins", 40)
        font.setBold(True)
        self.timer_label.setFont(font)

        # Добавляем название приложения рядом
        self.app_name_label = QtWidgets.QLabel("1Loveloto")
        app_font = QtGui.QFont("Poppins", 20)
        app_font.setBold(False)
        self.app_name_label.setFont(app_font)
        self.app_name_label.setStyleSheet("color: rgba(0,0,0,0.3);")  # opacity ~0.3
        
        # initial theme colors
        self.primary_color = "#6a11cb"
        self.secondary_color = "#2575fc"
        self.text_on_primary = "#ffffff"

        # template for buttons; will be formatted with primary/secondary
        self.btn_style_template = """
        QPushButton {{
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 {primary}, stop:1 {secondary});
            color: {text};
            border: none; border-radius: 12px;
            padding: 10px 20px; font-size: 16px; font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 {hover1}, stop:1 {hover2});
        }}
        QPushButton:pressed {{ background-color: #1e40af; }}
        """

        # create buttons
        self.start_btn = QtWidgets.QPushButton("▶ Старт/Пауза")
        self.reset_btn = QtWidgets.QPushButton("🔄 Сброс всех бочонков")
        self.settings_btn = QtWidgets.QPushButton("🎶 Треки...")
        self.undo_btn = QtWidgets.QPushButton("↩ Назад")
        self.bg_btn = QtWidgets.QPushButton("🖼 Фон")

        # apply styles
        self.update_button_styles(self.primary_color, self.secondary_color, self.text_on_primary)

        # override some colors for specific buttons (optional)
        self.reset_btn.setStyleSheet(self.reset_btn.styleSheet().replace(self.primary_color, "#f43f5e").replace(self.secondary_color, "#ef4444"))
        self.settings_btn.setStyleSheet(self.settings_btn.styleSheet().replace(self.primary_color, "#22c55e").replace(self.secondary_color, "#16a34a"))
        self.undo_btn.setStyleSheet(self.undo_btn.styleSheet().replace(self.primary_color, "#eab308").replace(self.secondary_color, "#ca8a04"))

        top.addWidget(self.timer_label)
        top.addStretch()
        top.addWidget(self.start_btn)
        top.addWidget(self.reset_btn)
        top.addWidget(self.settings_btn)
        top.addWidget(self.undo_btn)
        top.addWidget(self.bg_btn)
        game_layout.addLayout(top)

        # Сетка бочонков без рамок
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        self.grid_container = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(8)
        scroll.setWidget(self.grid_container)
        game_layout.addWidget(scroll)

        self.stacked.addWidget(self.game_page)

        self.start_btn.clicked.connect(self.toggle_timer)
        self.reset_btn.clicked.connect(self.reset_game)
        self.undo_btn.clicked.connect(self.undo_action)
        self.settings_btn.clicked.connect(self.open_tracks_editor)
        self.bg_btn.clicked.connect(self.change_background)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._elapsed = 0

        self.buttons: List[Optional[BarrelButton]] = []
        self._build_grid()

    def update_button_styles(self, primary: str, secondary: str, text: str):
        # generate hover colors slightly brighter/darker
        def brighten(hexcolor, amt=20):
            c = QtGui.QColor(hexcolor)
            r = min(255, c.red() + amt)
            g = min(255, c.green() + amt)
            b = min(255, c.blue() + amt)
            return f"#{r:02x}{g:02x}{b:02x}"
        def darken(hexcolor, amt=20):
            c = QtGui.QColor(hexcolor)
            r = max(0, c.red() - amt)
            g = max(0, c.green() - amt)
            b = max(0, c.blue() - amt)
            return f"#{r:02x}{g:02x}{b:02x}"

        hover1 = brighten(primary, 12)
        hover2 = darken(secondary, 12)
        style = self.btn_style_template.format(primary=primary, secondary=secondary, text=text, hover1=hover1, hover2=hover2)
        # Apply to main buttons. For others we'll tweak individually afterward.
        for btn in (self.start_btn, self.reset_btn, self.settings_btn, self.undo_btn, self.bg_btn):
            btn.setStyleSheet(style)

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

            # --- Анимация появления бочонков как была ---
            # небольшая задержка для волнообразного появления
            start_geom = QtCore.QRect(btn.x(), btn.y() - 150, btn.width(), btn.height())
            end_geom = btn.geometry()
            btn.setGeometry(start_geom)
            anim = QtCore.QPropertyAnimation(btn, b"geometry")
            anim.setDuration(500 + (i % GRID_COLS) * 50)
            anim.setStartValue(start_geom)
            anim.setEndValue(end_geom)
            anim.setEasingCurve(QtCore.QEasingCurve.Type.OutBounce)
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

        # Анимация “подпрыгивания” бочонка
        try:
            btn.animate_pop_visual()
        except Exception:
            pass

        # Сохраняем для undo
        self.undo_stack.append(index)

        # Закрываем старое окно, если оно есть
        if self.current_track_window:
            self.current_track_window.close()

        # Создаём новое окно TrackWindow, привязанное к MainWindow
        self.current_track_window = TrackWindow(
            self.tracks[index],
            parent=self  # центрирование будет работать внутри TrackWindow
        )
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

    # ---- Background change + palette extraction ----
    def change_background(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите фон", "", "Изображения (*.png *.jpg *.jpeg)")
        if not file_path:
            return

        # Set window background pixmap (scaled to window size)
        pix = QtGui.QPixmap(file_path)
        if not pix.isNull():
            brush = QtGui.QBrush(pix.scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                            QtCore.Qt.TransformationMode.SmoothTransformation))
            pal = self.palette()
            pal.setBrush(QtGui.QPalette.ColorRole.Window, brush)
            self.setAutoFillBackground(True)
            self.setPalette(pal)

        # Try to extract main color from image and update button theme
        palette_info = self.extract_palette(file_path)
        if palette_info:
            primary = palette_info.get("primary", self.primary_color)
            text = "#ffffff" if palette_info.get("is_dark", False) else "#111111"
            # create a secondary color (slightly different)
            c = QtGui.QColor(primary)
            sec = QtGui.QColor(max(0, c.red()-20), max(0, c.green()-10), min(255, c.blue()+20))
            sec_hex = f"#{sec.red():02x}{sec.green():02x}{sec.blue():02x}"
            self.update_button_styles(primary, sec_hex, text)

    def extract_palette(self, img_path: str) -> dict:
        """
        Simple dominant color extraction using Pillow sampling.
        Returns dict { 'primary': '#rrggbb', 'is_dark': True/False }
        """
        if Image is None:
            return {}
        try:
            im = Image.open(img_path).convert("RGB")
            im = im.resize((80, 80))
            pixels = list(im.getdata())
            most = Counter(pixels).most_common(5)
            if not most:
                return {}
            primary_rgb = most[0][0]
            r, g, b = primary_rgb
            primary_hex = f"#{r:02x}{g:02x}{b:02x}"
            luminance = (0.299*r + 0.587*g + 0.114*b)/255
            is_dark = luminance < 0.5
            return {"primary": primary_hex, "is_dark": is_dark}
        except Exception as e:
            print("extract_palette error:", e)
            return {}

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
