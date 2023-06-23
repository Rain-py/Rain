import sys
import subprocess
def install(pkg,path):
    return subprocess.check_call([sys.executable, "-m", "pip", "install", pkg,"--target={}".format(path)])
pkgs = [
'numpy',
'tensorflow_cpu',
'tensorflow_intel'
]
base = 'worker/library/'
for i in pkgs:
    name = i
    path = base+'/'+name
    print(path)
    install(i, path)