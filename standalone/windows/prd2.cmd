@echo off
rem Starts prd2 with the Python and Git bundled next to this script.
setlocal
set "BUNDLE_DIR=%~dp0"

rem Bundled Git first. Its usr\bin goes last: it provides sh and sed for prd2's git filter without shadowing Windows commands.
set "PATH=%BUNDLE_DIR%git\cmd;%PATH%;%BUNDLE_DIR%git\usr\bin"

rem -I keeps the user's PYTHONPATH, user site-packages and current directory out of the bundle.
rem -X utf8 reads and writes UTF-8; the legacy Windows code page cannot store Czech letters in object names.
"%BUNDLE_DIR%python\python.exe" -I -X utf8 -c "from deployment_manager.main import main; main(prog_name='prd2')" %*
exit /b %ERRORLEVEL%
