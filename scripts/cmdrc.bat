@echo off

set Path=%Path%;%~dp0
for /F %%F in ('dir /b /ad %~dp0') do call :addpath %~dp0%%F

doskey ls=dir /ogn $* $B findstr /r "^[012]"
doskey config=subl %~dpf0
set prompt=[%COMPUTERNAME%] $P$_$T$S$G$S

exit /b

:addpath
set Path=%~1;%Path%
rem if exist %~1\bin\ set Path=%Path%;%~1\bin
rem if exist %~1\Scripts\ set Path=%Path%;%~1\Scripts
exit /b
