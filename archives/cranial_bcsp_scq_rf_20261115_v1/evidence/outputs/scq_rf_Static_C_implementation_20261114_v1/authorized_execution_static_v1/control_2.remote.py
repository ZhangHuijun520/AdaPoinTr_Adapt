from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9VtuOm0gQfecr2Ek2LxHD/RaJrDDGY2ts8BpPLtJKraK7sclgIE0zGefr0x7bGVsbrSKtxi+IripOnVNVKvrVH2pe1moO3VrqKJcV2kv9Brp7WXNdCRNZXTcbqn5pHrZQq0CgbcqaM/StYffqXLwvmbS5JyWTlfY3YtWqWXUqZlCXUKEcdy0q+qrawCaHA87/A1Gz6G+0GKGMAy8xKpqKRKijlGiIMyhrZGiGo+u6hR50iT62DeNydDcM0YdJNhlMYzSMP0yiOAtu5ncKgRxjz3cVwI6v0AKwYlmmp4Cjew6h4APAM8hgGmboY7q4zeZhFKMoTUaTm+CdpfnOO+8Yls7mKLmboeV4EYfDLDCOjtnt9NeOdB4nT9C/9M4/L8dpMkyT5cfFZBkPPi/jKB3GwU9xs/l0EEa3cTIMwtXqxLrnN5wsgstVXN20FW7qolyd1T4Ko7Go/CQLRQeeqS9n8wvT45v2vLDjMBtncTwMtKN9PELjuwFKR6PpJDkluwiTbJQuZvEi+7d391U6iy+pZV0gDHhNjxQ+DW8Ohb40kzMaSzGmafKz5ZdtLyt5Ux/Kstt2b6mk9h17WoG83NCmFxtQ6cpVDVWwjBczcbovq0qBglMW2J3sOZamdbLatFwVk0xApfVD98xb2bPaAbZbvm5q81rXZGUiK5msDH5nufF1yQhqgfGt+qS1w18RK44Ko72usl6dSfvvSCqSbEXYdbsVihj92tOOvxyZ856c8nikuOel6MGBw47Tl66pn1kp3RoM25HBNFxbrF3qeoVvE9s3bS8HDzuGjh0T55pt5raV+67luNizPZM6biH6nhu5rtl6IRChFw1g5XfYZXw5tWIMOGsq9SzdibAz+1FeXoCmEd/Vc6L7tNC9XCsIMW0hxBI/F1dzPNfeaTRNS4QQUuTUND1qGcTS7MLaFayvdzP78sIOiU57tbccxfgmdn3QMdZyE5umRrFAyQ2b5uIS4fo22MTAWBdPcEwLwPeg8HW3sIlmOra4ZLy/4BKooK/x+lrAycb7N7rEcPD6r8PdR2qZyFvIV392/9RX8tVrhq8uSo4+lhzhhtBr/sil3WlPQvoBLFRWqg=='))
assert hashlib.sha256(b).hexdigest() == 'aafed3d7ce094f20c5d4bddc07072398e4b5303204f3d9dcc5e40ebc7a814160'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'aafed3d7ce094f20c5d4bddc07072398e4b5303204f3d9dcc5e40ebc7a814160'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))