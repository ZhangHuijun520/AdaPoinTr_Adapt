from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9lm1vm0gQx9/zKbi0d29OBFhggUr0hA2OrdjGB04fpJNWyz7YNBjoArm4n77r2E7su0qtVNXv2J3Zmd9/ZjTi1W96XlR6jtu10rJO1Viv9Bvc3quG6yqEqvq63jD9U/2wxZWOKW7qouoE+rcW9/pCfi+FsrmnhVC15gd89bJetToRuCpwiXLSNoj3ZbnBmxwf4vxcED0b/o3SEUrZ556JLeJ1SSPUMkYN1AlcVAgYAJqm6aAHU2GPTS06dXgXhejdJJsMpjGK4neTYZwFN4s7jeKcEM93NUygrzGOiWbblqdhaHqQMuxjjF+CDKZhht4n6W22CIcxGibz0eQmeGMbPnzjHd2S2QLN72ZoOU7jMMoCcDTMbqffNiSLeP4U+pvWxcflOJlHyXz5Pp0s48HHZTxMojh4FjdbTAfh8DaeR0G4Wp3c7vmiSRpcsOT6pilJXfFidVb8YTgcy9JPslC24IV9OVtcmq/bNOelHYfZOIvjKDCO9+MRGt8NUDIaTSfzU9o0nGejJJ3FafZ/6+5VMosvKmbNEcFkzY4MH6KbQ6kvjnLGsZSjmsyfu37hDouiq6tDYXY770+m6H0rnhZhV2xY3cs9qLXFqsJlsIzTmTzdF2WpYd4xETit6kHbMFpVr5tOl9NMsc6qh/YFXNtj7QI2225dV9a1aajaRNUyVRv8yIrr1oWgqMGi2+pPYlvyGQn+LDHaCyuq1Zm277gymWYr/a6brdQkdg5t9wtx/tOXU5JHRvqukH04UOyoPrV19cKltWsMHKja2PU5dKlLGPBz27Es26J+zigBrmebhmVQm0AALJa7OWcGoBbmJjWlh3zHqIyIe9kEUXzBu4y/UK+chU7UpX6W70TZ2f1Rn+cyh0ILMsgAdrzcIb5JqGN5Ls09QKQGDk2ArZx7NnVtk1mW4xhmTiBmkGO4q1hf7Qb3AsoOmU67tb85qjGALykdaDnQ46ZHPDe3ueMTwIELGPEM6JmebziUcAB9n+eOFOG4sm224wHgqW8vuQtK3FdkfS3jqeDtH6YiSPD6r8OPkNIImZirV7+3/1RX6tVrQa4uS8ceiw6RmrLr7rFTdqc9hfIVIqZeSg=='))
assert hashlib.sha256(b).hexdigest() == '19282bac7a8f1b2afe1414e878067c8894e1062cd46b47e702d86b4a7022e427'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '19282bac7a8f1b2afe1414e878067c8894e1062cd46b47e702d86b4a7022e427'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))