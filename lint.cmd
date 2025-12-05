@echo off

rem example of batch file to run ruff and mypy for both python 3.9 and 3.13  

set "ORIGINAL_PATH=%PATH%"
pushd %CD%

rem cd calibre-plugin

echo Checking ruff 3.8
set path=%localappdata%\Programs\Python\Python38;%localappdata%\Programs\Python\Python38\Scripts\
ruff check calibre-plugin
echo Checking mypy 3.8
mypy --package calibre-plugin
echo.

set path=C:\Python313;%AppData%\Python\Python313\Scripts\
echo Checking ruff 3.11/3.13
ruff check calibre-plugin
echo Checking mypy 3.11/3.13
mypy --config-file .mypy311.ini --package calibre-plugin

popd
set "PATH=%ORIGINAL_PATH%"
