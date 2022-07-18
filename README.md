# tcc-build

A script to set up a simple C development environment with TCC.

The script requires Python and `7za` on your path.  The names of the archives required can be
found in `archives/archives.txt`.  Executables `lua.exe` and `sqlite3.exe` are included in
the build result, as well as their siblings.  `curl.exe` is excluded since it is shipped
with Windows 10 and 11.
