#! python3

import glob
import os
import subprocess
import sys

def cmd(command, check=True, **kwargs):
    if isinstance(command, str):
        command = command.split()
    worker = subprocess.Popen(command,
        stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
        **kwargs)
    stdout = worker.communicate()[0].decode(sys.stdout.encoding or "utf-8")
    if worker.wait() != 0:
        print(" ".join('"%s"' % p if " " in p else p for p in command))
        sys.exit(stdout.rstrip())

def main():
    os.chdir(os.path.dirname(__file__))
    if os.path.isdir("temp"):
        print("Clearing previous build...")
        cmd("cmd /c rmdir /s /q temp")

    print("Extracting archives...")
    os.mkdir("temp")
    cmd("7za x -otemp archives\\tcc-0.9.27-win64-bin.zip")
    cmd("7za x -otemp archives\\lua-5.3.5.tar.gz")
    cmd("7za x -otemp temp\\lua-5.3.5.tar")
    cmd("cmd /c rename temp\\lua-5.3.5 lua")
    cmd("7za x -otemp archives\\sqlite-amalgamation-3330000.zip")
    cmd("cmd /c rename temp\\sqlite-amalgamation-3330000 sqlite")
    cmd("7za x -otemp\\sqlite archives\\sqlite-dll-win64-x64-3330000.zip")
    cmd("7za x -otemp archives\\sqlite-tools-win32-x86-3330000.zip")
    cmd("cmd /c move temp\\sqlite-tools-win32-x86-3330000\\* temp\\sqlite")
    cmd("7za x -otemp archives\\glfw-3.3.2.bin.WIN64.zip")
    cmd("7za x -otemp archives\\glfw-3.3.2.zip")
    cmd("7za x -otemp archives\\winapi-full-for-0.9.27.zip")


    print("Building Lua...")
    lua_src = [f for f in glob.glob("temp\\lua\\src\\*.c")
        if os.path.basename(f) not in ("lua.c", "luac.c")]
    cmd("temp\\tcc\\tcc.exe -D LUA_BUILD_AS_DLL %s -shared -o temp\\tcc\\lua.dll" % (
        " ".join(lua_src),))
    cmd("cmd /c move temp\\tcc\\lua.def temp\\tcc\\lib")
    cmd("temp\\tcc\\tcc.exe %s temp\\lua\\src\\luac.c -o temp\\tcc\\luac.exe" % (
        " ".join(lua_src),))
    cmd("temp\\tcc\\tcc.exe -llua temp\\lua\\src\\lua.c -o temp\\tcc\\lua.exe")
    for header in ("lua.h", "luaconf.h", "lualib.h", "lauxlib.h", "lua.hpp"):
        cmd("cmd /c copy temp\\lua\\src\\%s temp\\tcc\\include" % header)

    print("Deploying SQLite...")
    cmd("cmd /c copy temp\\sqlite\\*.exe temp\\tcc")
    cmd("cmd /c copy temp\\sqlite\\*.h temp\\tcc\\include")
    cmd("cmd /c copy temp\\sqlite\\sqlite3.dll temp\\tcc")
    cmd("cmd /c copy temp\\sqlite\\sqlite3.def temp\\tcc\\lib")

    print("Deploying GLFW...")
    cmd("cmd /c copy temp\\glfw-3.3.2.bin.WIN64\\lib-mingw-w64\\glfw3.dll temp\\tcc")
    cmd("xcopy temp\\glfw-3.3.2.bin.WIN64\\include temp\\tcc\\include /E")
    cmd("temp\\tcc\\tcc.exe -impdef temp\\tcc\\glfw3.dll -o temp\\tcc\\lib\\glfw3.def")

    print("Deploying system headers...")
    cmd("cmd /c rename temp\\winapi-full-for-0.9.27\\include\\winapi\\windows.h windows.h.bak")
    cmd("xcopy temp\\winapi-full-for-0.9.27\\include temp\\tcc\\include /E")

    print("Compiling extra math library...")
    cmd("temp\\tcc\\tcc.exe math.c -shared -o temp\\tcc\\m.dll")
    cmd("cmd /c move temp\\tcc\\m.def temp\\tcc\\lib")

    print("TCC is available in temp\\tcc")
    print("SQLite, Lua, and GLFW available as libraries (-lsqlite3, -llua, -lglfw3)")
    print("Try compiling the GLFW examples")


if __name__ == '__main__':
    main()
