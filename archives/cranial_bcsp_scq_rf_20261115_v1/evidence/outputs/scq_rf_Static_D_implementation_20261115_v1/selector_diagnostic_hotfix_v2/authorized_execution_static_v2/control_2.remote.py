from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/control/launch_once_v2.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9lm1vo0YQx9/zKWh6vTcVYXmGk7gKGxxbsY1rnLueVGk17C42FwzcsqRxP33XsZ3E6qk6qYrfwcww8/vPjEb8/JOel7WeQ7dROiZUjfVKv4XuXkWepxCq6ptmy/SvzcMOah0otE1ZC47/avi9vpDPK65s72nJVa39gVi9atadTjjUJVQ4J12Li76qtrDN4Zjn/yXRs+HveDnCmQBRElw0FY1xxxhFWHAoa2wi0zUMw8EPpsIe24YLdXgXR/jTJJsMpgmOk0+TYZKFN4s7zfItahg+aJbrEy2wmaUZrgsaAWqxAnK/oN5LksE0yvDndHmbLaJhgofpfDS5CT/YKHA/+KewdLbA87sZXo2XSRRn4TPE7Hb6fUe6SOZPqb/rXXxZjdN5nM5Xn5eTVTL4skqGaZyExnPexXQQDW+TeRxG6/Ur64EvnizDy3Vc37YVaeqiXJ/1fhgNx7LzkyySE3hBX80WF8YT2/a8seMoG2dJEofoZB+P8PhugNPRaDqZv4ZdRvNslC5nyTL7t3f/VTpLLqllU2ACZMNOCH/EN8dGX5rkDGMl1zSdP4/8suPlpWjqY1v21+5Xpuh9x59OoCi3rOnlBdS6cl1DFa6S5Uy+3ZdVpUEhGA+dTvVdG6FO1ZtW6HKTKeisfuheuLUD1T5huxObprauDaRqE1XLVG3wI8dNbEpOcQtc7PQnrR35hnlxUhgfdJX1+kzaf0cyWWQnw67bnVTE2beedeLtYM5n8prjkZFelHIGR4Y909euqV+otG4DpuOqAfWA2E7AAgjcgFguLVyPUmDMJg5BAEBM4vq5ZZqUFI6PAo84duEEBMBGZi4zQi8HwMu/YV/x7dTKNRC8qfSzcq+EndlP8lzmezZQj/kmym3ThjxHgeFaJs2luDz3LHA9BwAR5OcF85yisFFBEaM2tVDg7BvW1/udfXthx0KvZ3WwnMQYLHAsZjqWb7qImUFumHZODDlAMCzHBt+m1HXzAkl10ueznDIX2YaU4rIc+erHCx6BCvqabK5lOtX8+N5QOAnf/Xb891FaLusW6tUv3Z/1lXr1jpOri8Kxx1Jg0lB2LR6Fsn87QCj/ABT1WCU='))
assert hashlib.sha256(b).hexdigest() == '9a720d99cd568f3122370858ce85533c72e281118a0a154f78227e0715f5155e'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '9a720d99cd568f3122370858ce85533c72e281118a0a154f78227e0715f5155e'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))