from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/launch_once_v3.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9VmmT2jYY/u5foWzTfukY34cy43QMmIVZwBR7k2bajkaSJXDWV3xsdzv58ZVZyC6bdHok8IVBeqXnegXSdy8UkhYKwc1WalgLZNZJXY6bG6A6jkQToGzLnCnvy9t7XCg4wVWZFm2N/ijrG2Ulvse19Ct4AeT5w0rwO/j4EbC7tAWarh2V9iD/vOIZzX/esNf1f/cpWblpvmqzQmtcpDhDhDYV4l2W5Tgn+BSYSjT6Ga0nCNdtylPaL6BdgpGu6ramaSa6NZ7R5jdJWgO5+kriPc7J1UvsrirrFoyuxz56M4tmw3mAxsGb2SiIvMvVtZxgQqkLHRlTG8qMYyqbpuHK2NZcO2EYYowfQYZzP0Jvw/VVtPJHARqFy8ns0ntlqtB+5R6WhYsVWl4vUDxdB/448vRDYXE1/3IhXAXLHfQXq6t38TRcjsNl/HY9i4PhuzgYhePA0z7hruZDf3QVLMeev9k8mX3QN56tvZMHreRVRsuCp5ujyEf+aCoCn0W+CP5RcbxYnUdVm1fHMU79aBoFwdhTD/PTCZpeD1E4mcxny6ca1/4ymoTrRbCOPq/2u8JFcAYLW44oplt2YP5lfLmP9UwCjthjcQTD5ae+nqWHddqWxT6E/pb5kUlK19S7q6dNc1Z24uaRm3RT4MyLg/VCjG7SLJMxb1ntaWoDNFcVn0pZtYo4pQlWWHHbPMqVH8T0gNV9uy0LY6CpQJ4BOQLy8N/8TbXbtE5QJXzcKzuLDf2Aav7cjf55ESd52jSpcHirD6p7ob1mHzrWtN+Q1vi7nNkdo13bk+9JxdrB+6YsHmXIzRbrlg1cbCSq5hgcG5RRyBzDYYZrUog5hFwMILSpAxk3mK0SYokx0cyE6o7FddE8gYg7kW2d/ol7xm9qTzS1rctMOWJ44uVo/uCIO7qaYN3hTNwAGAqRwhOBbmJqqkU4EZos07Y4NTi1rcSlhs6gq3LiEA5VavUZdUV/Ak/iZY/9tCMPMwf9lstcZjpEsyhjzHAo0Q2qapBgYjgatpipug4kNjRExxwIXcuhJuacqEy3E9UAr0//481wV9DtQKAA/fUPmlRT7+VP+7eiVNWCjoOL75vfigtw8bKmF+fQ1D9mEC0TNmjvWmn3tNlxS38Be5+2IQ=='))
assert hashlib.sha256(b).hexdigest() == '78867d9a73448c0692e2535cf4ee685606b8b8246c75c97752528f72ba8cca29'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '78867d9a73448c0692e2535cf4ee685606b8b8246c75c97752528f72ba8cca29'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))