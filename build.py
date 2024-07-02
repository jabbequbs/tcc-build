#! python3

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from urllib.request import urlopen


def cmd(command, check=True, **kwargs):
    if isinstance(command, str):
        command = command.split()
    worker = subprocess.Popen(command,
        stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
        **kwargs)
    stdout = worker.communicate()[0].decode(sys.stdout.encoding or "utf-8")
    if check and worker.wait() != 0:
        print(" ".join('"%s"' % p if " " in p else p for p in command))
        sys.exit(stdout.rstrip())
    return stdout.rstrip()


def copy(source, destination):
    destdir = destination[:-1] if destination[-1] == "\\" else os.path.dirname(destination)
    os.makedirs(destdir, exist_ok=True)
    if os.path.isdir(source):
        shutil.copytree(source, destination, dirs_exist_ok=True)
    elif os.path.isfile(source):
        if os.path.isdir(destination):
            shutil.copy2(source, os.path.join(destination, os.path.basename(source)))
        else:
            shutil.copy2(source, destination)
    else:
        raise Exception(f"No such source: {source} -> {destination}")


def rmdir(dirname):
    if os.path.isdir(dirname):
        cmd(f"cmd /c rmdir /s /q {dirname}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true",
        help="Remove existing temp and shell directories")
    parser.add_argument("--download", action="store_true",
        help="Just download and extract the archives")
    args = parser.parse_args()

    os.chdir(os.path.dirname(__file__))
    if args.clean:
        print("Clearing previous build...")
        rmdir("temp")
        rmdir("shell")

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
    for dirname, archiveName in filenames.items():
        if os.path.isdir("temp\\"+dirname):
            continue
        print("  "+archiveName)
        cmd(f"py scripts\\extract.py archives\\{archiveName} temp\\{dirname}")

    if args.download:
        return

    copy("scripts\\cmdrc.bat", "shell\\cmdrc.bat")
    copy("temp\\tcc-bin", "shell\\tcc")

    if not os.path.isfile("shell\\tcc\\make.exe"):
        print("Building make/busybox...")
        copy("temp\\tcc-bin", "temp\\busybox\\tcc")
        copy("scripts\\makebox.bat", "temp\\busybox\\makebox.bat")
        cmd("cmd /c call makebox.bat", cwd="temp\\busybox")
        copy("temp\\busybox\\make.exe", "shell\\tcc\\make.exe")
        copy("temp\\busybox\\sh.exe", "shell\\tcc\\sh.exe")

    if not os.path.isfile("shell\\lua\\lua.exe"):
        print("Building Lua...")
        os.mkdir("shell\\lua")
        lua_src = [f for f in glob.glob("temp\\lua-src\\src\\*.c")
            if os.path.basename(f) not in ("lua.c", "luac.c")]
        cmd("shell\\tcc\\tcc.exe -D LUA_BUILD_AS_DLL %s -shared -o shell\\lua\\lua.dll" % (
            " ".join(lua_src),))
        cmd("cmd /c move shell\\lua\\lua.def shell\\tcc\\lib")
        cmd("shell\\tcc\\tcc.exe %s temp\\lua-src\\src\\luac.c -o shell\\lua\\luac.exe" % (
            " ".join(lua_src),))
        cmd("shell\\tcc\\tcc.exe -llua temp\\lua-src\\src\\lua.c -o shell\\lua\\lua.exe")
        for header in ("lua.h", "luaconf.h", "lualib.h", "lauxlib.h", "lua.hpp"):
            copy(f"temp\\lua-src\\src\\{header}", f"shell\\tcc\\include\\{header}")

    if not os.path.isfile("shell\\lua\\fennel.exe"):
        cmd("shell\\tcc\\tcc.exe -llua -luser32 temp\\srlua\\srlua.c -o shell\\lua\\srlua.exe")
        cmd("shell\\tcc\\tcc.exe temp\\srlua\\glue.c -o shell\\lua\\glue.exe")
        cmd("shell\\lua\\glue.exe shell\\lua\\srlua.exe scripts\\lfreeze.lua shell\\lua\\lfreeze.exe")
        cmd("shell\\lua\\lfreeze.exe temp\\fennel-src\\fennel shell\\lua\\fennel.exe shell\\lua\\glue.exe shell\\lua\\srlua.exe")
        copy("temp\\fennel-src\\fennel.lua", "shell\\lua\\lua\\fennel.lua")
        copy("temp\\lunajson\\src\\lunajson.lua", "shell\\lua\\lua\\lunajson.lua")
        copy("temp\\lunajson\\src\\lunajson\\decoder.lua", "shell\\lua\\lua\\lunajson\\decoder.lua")
        copy("temp\\lunajson\\src\\lunajson\\encoder.lua", "shell\\lua\\lua\\lunajson\\encoder.lua")
        copy("temp\\lunajson\\src\\lunajson\\sax.lua", "shell\\lua\\lua\\lunajson\\sax.lua")

    if not os.path.isfile("shell\\lua\\cjson.dll"):
        print("Building lua-cjson...")
        # This command manually determined for this particular version of cjson by looking at the rockspec
        cmd("shell\\tcc\\tcc.exe -shared -o cjson.dll lua_cjson.c strbuf.c fpconv.c -llua -Dstrtoll=_strtoi64 -D_MSC_VER",
            cwd="temp\\lua-cjson")
        cmd("cmd /c copy temp\\lua-cjson\\cjson.dll shell\\lua\\cjson.dll")
        copy("temp\\lua-cjson\\lua\\cjson\\util.lua", "shell\\lua\\lua\\cjson\\util.lua")

    # print("Building luasocket...")
    # still broken, need to analyze the rockspec and try some more things
    # seems to be due to the tcc winapi being incomplete, maybe need a complete windows sdk

    if not os.path.isfile("shell\\sqlite\\sqlite3.exe"):
        print("Deploying SQLite...")
        os.mkdir("shell\\sqlite")
        cmd("cmd /c copy temp\\sqlite-tools\\*.exe shell\\sqlite")
        cmd("cmd /c copy temp\\sqlite-src\\*.h shell\\tcc\\include")
        cmd("cmd /c copy temp\\sqlite-bin\\sqlite3.dll shell\\sqlite")
        cmd("shell\\tcc\\tcc.exe -impdef shell\\sqlite\\sqlite3.dll -o shell\\tcc\\lib\\sqlite3.def")

    if not os.path.isfile("shell\\tcc\\glfw3.dll"):
        print("Deploying GLFW...")
        cmd("cmd /c copy temp\\glfw-bin\\lib-mingw-w64\\glfw3.dll shell\\tcc")
        cmd("xcopy temp\\glfw-bin\\include shell\\tcc\\include /E")
        cmd("shell\\tcc\\tcc.exe -impdef shell\\tcc\\glfw3.dll -o shell\\tcc\\lib\\glfw3.def")

    if not os.path.isfile("shell\\tcc\\freeglut.dll"):
        print("Deploying FreeGLUT...")
        cmd("cmd /c copy temp\\glut-bin\\bin\\x64\\freeglut.dll shell\\tcc")
        cmd("xcopy temp\\glut-bin\\include shell\\tcc\\include /E")
        cmd("shell\\tcc\\tcc.exe -impdef shell\\tcc\\freeglut.dll -o shell\\tcc\\lib\\freeglut.def")

    if not os.path.isfile("shell\\tcc\\libcurl.dll"):
        print("Deploying cURL...")
        cmd("cmd /c copy temp\\curl-bin\\bin\\libcurl-x64.dll shell\\tcc\\libcurl.dll")
        cmd("xcopy temp\\curl-bin\\include shell\\tcc\\include /E")
        cmd("shell\\tcc\\tcc.exe -impdef shell\\tcc\\libcurl.dll -o shell\\tcc\\lib\\libcurl.def")

    for prog in ("python", "mingit", "love2d", "npp"):
        print(f"Deploying {prog}...")
        copy(f"temp\\{prog}", f"shell\\{prog}")

    if args.clean:
        print("Deploying system headers...")
        copy("temp\\win-api\\include\\winapi\\windows.h", "temp\\win-api\\include\\winapi\\windows.h.bak")
        copy("temp\\win-api\\include", "shell\\tcc\\include")

    if not os.path.isfile("shell\\tcc\\m.dll"):
        print("Compiling extra math library...")
        cmd("shell\\tcc\\tcc.exe scripts\\math.c -shared -o shell\\tcc\\m.dll")
        cmd("cmd /c move shell\\tcc\\m.def shell\\tcc\\lib")

    print("Refreshing libraries...")
    for lib in ("kernel32", "user32", "ws2_32", "opengl32"):
        location = cmd(f"where {lib}.dll")
        cmd(f"shell\\tcc\\tcc.exe -impdef {location} -o shell\\tcc\\lib\\{lib}.def")

    print("\nUse 'cmd /k cmdrc.bat' in the 'shell' folder")


if __name__ == '__main__':
    main()
