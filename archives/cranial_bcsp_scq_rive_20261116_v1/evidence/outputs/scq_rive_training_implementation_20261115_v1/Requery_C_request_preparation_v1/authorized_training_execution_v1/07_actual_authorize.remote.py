import pathlib,hashlib,json,importlib.util,socket,os
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
root=P("/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1")
p=root/"bcsp_rive_training_entry_v1.py";assert hashlib.sha256(p.read_bytes()).hexdigest()=="2b864497f28d1940af10bcb9d5b099e9846dfd0faf284785bd4e7b8b7980de15"
s=importlib.util.spec_from_file_location("rive_installed_contract_only",p);e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
run="SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1";control=root/"control"/run
def rec(p,h):return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
result=e.authorize(rec(root/(run+"_execution_request_v1.json"),"45d37fc024dd4e97a82cd08c93ad25cebfcbd4a4f74ae8b2be9d22e4536392de"),rec(control/"authorization_v1.json","629cf796979a5d20cd49d02dd4523c498de95097ea70d66b8c1bc55234c16842"),rec(control/"runtime_v1.json","6c736b2af39c12e1a83fa37a0512c18ef1b43235394fce3228ed2fb0a721379c"))
assert result[0]["arm"]=="RF-Requery" and result[0]["fold"]=="C" and len(result[3])==315 and result[1]["counts"]["updates"]==3900
print(json.dumps(dict(status="INSTALLED_ACTUAL_AUTHORIZE_PASS",cases=len(result[3]),updates=3900,effective_wall=result[0]["resources"]["wall_seconds"],legacy_wall=result[1]["resources"]["wall_seconds"],model_calls=0)))
