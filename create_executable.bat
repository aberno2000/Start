@echo on

for /f "tokens=2 delims==" %%i in ('"wmic os get localdatetime /value"') do set datetime=%%i
set current_date=%datetime:~6,2%.%datetime:~4,2%.%datetime:~0,4%
set output_name=nia_start_%current_date%

pyinstaller --onefile --add-binary ".\Release\nia_start.exe;." --add-binary ".\Release\gmsh-4.12.dll;." --add-binary ".\Release\libgmp-10.dll;." --add-data ".\icons;icons" --paths ".\ui;.\include" --name %output_name% ui\main.py
pyinstaller nia_start.spec

xcopy /E /I .\icons .\dist\icons
copy .\Release\nia_start.exe .\dist\nia_start.exe

pause
