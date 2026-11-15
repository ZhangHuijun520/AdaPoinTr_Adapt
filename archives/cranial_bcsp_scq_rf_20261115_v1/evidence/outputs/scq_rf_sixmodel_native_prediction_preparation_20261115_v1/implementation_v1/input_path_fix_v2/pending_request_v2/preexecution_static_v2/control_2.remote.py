from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_launch_once_v2.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNrFlluP2kYUx9/9KSbbtC+R19fxJZJTGTALWsAUs0mjJBqN5wLO+hZfKBvlw3dgYYFkq7aJlrzZcy7z+58zmjO/PFPiJFdiXC+lmjVAZq3UZri+BaptS4QCZVlkTPlYrO5wrmCKyyLJmwr9VVS3ylR8zyvpHXgG5NG9J/gAvnwBbJ00QNO1E9Muyb97fLXN/w7YcX1vnJIWi/qHghVS4TzBKYpJXSLepmmGsxg/RU4l6v6BZn1UJ+usoCxFOW6SFUOUrVhalBnLG6SruqVpGkQr/SuE7JYmFZBLIMs/yLFPJZ9Xj8TWZVE1oHvT89HrYTTsjALUC14Pu0HkXU1vZMMxqKY5WDYsh8iuyQxZsywsE0wNxnHscGofknRGfoTehLPraOp3A9QNJ/3hlffSVF3rpbN3C8dTNLkZo/lgFvi9yHuAGF+PHjeE02CyTf2odfp2PggnvXAyfzMbzoPO23nQDXuBpz3knY46fvc6mPQ8f7E4Wr3n6w1n3lmLrmRlSoqcJ4uT8nf97kAUfxj5ogkH+vl4en7CJitPyzvwo0EUBD1P3a8P+mhw00Fhvz8aTo55Z/4k6oezcTCLvrVuosJxcGY5S44IJku2p/izd7Ur90+AOSGZiyMbTh56f/Y+V0lT5LvibObXCyYpbV1th1qTZKxoxUyT62SR49SbB7Ox+LtN0lTGvGGVB2tg66paA6UoG0UcaooVlq/qA7l8z7XJV941yyI3LjUVyEMgR0Du/JfbrlkmFUUlrpo7Zau2Jp9QxQ8ay4rRhDSJEHKs7VHfXT12IcLtsrwTkir2qWV185Q4/9CZI2+2ZqTdfu1wNngf6yI/AMr1EuvQApBSnWLMbMfQDHFDm9BSoYkNSycGdG3bxbqrGgYhrs5jjUBm25BjjcQm5IZLXZERt6IbVfIZb3Z8SuHiVDRVkSrfCj5BOBJ7sr6XzHUWO1A3oaHGFOuqS6lqwZhwDIUwg3LqUtNyNS1WLW6YJnZh7DiqqA9hGFtsU8Q235zpnyN2t/lxT+9X9gJtFRoO1LiKscYY5wYnQiJm0MFiCNMYc8ioBR3CqUGJ6VqYmlQMY5dz0XQ1Bq/Oe3ekuM3J8lJkBPqr3zSpIt7z33ePYKmsxNYcXPxav88vwMXzilycm2/zSkNEeF4260bavtm2HNLfK94Vxw=='))
assert hashlib.sha256(b).hexdigest() == 'a883611930516b5a70311781964fc818c3438ee92c515be0bf961f38817b8459'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'a883611930516b5a70311781964fc818c3438ee92c515be0bf961f38817b8459'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))