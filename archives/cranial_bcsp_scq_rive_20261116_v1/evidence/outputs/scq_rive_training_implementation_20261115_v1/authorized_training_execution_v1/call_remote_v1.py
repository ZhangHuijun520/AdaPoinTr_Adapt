"""This authorized run's byte-capturing operational calls; no automatic retry."""
import ast
import base64
import hashlib
import json
import subprocess
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent


def call(name, code, seconds=30):
    raw = code.encode('utf-8')
    compile(ast.parse(raw), name, 'exec')
    prefix = ('/usr/bin/timeout ' + str(seconds)
              + "s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B - <<'PY'\n")
    plain = prefix + code + '\nPY'
    wire = base64.b64encode(zlib.compress(raw, 9)).decode('ascii')
    packed = prefix + "import zlib,base64\nexec(zlib.decompress(base64.b64decode('" + wire + "')))\nPY"
    command = min((plain, packed), key=lambda text: len(text.encode('utf-8')))
    assert len(command.encode('utf-8')) <= 2048, (name, len(command.encode('utf-8')))
    with (HERE / (name + '.remote.py')).open('xb') as stream:
        stream.write(raw)
    with (HERE / (name + '.command.json')).open('x', encoding='utf-8') as stream:
        json.dump(dict(command=command,bytes=len(command.encode()),
                       source_sha256=hashlib.sha256(raw).hexdigest(),automatic_retry=False),stream,indent=2)
    local_timeout = False
    try:
        result = subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec',
                                 '/home/zhj/.local/bin/hpc5000','exec','--timeout',
                                 str(seconds+10),'--',command],
                                capture_output=True,timeout=seconds+20)
        rc, stdout, stderr = result.returncode,result.stdout,result.stderr
    except subprocess.TimeoutExpired as error:
        rc,local_timeout = 124,True
        stdout,stderr = error.stdout or b'',error.stderr or b''
    (HERE/(name+'_stdout.bin')).write_bytes(stdout)
    (HERE/(name+'_stderr.bin')).write_bytes(stderr)
    rows=[json.loads(line) for line in stdout.decode('utf-8',errors='replace').splitlines()
          if line.startswith('{')]
    with (HERE/(name+'.result.json')).open('x',encoding='utf-8') as stream:
        json.dump(dict(returncode=rc,local_timeout=local_timeout,rows=rows,
                       stdout_bytes=len(stdout),stderr_bytes=len(stderr)),stream,indent=2)
    print(json.dumps(dict(stage=name,returncode=rc,local_timeout=local_timeout,rows=rows),ensure_ascii=True))
    if rc or local_timeout:
        raise RuntimeError('FAILED_STOP_NO_RETRY: '+name)
    return rows
