@echo off

set T=-m32
if %PROCESSOR_ARCHITECTURE%_==AMD64_ set T=-m64
if %PROCESSOR_ARCHITEW6432%_==AMD64_ set T=-m64

set PATH=%~dp0tcc;%PATH%
set CC=tcc
if _%1==_gcc set CC=%1

echo Compiling time...
%CC% %T% utils/time.c -o time.exe
if errorlevel 1 goto :nocc

call :compile gmake
if errorlevel 1 goto :stop

call :compile busybox
if errorlevel 1 goto :stop

rem start sh -t "BUSYBOX FOR TCC" -c ./menu.sh
exit 0

:nocc
echo.
echo Could not find a working TinyCC.

:stop
pause
exit 1

:compile
echo Compiling %1...
cd %1 && %CC% %T% @0.tcc/%1.%CC%.rsp -w
if errorlevel 1 exit /B 1
cd ..
exit /B 0
