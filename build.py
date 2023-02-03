"""
"""

import os
import csv
import sys
import subprocess

MOD_PATH, _ = os.path.split(os.path.abspath(__file__))

def getBuildGraph():
    """
    """
    with open(MOD_PATH + "/graph.csv", 'r') as f:
        dr = csv.DictReader(f)
        rows = [row for row in dr]
    headers = ["from", "action", "to"]
    edges = []
    for row in rows:
        edge = []
        for h in headers:
            edge.append(row[h])
        edges.append(tuple(edge))
    return edges

def compile(emscriptenSystemPath, fromFile, toFile):
    """
    Captures three unique build modes:
    * MUSL compiles are matched against "libc/musl/" or "pthread/" and require unique build flags
    * LIBC (non-MUSL) compiles are matched against *.C (once MUSL is filtered out) and require unique build flags
    * LIBCXX (also filtered against MUSL) are matched against *.CPP and also require unique build flags
    """
    CLANG_FLAGS = "-triple wasm32-unknown-emscripten -emit-obj -fcolor-diagnostics"
    CLANG_FLAGS += " -isystem\"%s/lib/libcxx/include\"" % emscriptenSystemPath
    CLANG_FLAGS += " -isystem\"%s/include/compat\"" % emscriptenSystemPath
    CLANG_FLAGS += " -isystem\"%s/include\"" % emscriptenSystemPath
    CLANG_FLAGS += " -isystem\"%s/lib/libc/musl/include\"" % emscriptenSystemPath
    CLANG_FLAGS += " -isystem\"%s/lib/libc/musl/arch/emscripten\"" % emscriptenSystemPath
    CLANG_FLAGS += " -isystem\"%s/lib/libc/musl/arch/generic\"" % emscriptenSystemPath
    CLANG_FLAGS += " -fno-common"
    CLANG_FLAGS += " -mconstructor-aliases"
    CLANG_FLAGS += " -fvisibility hidden -fno-threadsafe-statics -fgnuc-version=4.2.1"
    CLANG_FLAGS += " -D__EMSCRIPTEN__ -D_LIBCPP_ABI_VERSION=2"
    C_FLAGS = "-x c -Os -std=gnu11 -fno-threadsafe-statics -fno-builtin"
    C_FLAGS += " -DNDEBUG -Dunix -D__unix -D__unix__ -D_XOPEN_SOURCE"
    C_FLAGS += " -Wno-dangling-else -Wno-ignored-attributes -Wno-bitwise-op-parentheses -Wno-logical-op-parentheses -Wno-shift-op-parentheses"
    C_FLAGS += " -Wno-string-plus-int -Wno-unknown-pragmas -Wno-ignored-pragmas -Wno-shift-count-overflow -Wno-return-type -Wno-macro-redefined"
    C_FLAGS += " -Wno-unused-result -Wno-pointer-sign -Wno-implicit-function-declaration -Wno-int-conversion"
    C_FLAGS += " -isystem\"%s/lib/libc/musl/src/internal\"" % emscriptenSystemPath
    MUSL_FLAGS = "-isystem\"%s/lib/libc/musl/src/include\"" % emscriptenSystemPath
    MUSL_FLAGS += " -I\"%s/lib/pthread\"" % emscriptenSystemPath
    CXX_FLAGS = "-x c++ -Os -std=c++11 -fno-threadsafe-statics -fno-rtti -I\"%s/lib/libcxxabi/include\"" % emscriptenSystemPath
    CXX_FLAGS += " -DNDEBUG -D_LIBCPP_BUILDING_LIBRARY -D_LIBCPP_DISABLE_VISIBILITY_ANNOTATIONS"
    objPath = MOD_PATH + "/obj"
    print("COMPILING %s => %s" % (fromFile, toFile))
    if not os.path.isdir(objPath):
        os.mkdir(objPath)
    if "libc/musl/" in fromFile or "pthread/" in fromFile:
        allArgs = ["clang", "-cc1"]
        allArgs += C_FLAGS.split(" ")
        allArgs += MUSL_FLAGS.split(" ")
        allArgs += CLANG_FLAGS.split(" ")
        allArgs += ["-o", toFile, '"%s/%s"' % (emscriptenSystemPath, fromFile)]
        subprocess.Popen(allArgs).communicate()
    elif fromFile.endswith(".c") and "pthread/" not in fromFile and "libc/musl/" not in fromFile:
        allArgs = ["clang", "-cc1"]
        allArgs += C_FLAGS.split(" ")
        allArgs += CLANG_FLAGS.split(" ")
        allArgs += ["-o", toFile, '"%s/%s"' % (emscriptenSystemPath, fromFile)]
        subprocess.Popen(allArgs).communicate()
    elif fromFile.endswith(".cpp") and "pthread/" not in fromFile and "libc/musl/" not in fromFile:
        allArgs = ["clang", "-cc1"]
        allArgs += CXX_FLAGS.split(" ")
        allArgs += CLANG_FLAGS.split(" ")
        allArgs += ["-o", toFile, '"%s/%s"' % (emscriptenSystemPath, fromFile)]
    else:
        raise Exception("File '%s' did not match any known build mode" % fromFile)

def main(emscriptenSystemPath):
    """
    """
    emscriptenSystemPath = emscriptenSystemPath.replace("\\", "/")
    bg = getBuildGraph()
    for edge in bg:
        if edge is not bg[1]:
            continue
        action = edge[1]
        if action == "IGNORE":
            pass
        elif action == "COMPILE":
            compile(emscriptenSystemPath, edge[0], edge[2])
        else:
            raise Exception("Unsupported action '%s'" % action)

if __name__ == "__main__":
    main(sys.argv[1])
