#!/bin/bash
# build_mac.sh
# Сборка PyQt6 приложения для macOS в .app с ресурсами и иконкой

# 1️⃣ Настройки
APP_NAME="MusicalLoto"
MAIN_SCRIPT="musical_loto.py"
ICON_FILE="resources/app_icon.icns"       # Иконка для приложения
RESOURCES_DIR="resources"                 # Папка с картинками/ресурсами
VENV_DIR="venv"                           # Виртуальное окружение

# 2️⃣ Активируем виртуальное окружение
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Создаю виртуальное окружение..."
    python3 -m venv $VENV_DIR
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install pyinstaller pyqt6
fi

# 3️⃣ Удаляем старые сборки
rm -rf build dist *.spec

# 4️⃣ Собираем приложение
pyinstaller \
    --noconfirm \
    --onefile \
    --windowed \
    --name "$APP_NAME" \
    --icon "$ICON_FILE" \
    --add-data "$RESOURCES_DIR:$RESOURCES_DIR" \
    "$MAIN_SCRIPT"

# 5️⃣ Завершаем
echo "Сборка завершена!"
echo "Готовое приложение находится в папке dist/$APP_NAME"
