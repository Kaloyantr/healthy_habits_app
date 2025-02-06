import os
from flask import current_app
from werkzeug.utils import secure_filename

def allowed_file(filename, allowed_extensions=None):
    """
    Проверява дали даден файл има позволено разширение.
    
    Ако allowed_extensions не е зададен, ще се използва настройката ALLOWED_EXTENSIONS
    от конфигурацията на приложението (current_app.config).
    """
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_secure_filename(filename):
    """
    Връща сигурно генерирано име за файла, използвайки secure_filename от Werkzeug.
    """
    return secure_filename(filename)

# Можеш да добавиш и други помощни функции, свързани с файловете,
# като например функции за обработка на пътища, копиране на файлове и т.н.
