import subprocess
import sys
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
venv_py = root / '.venv' / 'Scripts' / 'python.exe'
python_exec = str(venv_py) if venv_py.exists() else sys.executable

def main():
    code = subprocess.call([python_exec, '-m', 'pytest', '-q', 'backend/tests'])
    sys.exit(code)

if __name__ == '__main__':
    main()
