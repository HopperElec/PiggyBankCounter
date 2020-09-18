@echo off
title Python program compiler
pyinstaller --clean --onefile --distpath ./ --add-data favicon.png;. --add-data *.ttf;. --add-data coin.mp3;. --add-data images;images main.pyw
pause