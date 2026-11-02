"""HTTP-Prüfung auf freiem Port; beendet ausschliesslich den eigenen Prozess."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
root = Path(__file__).resolve().parents[1]
env = dict(os.environ, PYTHONUTF8='1')
process = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'main.py',
                            '--server.port', str(port)], cwd=root, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for attempt in range(60):
        if process.poll() is not None:
            raise RuntimeError('Streamlit wurde vorzeitig beendet')
        try:
            with urlopen(f'http://127.0.0.1:{port}/_stcore/health', timeout=1) as response:
                assert response.read() == b'ok'
            print('Streamlit HTTP health: OK')
            break
        except OSError:
            time.sleep(0.5)
    else:
        raise TimeoutError('Streamlit nicht erreichbar')
finally:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
