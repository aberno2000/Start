@echo on
pyinstaller --onefile --add-binary ".\Release\nia_start.exe;." --add-binary ".\Release\gmsh-4.12.dll;." --add-binary ".\Release\libgmp-10.dll;." --add-binary "C:\Users\vladislavsemykin\.conda\envs\startenv\Lib\site-packages\vtk.libs\*.dll;." --paths ".\ui;.\include;.\icons;." --name nia_start ui\main.py
pyinstaller nia_start.spec
pause
