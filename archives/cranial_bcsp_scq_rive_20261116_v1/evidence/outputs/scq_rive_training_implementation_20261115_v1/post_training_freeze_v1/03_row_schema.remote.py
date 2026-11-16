import pathlib,json,socket
assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0"
p=pathlib.Path("/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1")
with (p/"SCQ_geometry.jsonl").open() as f:a=json.loads(next(f))
with (p/"resources.jsonl").open() as f:b=json.loads(next(f))
print(json.dumps(dict(status="ROW_SCHEMA_OBSERVED",geometry_keys=list(a),geometry_fields=list(a["geometry"]),loss_components=a["loss_components"],reconstruction_sum=a["reconstruction_sum"],resource_first=b)))
