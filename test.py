import os
import subprocess
import sys

import numpy as np
from setuptools import find_packages, setup
from setuptools.command.build_ext import build_ext

# from Cython.Build import cythonize

is_posix = (os.name == "posix")

if is_posix:
    os_name = subprocess.check_output("uname").decode("utf8")
    if "Darwin" in os_name:
        os.environ["CFLAGS"] = "-stdlib=libc++ -std=c++11"
    else:
        os.environ["CFLAGS"] = "-std=c++11"

if os.environ.get('WITHOUT_CYTHON_OPTIMIZATIONS'):
    os.environ["CFLAGS"] += " -O0"


# Avoid a gcc warning below:
# cc1plus: warning: command line option ???-Wstrict-prototypes??? is valid
# for C/ObjC but not for C++
class BuildExt(build_ext):
    def build_extensions(self):
        if os.name != "nt" and '-Wstrict-prototypes' in self.compiler.compiler_so:
            self.compiler.compiler_so.remove('-Wstrict-prototypes')
        super().build_extensions()


def main():
    cpu_count = os.cpu_count() or 8
    version = "20220531"
    packages = find_packages(include=["hummingbot", "hummingbot.*"])
    package_data = {
        "hummingbot": [
            "core/cpp/*",
            "VERSION",
            "templates/*TEMPLATE.yml"
        ],
    }
    print(packages)


if __name__ == "__main__":
    main()
