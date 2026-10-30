@echo off
chcp 65001 >nul
if not exist www mkdir www
copy /y index.html www\ >nul
copy /y manifest.webmanifest www\ >nul
copy /y sw.js www\ >nul
copy /y icon.svg www\ >nul
copy /y icon.ico www\ >nul
copy /y icon-*.png www\ >nul
python -m pip install --upgrade pyinstaller pywebview
python -m PyInstaller --noconsole --onefile --name TrekerPitaniya --add-data "www;www" --icon www\icon.ico desktop_app.py
echo Готово: dist\TrekerPitaniya.exe
pause
