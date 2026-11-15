from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/control/launch_once_v3.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9Vl2PmzgUfedXsLPdvlQMmA9jV6IrQsgkmiRkQ6bdSitZxtgJHQLUwOzM/vo6k6STaKtVpdWEF/C95txzzjVX/PqLmRWVmdF2o7W80w3ea/2Wtve65fsay3VzU2+5+aV+eKKVSXPa1EXVSfJ3Le/NhXpeSW17nxdSN5qf2GuW9bo1maRVQUuSsbYhoi/LLd1m9IDz/0DMNPqDLEcklVwQUZd5RFrOc4t0khYVsS0bAgBc8uBo/LGpZadHd8OQfJykk8E0JsP44ySK0+BmcWfkNGMMYd+gDGKDC8oM13WQQSFAMOcUU0pfQAbTMCWfkuVtugijmETJfDS5Cd67Fobv0XFbMluQ+d2MrMbLOBymgX1MzG6nP04ki3j+DP3D7OLzapzMh8l89Wk5WcWDz6s4SoZxAL7jLqaDMLqN58MgXK9Pont+w8kyuJTf5rYpWV2JYn3mfBRGY+X7JA2V/y/EV7PFRcl12+bc1HGYjtM4HgbWMT4ekfHdgCSj0XQyP6W6DOfpKFnO4mX67+zurWQWX07JRhBG2YYfCfw5vDmYfFkeZyRW6ngm8+/NvmRjZdHV1cGS3YR7xzWzb+Xz2OuKLa97NfWMtlhXtAxW8XKmVvdFWRpUdFwGXqsj6FpWq5t105nqBOfU5NVD+8La2HPaATZP3aaunGtg6cZEN1LdGPzMQOs2hcxJQ2X3ZD4rbdlXIsVeX7RXVVTrM2H/tY+rAk9q03XzpNRI/rXnbfdaRE57ccrhkbO+K5T3h/o7Pl/aunphZLQbantQh45vUYyQj7CTecBi2EOeBQHkGYQuwAgjGzggF9DPPY6pBSn3bU/gDEGLIqQQaa+Ml8U/dFfxtZSq5neyLs2zYieyzuJHcVkuXORatk+pr9S41BEcCJ8hiDDPIcNWbtucAxspeRZCduaoC3ooB5xxnO/s6qvdSX1tWYcyp33aR45SMMYAq94gx7Et7ADoiCwDyHZ85Coswai6O54thPB9mFk2zbIMc+BCQUUmPP3DxT77kvYV21wrMN3+8BZokgVvfj/84WiNVFWFfvVb+1d1pV+9kezqgtT4Y9ERVuf8unvstN1qT0H7BiC1SRA='))
assert hashlib.sha256(b).hexdigest() == 'c86583650c2dbcc82ff07951824a4f799c08d41d4dc6dc02ebc197b77e811a15'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'c86583650c2dbcc82ff07951824a4f799c08d41d4dc6dc02ebc197b77e811a15'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))