#! python3

import glob
import os
import subprocess
import sys
from urllib.request import urlopen


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

    print("Loading archives...")
    with open("archives\\archives.txt") as f:
        archives = {}
        filenames = {}
        for line in f:
            parts = line.strip().split(maxsplit=1)
            archives[parts[0]] = parts[1]
            filenames[parts[0]] = parts[1].split("/")[-1]

    print("Checking archives...")
    for name, url in archives.items():
        filename = f"archives\\{filenames[name]}"
        if not os.path.isfile(filename):
            print(f"  {url}")
            response = urlopen(url)
            with open(filename, "wb") as f:
                f.write(response.read())

    print("Extracting archives...")
    os.mkdir("temp")
    cmd(f"7za x -otemp archives\\{filenames['tcc-bin']}")
    cmd(f"7za x -otemp archives\\{filenames['lua-src']}")
    cmd(f"7za x -otemp temp\\{filenames['lua-src'][:-3]}")
    cmd(f"cmd /c rename temp\\{filenames['lua-src'][:-7]} lua")
    cmd(f"7za x -otemp archives\\{filenames['sqlite-src']}")
    cmd(f"cmd /c rename temp\\{filenames['sqlite-src'][:-4]} sqlite")
    cmd(f"7za x -otemp\\sqlite archives\\{filenames['sqlite-bin']}")
    cmd(f"7za x -otemp archives\\{filenames['sqlite-tools']}")
    cmd(f"cmd /c move temp\\{filenames['sqlite-tools'][:-4]}\\* temp\\sqlite")
    cmd(f"7za x -otemp archives\\{filenames['glfw-bin']}")
    cmd(f"cmd /c rename temp\\{filenames['glfw-bin'][:-4]} glfw-bin")
    cmd(f"7za x -otemp archives\\{filenames['glfw-src']}")
    cmd(f"7za x -otemp archives\\{filenames['win-api']}")
    cmd(f"cmd /c rename temp\\{filenames['win-api'][:-4]} win-api")
    cmd(f"7za x -otemp archives\\{filenames['glut-bin']}")
    cmd(f"7za x -otemp archives\\{filenames['curl-bin']}")
    curl_archive = glob.glob("temp\\curl-*")[0]
    cmd(f"cmd /c rename {curl_archive} curl")

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
    cmd("temp\\tcc\\tcc.exe -impdef temp\\tcc\\sqlite3.dll -o temp\\tcc\\lib\\sqlite3.def")

    print("Deploying GLFW...")
    cmd("cmd /c copy temp\\glfw-bin\\lib-mingw-w64\\glfw3.dll temp\\tcc")
    cmd("xcopy temp\\glfw-bin\\include temp\\tcc\\include /E")
    cmd("temp\\tcc\\tcc.exe -impdef temp\\tcc\\glfw3.dll -o temp\\tcc\\lib\\glfw3.def")

    print("Deploying FreeGLUT...")
    cmd("cmd /c copy temp\\freeglut\\bin\\x64\\freeglut.dll temp\\tcc")
    cmd("xcopy temp\\freeglut\\include temp\\tcc\\include /E")
    cmd("temp\\tcc\\tcc.exe -impdef temp\\tcc\\freeglut.dll -o temp\\tcc\\lib\\freeglut.def")

    print("Deploying cURL...")
    cmd("cmd /c copy temp\\curl\\bin\\libcurl-x64.dll temp\\tcc\\libcurl.dll")
    cmd("xcopy temp\\curl\\include temp\\tcc\\include /E")
    cmd("temp\\tcc\\tcc.exe -impdef temp\\tcc\\libcurl.dll -o temp\\tcc\\lib\\libcurl.def")

    print("Deploying system headers...")
    cmd("cmd /c rename temp\\win-api\\include\\winapi\\windows.h windows.h.bak")
    cmd("xcopy temp\\win-api\\include temp\\tcc\\include /E")

    print("Compiling extra math library...")
    cmd("temp\\tcc\\tcc.exe math.c -shared -o temp\\tcc\\m.dll")
    cmd("cmd /c move temp\\tcc\\m.def temp\\tcc\\lib")

    print("\nTCC is available in temp\\tcc")
    print("Try compiling the GLFW examples")


if __name__ == '__main__':
    main()
