import gzip,hashlib,importlib.util,io,json,os,sys
from pathlib import Path
os.environ.update(OMP_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",MKL_NUM_THREADS="2")
import numpy as np
import skimage
d=Path("outputs/bcsp_oasg_20261124_v1").resolve()
out=d/"skullfix_cpu_scoring_v1"
g=d/"candidate_freeze_external_v1/OASG_SF_90case_local_geometry_verification_v1.json"
def sha(b):return hashlib.sha256(b).hexdigest()
def rec(p,b):return dict(path=str(p),bytes=len(b),sha256=sha(b))
def pin(r):
 p=Path(r["path"]);b=p.read_bytes()
 assert p.resolve()==p and rec(p,b)==r,p
 return b
def put(p,data):
 with p.open("xb") as f:f.write(data)
 assert p.read_bytes()==data
 return rec(p,data)
def js(x):return (json.dumps(x,indent=2,allow_nan=False)+"\n").encode()
v=g.read_bytes();assert sha(v)=="7231b73ac880e7fa82934dfa60d4eacc25b6398ddea2832316e6df8f63a17fac"
z=json.loads(v)
def loadmod(key):
 a=z["evidence"][key];pin(a)
 s=importlib.util.spec_from_file_location(key,a["path"]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
u=loadmod("reader");m=loadmod("metric")
orig=json.loads(pin(z["evidence"]["skullfix_manifest"]).splitlines()[0])
manifest={r["case_id"]:r for r in map(json.loads,pin(z["evidence"]["skullfix_manifest"]).splitlines())}
assert len(z["cases"])==len(manifest)==90
out.mkdir();(out/"references").mkdir()
rows=[]
def read_mask(binding,c):
 p=Path(binding["path"]);b=p.read_bytes()
 assert p.resolve()==p and sha(b)==binding["sha256"],p
 _,off,dt,sh,A,origin=u.header(p)
 assert list(sh)==c["shape"] and A.tolist()==c["affine"] and origin.tolist()==c["origin"]
 n=int(np.prod(sh))*dt.itemsize
 with gzip.GzipFile(fileobj=io.BytesIO(b[off:])) as f:raw=f.read(n+1)
 assert len(raw)==n
 return np.frombuffer(raw,dt).reshape(sh,order="F")>0
for k,c in enumerate(z["cases"],1):
 cid=c["case_id"];G=read_mask(c["raw"]["implant"],c)
 axes=[np.flatnonzero(G.any(axis=tuple(i for i in range(3) if i!=j))) for j in range(3)]
 lo=np.array([v[0]-1 for v in axes]);hi=np.array([v[-1]+2 for v in axes])
 assert np.min(lo)>=0 and np.all(hi<=np.array(G.shape)),cid
 sl=tuple(slice(a,b) for a,b in zip(lo,hi))
 D=read_mask(c["raw"]["defective"],c)
 A=np.array(c["affine"]);origin=np.array(c["origin"])
 r=m.surface_references(G[sl],D[sl],A,lo@A+origin)
 jj=r["a_is_j"];w=r["a_weights"]
 assert int(jj.sum())==c["J_faces"] and int((~jj).sum())==c["E_faces"]
 assert float(w[jj].sum())==c["J_area_mm2"] and float(w[~jj].sum())==c["E_area_mm2"]
 a2,w2,j2=m.a2_reference(r)
 assert len(a2)==c["A2_points"] and np.isfinite(a2).all()
 assert np.array_equal(w2.reshape(-1,4).sum(1),w) and np.array_equal(j2,np.repeat(jj,4))
 packed=io.BytesIO()
 np.savez_compressed(packed,**{k:r[k] for k in ("a_centers","a_weights","a_is_j","a_axes","affine","origin")})
 b=packed.getvalue();p=out/"references"/(cid+"_A1.npz")
 ref=put(p,b)
 with np.load(p,allow_pickle=False) as bank:
  assert set(bank.files)=={"a_centers","a_weights","a_is_j","a_axes","affine","origin"}
  assert all(np.array_equal(bank[f],r[f]) for f in bank.files)
 a=manifest[cid];assert c["point_record"]["sha256"]==a["sha256"] and c["normalization"]==a["normalization"]
 pin(c["point_record"])
 rows.append(dict(case_id=cid,source_id=c["source_id"],split=c["split"],normalization=a["normalization"],
    normalization_source="defective_bbox",reference=ref,point_file=c["point_record"],target_array_sha256=a["target_array_sha256"]))
 del G,D,r,a2,w2,j2
 if k%15==0:print("REFERENCES",k,flush=True)
idx=put(out/"OASG_SF_score_case_index_v1.json",js(dict(schema="oasg-sf-score-case-index-v1",dataset="SkullFix",cases=rows)))
ids=np.random.Generator(np.random.PCG64(2026112401)).integers(0,90,size=(2000,90),dtype=np.int64)
tmp=io.BytesIO();np.save(tmp,ids,allow_pickle=False)
boot=put(out/"OASG_SF_source_bootstrap_indices_v1.npy",tmp.getvalue())
out1=dict(index=idx,bootstrap=boot,source_ids=[r["source_id"] for r in rows],metric=z["evidence"]["metric"],reader=z["evidence"]["reader"],
         geometry=rec(g,v),versions=dict(python=sys.version.split()[0],numpy=np.__version__,skimage=skimage.__version__),reference_files=90)
print(json.dumps(out1),flush=True)
