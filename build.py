#! python3

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
    if worker.wait() != 0:
        print(" ".join('"%s"' % p if " " in p else p for p in command))
        sys.exit(stdout.rstrip())
    return stdout.rstrip()


def copy(source, destination):
    destdir = destination[:-1] if destination[-1] == "\\" else os.path.dirname(destination)
    os.makedirs(destdir, exist_ok=True)
    if os.path.isdir(source):
        shutil.copytree(source, destination)
    elif os.path.isfile(source):
        destination = os.path.join(destdir, os.path.basename(source))
        shutil.copy2(source, destination)
    else:
        raise Exception(f"No such source: {source} -> {destination}")


def rmdir(dirname):
    if os.path.isdir(dirname):
        cmd(f"cmd /c rmdir /s /q {dirname}")


def main():
    os.chdir(os.path.dirname(__file__))
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
        print("  "+archiveName)
        if archiveName.lower().endswith(".zip"):
            zArchive = zipfile.ZipFile(f"archives\\{archiveName}")
            members = [m.filename for m in zArchive.infolist() if not m.is_dir()]
        elif archiveName.lower().endswith(".tar.gz") or archiveName.lower().endswith(".tar.bz2"):
            zArchive = tarfile.open(f"archives\\{archiveName}")
            members = [m.name for m in zArchive.getmembers() if m.isfile()]
        else:
            print("    Unknown archive type")
        parent = os.path.commonprefix(members)
        if "/" not in parent:
            parent = ""
        parent = parent.split("/")[0]+"/"
        for filename in members:
            if filename[0] in ("/", "\\") or ".." in filename:
                raise Exception(f"Dangerous filename: {filename}")
            destination = os.path.join("temp", dirname, filename.replace(parent, "", 1)).replace("/", os.sep)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            if archiveName.lower().endswith(".zip"):
                with open(destination, "wb") as f:
                    f.write(zArchive.read(filename))
            else:
                with open(destination, "wb") as f:
                    f.write(zArchive.extractfile(filename).read())

    copy("scripts\\cmdrc.bat", "shell\\cmdrc.bat")
    copy("temp\\tcc-bin", "shell\\tcc")

    print("Building make/busybox...")
    copy("temp\\tcc-bin", "temp\\busybox\\tcc")
    copy("scripts\\makebox.bat", "temp\\busybox\\makebox.bat")
    cmd("cmd /c call makebox.bat", cwd="temp\\busybox")
    copy("temp\\busybox\\make.exe", "shell\\tcc\\make.exe")
    copy("temp\\busybox\\sh.exe", "shell\\tcc\\sh.exe")

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
    cmd("shell\\tcc\\tcc.exe -llua -luser32 temp\\srlua\\srlua.c -o shell\\lua\\srlua.exe")
    cmd("shell\\tcc\\tcc.exe temp\\srlua\\glue.c -o shell\\lua\\glue.exe")
    cmd("shell\\lua\\glue.exe shell\\lua\\srlua.exe scripts\\lfreeze.lua shell\\lua\\lfreeze.exe")
    cmd("shell\\lua\\lfreeze.exe temp\\fennel-src\\fennel shell\\lua\\fennel.exe shell\\lua\\glue.exe shell\\lua\\srlua.exe")

    print("Deploying SQLite...")
    os.mkdir("shell\\sqlite")
    cmd("cmd /c copy temp\\sqlite-tools\\*.exe shell\\sqlite")
    cmd("cmd /c copy temp\\sqlite-src\\*.h shell\\tcc\\include")
    cmd("cmd /c copy temp\\sqlite-bin\\sqlite3.dll shell\\sqlite")
    cmd("shell\\tcc\\tcc.exe -impdef shell\\sqlite\\sqlite3.dll -o shell\\tcc\\lib\\sqlite3.def")

    print("Deploying GLFW...")
    cmd("cmd /c copy temp\\glfw-bin\\lib-mingw-w64\\glfw3.dll shell\\tcc")
    cmd("xcopy temp\\glfw-bin\\include shell\\tcc\\include /E")
    cmd("shell\\tcc\\tcc.exe -impdef shell\\tcc\\glfw3.dll -o shell\\tcc\\lib\\glfw3.def")

    print("Deploying FreeGLUT...")
    cmd("cmd /c copy temp\\glut-bin\\bin\\x64\\freeglut.dll shell\\tcc")
    cmd("xcopy temp\\glut-bin\\include shell\\tcc\\include /E")
    cmd("shell\\tcc\\tcc.exe -impdef shell\\tcc\\freeglut.dll -o shell\\tcc\\lib\\freeglut.def")

    print("Deploying cURL...")
    cmd("cmd /c copy temp\\curl-bin\\bin\\libcurl-x64.dll shell\\tcc\\libcurl.dll")
    cmd("xcopy temp\\curl-bin\\include shell\\tcc\\include /E")
    cmd("shell\\tcc\\tcc.exe -impdef shell\\tcc\\libcurl.dll -o shell\\tcc\\lib\\libcurl.def")

    print("Deploying system headers...")
    cmd("cmd /c rename temp\\win-api\\include\\winapi\\windows.h windows.h.bak")
    cmd("xcopy temp\\win-api\\include shell\\tcc\\include /E")

    print("Compiling extra math library...")
    cmd("shell\\tcc\\tcc.exe math.c -shared -o shell\\tcc\\m.dll")
    cmd("cmd /c move shell\\tcc\\m.def shell\\tcc\\lib")

    print("Refreshing libraries...")
    for lib in ("kernel32", "user32", "ws2_32", "opengl32"):
        location = cmd(f"where {lib}.dll")
        cmd(f"shell\\tcc\\tcc.exe -impdef {location} -o shell\\tcc\\lib\\{lib}.def")

    print("\nUse 'cmd /k cmdrc.bat' in the 'shell' folder")


if __name__ == '__main__':
    main()
