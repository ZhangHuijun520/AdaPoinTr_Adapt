"""One analytic synthetic fixture; never reads a dataset or checkpoint."""
import hashlib,json
from pathlib import Path
import numpy as np
S=Path(__file__).resolve().parent
i=np.arange(8192,dtype=np.float64);u=i/8192;theta=2*np.pi*u;z=2*u-1;rho=np.sqrt(1-z*z)
x=np.column_stack([.8*rho*np.cos(theta),.7*rho*np.sin(theta),.6*z]).astype('float32')
g=np.column_stack([.15+.20*np.cos(theta),.05+.18*np.sin(theta),.25+.04*np.sin(2*theta)]).astype('float32')
p=S/'artificial_h2_input_v1.npz'
with p.open('xb') as f:np.savez_compressed(f,partial=x,target=g)
record=dict(schema='H2-analytic-fixture-v1',label='ARTIFICIAL_ONLY_NO_PATIENT',partial='ellipsoid spiral with i=0..8191; u=i/8192; theta=2pi*u; z=2u-1; rho=sqrt(1-z^2); (.8rho cos(theta),.7rho sin(theta),.6z)',target='(.15+.20cos(theta), .05+.18sin(theta), .25+.04sin(2theta))',payload=dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()),arrays={k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.tobytes()).hexdigest()) for k,v in [('partial',x),('target',g)]},generation='float64 NumPy analytic coordinates cast once to FP32; package bytes frozen, no server regeneration',patient_data_used=False)
with (S/'artificial_fixture_definition_v1.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
print(json.dumps(record['payload']))
