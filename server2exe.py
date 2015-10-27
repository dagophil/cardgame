import sys
import os
import shutil
from distutils.core import setup
import py2exe

def build():
    # Erase previous destination dir.
    dist_dir = "dist_server"
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir)
    
    setup(
        console=[{
            "script": "server.py"
        }],
        options={
            "py2exe": {
                "optimize": 2,
                "bundle_files": 1,
                "compressed": True,
                "dist_dir": dist_dir
            }
        },
        zipfile=None
    )
    
    if os.path.isdir("build"):
        shutil.rmtree("build")
    
if __name__ == "__main__":
    if "py2exe" not in sys.argv:
        sys.argv.append("py2exe")
    build()
    raw_input("Press any key to continue")
