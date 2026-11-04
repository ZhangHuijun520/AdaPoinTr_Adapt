"""Local-only single training-start wrapper; no installed client edits or server staging files."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import sys
import time

CLIENT = Path('/home/zhj/.local/share/remote-agent-toolkit/release/hpc5000.py')
CLIENT_SHA = '994e2dac717b32f388e007150866ca6b08ecf9b73010007d2470f32e886b7e40'
PAYLOAD_SHA = '6881baa9217f0e5f79bdeda409fe211c0ce40ab864ba99a21c3897f6a866571e'
MAX_LINE = 2048
CHUNK = 1024


def main():
    data = json.loads(sys.stdin.buffer.read())
    raw = base64.b64decode(data['payload_base64'], validate=True)
    assert hashlib.sha256(raw).hexdigest() == PAYLOAD_SHA, 'unchanged installer payload'
    client_raw = CLIENT.read_bytes()
    assert hashlib.sha256(client_raw).hexdigest() == CLIENT_SHA, 'client source drift'
    sys.path.insert(0, '/home/zhj/.local/share/remote-agent-toolkit/site-packages')
    spec = importlib.util.spec_from_file_location('bcsp_training_launch_existing_client', CLIENT)
    hpc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = hpc
    spec.loader.exec_module(hpc)
    original_build, original_send = hpc.build_remote_command, hpc.send_stdin
    command = ("/usr/bin/timeout --signal=TERM --kill-after=2s 120s "
               "/opt/conda/bin/python3.8 -I -S -B <<'BCSP_TRAIN_START_V2'\n"
               + raw.decode('utf-8') + "\nBCSP_TRAIN_START_V2\n")
    plan = {}

    def short_build(text, command_id):
        outer, begin, end = original_build(text, command_id)
        words = shlex.split(outer)
        assert len(words) == 8 and words[:2] == ['printf', '%s']
        assert words[3:] == ['|', 'base64', '-d', '|', 'bash']
        encoded = words[2]
        assert re.fullmatch(r'[A-Za-z0-9+/]*={0,2}', encoded)
        wrapper = base64.b64decode(encoded, validate=True)
        wrapper_sha = hashlib.sha256(wrapper).hexdigest()
        parts = [encoded[i:i + CHUNK] for i in range(0, len(encoded), CHUNK)]
        lines = ["BCSP_TRAIN_START_B64=''"]
        lines += ['BCSP_TRAIN_START_B64="$BCSP_TRAIN_START_B64"' + shlex.quote(x) for x in parts]
        guard = ('[ "$(printf \'%s\' "$BCSP_TRAIN_START_B64" | base64 -d | sha256sum | cut -d \' \' -f 1)" = '
                 + shlex.quote(wrapper_sha) + ' ]')
        lines.append("if " + guard + "; then printf '%s' \"$BCSP_TRAIN_START_B64\" | base64 -d | bash; fi; unset BCSP_TRAIN_START_B64")
        assert max(len(x.encode()) for x in lines) <= MAX_LINE
        assert ''.join(parts) == encoded and hashlib.sha256(base64.b64decode(''.join(parts))).hexdigest() == wrapper_sha
        plan.update(original_outer_bytes=len(outer.encode()), transmitted_lines=len(lines),
                    maximum_line_bytes=max(len(x.encode()) for x in lines), chunk_bytes=CHUNK,
                    decoded_wrapper_sha256=wrapper_sha, installer_payload_sha256=PAYLOAD_SHA)
        return '\n'.join(lines), begin, end

    def short_send(ws, text):
        if text.startswith("BCSP_TRAIN_START_B64=''\n"):
            for line in text.splitlines():
                assert len(line.encode()) <= MAX_LINE
                original_send(ws, line + '\r')
                time.sleep(0.01)
        else:
            original_send(ws, text)

    hpc.build_remote_command, hpc.send_stdin = short_build, short_send
    wire, begin, end = short_build(command, 'bcsp_train_offline_format_inspection')
    assert begin not in wire and end not in wire, 'completion markers hidden from terminal echo'
    if data['mode'] == 'inspect':
        print(json.dumps(dict(status='LOCAL_SHORT_WIRE_STATIC_INSPECTION_PASS', client_sha256=CLIENT_SHA,
                              remote_payload_executed=False, **plan)))
        return 0
    assert data['mode'] == 'execute_once'
    print(json.dumps(dict(status='LOCAL_SHORT_WIRE_READY', **plan)), flush=True)
    return hpc.main(['exec', '--timeout', '135', '--', command])


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print('Local training invocation stopped: ' + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
