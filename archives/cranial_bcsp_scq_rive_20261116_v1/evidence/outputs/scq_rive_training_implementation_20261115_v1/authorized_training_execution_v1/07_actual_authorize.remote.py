import pathlib,hashlib,json,importlib.util,socket,os
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
root=P("/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1")
p=root/"bcsp_rive_training_entry_v1.py";assert hashlib.sha256(p.read_bytes()).hexdigest()=="2b864497f28d1940af10bcb9d5b099e9846dfd0faf284785bd4e7b8b7980de15"
s=importlib.util.spec_from_file_location("rive_installed_contract_only",p);e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
run="SCQ_RIVE_Static_foldC_seed0_train_20261115_v1";control=root/"control"/run
def rec(p,h):return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
result=e.authorize(rec(root/(run+"_execution_request_v1.json"),"fdcb6cacef71bfae9395baf7b3bd05506b34b4053b75bfb03f54bff6bbe82bda"),rec(control/"authorization_v1.json","e00e2273fbdf052160071a7a1b4c69403c7970821c0624c9ab92c52808f8575d"),rec(control/"runtime_v1.json","d48506eb32d1476746de04e85d151df04f36c81dea8138ad2fafbbf085e26e6a"))
assert result[0]["arm"]=="RF-Static" and result[0]["fold"]=="C" and len(result[3])==315 and result[1]["counts"]["updates"]==3900
print(json.dumps(dict(status="INSTALLED_ACTUAL_AUTHORIZE_PASS",cases=len(result[3]),updates=3900,effective_wall=result[0]["resources"]["wall_seconds"],legacy_wall=result[1]["resources"]["wall_seconds"],model_calls=0)))
