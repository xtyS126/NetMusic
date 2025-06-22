import os
import sys
from PyInstaller.__main__ import run

if __name__ == '__main__':
    opts = [
        'app.py',
        '--onefile',
        '--add-data', 'templates;templates',
        '--add-data', 'config.py;.',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=flask_login',
        '--hidden-import=wtforms',
        '--hidden-import=mutagen',
        '--clean'
    ]
    run(opts)