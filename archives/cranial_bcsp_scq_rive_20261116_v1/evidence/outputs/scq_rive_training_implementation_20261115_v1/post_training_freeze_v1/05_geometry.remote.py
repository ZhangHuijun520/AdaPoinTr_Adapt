import pathlib,json,math,itertools,socket
assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0"
out=pathlib.Path("/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1")
def finite(v):
 if isinstance(v,dict):return all(finite(x) for x in v.values())
 if isinstance(v,list):return all(finite(x) for x in v)
 return not isinstance(v,(float,int)) or math.isfinite(v)
def close(a,b):return math.isclose(a,b,rel_tol=1e-5,abs_tol=1e-6)
n=0;nonzero=0;maxdelta=0.;sumrf=0.
with (out/"SCQ_geometry.jsonl").open() as a,(out/"metrics.jsonl").open() as b:
 for ga,mb in itertools.zip_longest(a,b):
  assert ga is not None and mb is not None;g=json.loads(ga);m=json.loads(mb);n+=1
  assert all(g[k]==m[k] for k in ("step","epoch","batch","case_ids")) and g["step"]==n and g["frame"]=="D-only normalized"
  v=g["geometry"];assert set(v)=={"coarse","dense","Q0","Q1","Q2","delta","delta0","delta1","N0_N1_equal","neighbor_set_overlap"} and finite(v)
  assert v["N0_N1_equal"] is True and v["neighbor_set_overlap"]==[1.]*8
  for key in ("coarse","dense","Q0","Q1","Q2","delta","delta0","delta1"):
   assert len(v[key]["centroid"])==8 and all(len(x)==3 for x in v[key]["centroid"])
  for i in range(8):
   for j in range(3):
    assert close(v["Q0"]["centroid"][i][j]+v["delta0"]["centroid"][i][j],v["Q1"]["centroid"][i][j])
    assert close(v["Q1"]["centroid"][i][j]+v["delta1"]["centroid"][i][j],v["Q2"]["centroid"][i][j])
    assert close(v["Q2"]["centroid"][i][j],v["coarse"]["centroid"][i][j])
   assert close(v["Q2"]["radius"][i],v["coarse"]["radius"][i])
  if n==1:assert v["delta0"]["max_norm"]==v["delta1"]["max_norm"]==[0.]*8
  c=g["loss_components"];assert set(c)=={"coarse_CD","dense_CD"} and finite(c)
  assert g["reconstruction_sum"]==c["coarse_CD"]+c["dense_CD"] and close(g["reconstruction_sum"],m["loss_reconstruction"])
  maxdelta=max(maxdelta,max(v["delta"]["max_norm"]));nonzero+=int(max(v["delta1"]["max_norm"])>0);sumrf+=sum(v["delta1"]["mean_norm"])/8
assert n==3900
print(json.dumps(dict(status="ALL3900_RF_GEOMETRY_AND_LOSS_PASS",records=n,Static_N0_N1_equal_records=n,RF_nonzero_steps=nonzero,max_query_delta_norm=maxdelta,RF_second_residual_mean=sumrf/n,units="D-only normalized; descriptive only")))
