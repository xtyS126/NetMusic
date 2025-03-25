# config.py
import os
from secrets import token_hex
import sys

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///music.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(sys._MEIPASS, 'uploads') if hasattr(sys, '_MEIPASS') else 'uploads'
    ALLOWED_EXTENSIONS = {'mp3', 'wav'}
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
    SECRET_KEY = token_hex(16)
