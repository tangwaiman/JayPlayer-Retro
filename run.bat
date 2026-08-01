@echo off
:: 切換到你放 Python 程式碼的資料夾（請根據你的實際路徑修改，例如 C:\music_player）
cd /d "C:\Python34"

:: 用 pythonw 啟動你的程式，後面加上 start 可以在背景行，bat 視窗會秒速自動關閉
start "" pythonw "music_player.pyw"

exit
