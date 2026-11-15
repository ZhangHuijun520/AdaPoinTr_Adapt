from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/launch_once_v2.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9Vltvo0YUfudX0HS7LxVhuA3DSmyFMY6t2MY1zm5XqjSaGzYbDOwAadxf33HsJLa6qlaq4jfPzOE732V84OefTFpUJiXtRmtFpxui1/otae914Psa47q5qbfC/Fo/7EhlEk6auqg6if+q5b25UL9XUtve80LqRvMDtWZZr1uTSVIVpMSUtQ3O+7Lcki0lR5z/B2Jm8e94OcKZFDnO65LHuBWCA9xJUlTYBja0LMvFD7YmHptadnp8N4zwp0k2GUwTPEw+TeIkC28WdwYnlDEU+AZhMDBETpjhug4yCLQQ5IIEhJBXkME0yvDndHmbLaI4wXE6H01uwg8uCOAH9FyWzhZ4fjfDq/EyiYZZ+EJidjv9/kG6SOZP0N89XXxZjdP5MJ2vPi8nq2TwZZXE6TAJrRfcxXQQxbfJfBhG6/XJ7oHfcLIML+W3uW1KVld5sT5zPo7isfJ9kkXK/1fiq9niouS6bXNu6jjKxlmSDEPwvD8e4fHdAKej0XQyP6W6jObZKF3OkmX279P9U+ksuZySTY4ZYRvxTOCP4c3R5MvyOCOxUtcznb+EfclgZdHV1dGS/YT7VWhm38qnsdcVW1H3auoZbbGuSBmukuVMre6LsjRI3gkZeq2OoAtAq5t105nqBnNiiuqhfWVtHDjtAZtdt6kr59oCujHRjUw3Bj8y0LpNITluiOx25pPSln3DMj/oiw+qimp9Juy/6oRqsFNF181OqZHiWy/a7q2InGZxyuFRsL4rlPfH/ns+X9u6emVktBtie1CnDvIJQJTbXHi+59sORzkKCMwB83NqQeh5AbAA2mcscmgzALiNKHICl7u5pRBJr4yXxd9k3/GtlKrwO1mX5lmzE1ln+8/iAgq8gHIrsImghHAqiA1zBj2XQtsByKYcuVy9TGDgQcCQQ13GHNcnDmFKubu3q6/2N/WtZR3bnOZ02HnJibvQVoGAnAU+cRnkLnAgDWjuCGKp1FwPcRBQBKln2cxDaulbiFCeQ+B4rv7xYn/7kvQV21wrMN3++N7SJAvf/Xb8wtEaqbrm+tUv7Z/VlX71TrKrC1ITj0WHWc3FdffYafvVgYL2D0yVS6U='))
assert hashlib.sha256(b).hexdigest() == 'e4380ba6346d6637cf568134f0b9f88fcb3e0c4ce0086ab9758d14015dac75cc'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'e4380ba6346d6637cf568134f0b9f88fcb3e0c4ce0086ab9758d14015dac75cc'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))