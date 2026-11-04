"""Freeze local research code/results, excluding arrays, weights and credentials."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
STEM = 'bcsp_representation_sampling_20261104_v2'
OUT = ROOT / 'deliverables' / STEM
def longpath(p):
 return Path('\\\\?\\' + str(p.resolve())) if not str(p).startswith('\\\\?\\') else p
PAYLOAD = longpath(OUT / 'payload')
ROOTS = [ROOT/'docs/cranial_bcsp_geov1_20261024', ROOT/'outputs/cranial_bcsp_geov1_20261024', ROOT/'outputs/cranial_geometry_diagnostic_20261023']
ALLOW = {'.py','.md','.json','.jsonl','.csv','.yaml','.yml','.sh','.ps1','.png','.html','.js','.txt','.sha256','.log','.xml','.patch','.bytes','.pid'}
SKIP_PARTS = {'__pycache__','.git','.pytest_cache','font_cache','matplotlib','mpl_cache'}
PATTERNS = {
 'private_key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'github_token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',
 'cloud_access_key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'bearer': rb'(?i)\bBearer[ \t]+[A-Za-z0-9_.-]{24,}',
 'jwt': rb'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b',
 'credential_url': rb'https?://[^\s/:@]{1,80}:[^\s/@]{1,160}@',
 'url_token': rb'(?i)[?&](?:access_token|auth_token|token)=[A-Za-z0-9_.%-]{16,}',
}

def sha(b): return hashlib.sha256(b).hexdigest()
def write(path,b):
 path=longpath(path)
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f: f.write(b)
def jwrite(path,value): write(path,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())

def main():
 if OUT.exists(): raise RuntimeError('Archive output already exists; no overwrite')
 chosen, excluded, findings = [], [], []
 for root in ROOTS:
  for p in sorted(root.rglob('*')):
   if not p.is_file(): continue
   rel=p.relative_to(ROOT).as_posix()
   reason=None
   if p.is_symlink(): reason='symlink_not_followed'
   elif any(x in SKIP_PARTS or 'plot_cache' in x for x in p.parts): reason='generated_cache'
   elif p.suffix.lower() not in ALLOW: reason='arrays_weights_archives_or_nonallowlisted_binary'
   elif p.name.lower() in {'auth.json','.env','credentials','.netrc','id_rsa','id_ed25519'}: reason='credential_filename'
   if reason:
    excluded.append({'path':rel,'bytes':p.stat().st_size,'reason':reason}); continue
   b=p.read_bytes()
   hits=[rule for rule,pattern in PATTERNS.items() if re.search(pattern,b)]
   if hits: findings.append({'path':rel,'rules':hits})
   chosen.append((p,rel,len(b),sha(b)))
 # Bind the historical parent files by their frozen hashes, never a drifting worktree.
 binding=json.loads((ROOT/'outputs/cranial_bcsp_geov1_20261024/consolidated_binding_v1/mother_and_training_design_binding_v1.json').read_text(encoding='utf-8'))
 for spec in binding['files']:
  p=Path(spec['parent_path']); b=p.read_bytes()
  assert len(b)==spec['bytes'] and sha(b)==spec['sha256'], spec['relative_path']
  rel='parent_source_snapshot/'+spec['relative_path']
  hits=[rule for rule,pattern in PATTERNS.items() if re.search(pattern,b)]
  if hits: findings.append({'path':rel,'rules':hits})
  chosen.append((p,rel,len(b),sha(b)))
 extra=['run_multisurface_CPU_v1.py','run_stageA_geometry_v1.py','summarize_multisurface_CPU_v1.py','summarize_stageA_v1.py','local_tools/archive_bcsp_representation_stage_20261104_v1.py']
 for rel in extra:
  p=ROOT/rel; b=p.read_bytes(); chosen.append((p,rel,len(b),sha(b)))
 if findings:
  print(json.dumps({'status':'STOP_SECRET_PATTERN_REVIEW','findings':findings},ensure_ascii=True)); return
 assert len({rel for _,rel,_,_ in chosen})==len(chosen)
 records=[]
 for p,rel,size,digest in chosen:
  b=p.read_bytes(); assert len(b)==size and sha(b)==digest, rel
  member='evidence/'+rel
  write(PAYLOAD/member,b)
  records.append({'path':member,'source_path':p.as_posix(),'bytes':size,'sha256':digest})
 # Portable report is explicitly a derived navigation copy; original bytes stay in evidence.
 report=ROOT/'docs/cranial_bcsp_geov1_20261024/骨组织完整边界点云_表示缺损采样与点数综合实验报告_20261104_zh_v1.md'
 portable=report.read_text(encoding='utf-8').replace(ROOT.as_posix()+'/', 'evidence/')
 portable='> GitHub／归档阅读副本：仅将本机绝对链接改为归档相对链接；原报告字节见 evidence/docs。\n\n'+portable
 write(PAYLOAD/'REPORT_zh.md',portable.encode())
 readme='''# 颅骨完整边界表示、实体缺损与采样研究归档

冻结日期：2026-11-04；实验范围：2026-10-23至2026-11-04。

## 阅读顺序

1. [综合实验报告](REPORT_zh.md)：研究问题、方法、结果、负结果和下一阶段路线。
2. evidence/docs/cranial_bcsp_geov1_20261024：正式方案与当前采样收束决定。
3. evidence/outputs/cranial_bcsp_geov1_20261024：采样、实体QC、模型入口、测试、评分、指标、审计及图表。
4. evidence/outputs/cranial_geometry_diagnostic_20261023：最初三数据集表示诊断。
5. evidence/parent_source_snapshot：按原冻结哈希验证的7个母版文件；其余母版继承本仓库父提交。

## 当前结论

输入为残骨D的完整边界，目标为缺失骨块G的完整边界。主线固定V1物理面积均匀采样、8192→8192；这不是最优性证明。SkullBreak/SkullFix主数据范围保持冻结。MUG实体方法已实现，但未通过高精度解剖GT准入。模型对照使用B0 AdaPoinTr，不是Mamba有效性结论。

## 保存范围与恢复限制

包含源代码、测试、配置/协议、机器可读指标、逐病例/来源评分、计数、审计、中文报告、静态和交互图。历史失败与待授权状态如实保留，不是当前运行指令。

不包含checkpoint、原始NRRD/STL、NPZ/NPY点集或预测数组、运输压缩包、编译环境、缓存和凭据。排除文件的路径/大小见excluded_inventory.json。它们保留在原本机位置；本任务不移动或删除它们。本归档可核查代码与已算指标，不是脱离原始资产可直接重训/重新推理的完整恢复包。部分历史脚本依赖绝对路径，需按原冻结合同恢复资产，禁止直接执行旧launcher。

原始文件字节保持不变，因此其内嵌绝对路径和历史链接未统一改写。REPORT_zh.md是明确标注的便携链接副本。正文图片属于已有开发数据几何诊断，不是原始CT；不构成临床验证。第三方代码及Plotly等保留原版权/许可说明，不新增替代许可。

files.sha256覆盖所有payload文件（自身除外）；manifest.json绑定源身份；excluded_inventory.json记录未复制资产。外层tar.gz另有SHA256、bytes和完整成员清单。构建过程流式重读归档并逐成员验证大小/哈希，不重跑科研计算。发布后以Git commit和annotated tag定位版本。
'''
 write(PAYLOAD/'README.md',readme.encode())
 jwrite(PAYLOAD/'manifest.json',{'scope':'Code, configurations, numerical results, diagnostics and evidence; no model weights or data arrays','source_roots':[p.as_posix() for p in ROOTS],'file_count':len(records),'source_bytes':sum(r['bytes'] for r in records),'files':records,'secret_scan_rules':list(PATTERNS),'secret_findings':[]})
 jwrite(PAYLOAD/'excluded_inventory.json',{'count':len(excluded),'bytes':sum(r['bytes'] for r in excluded),'files':excluded,'warning':'Excluded assets remain at original local paths; no copying, deletion or backup certification implied'})
 payload_files=sorted(p for p in PAYLOAD.rglob('*') if p.is_file())
 listing=[f'{sha(p.read_bytes())}  {p.relative_to(PAYLOAD).as_posix()}' for p in payload_files]
 write(PAYLOAD/'files.sha256',('\n'.join(listing)+'\n').encode())
 payload_files=sorted(p for p in PAYLOAD.rglob('*') if p.is_file())
 archive=OUT/(STEM+'.tar.gz')
 with archive.open('xb') as raw:
  with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz:
   with tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as tf:
    for p in payload_files:
     b=p.read_bytes(); info=tarfile.TarInfo(p.relative_to(PAYLOAD).as_posix());info.size=len(b);info.mtime=0;info.mode=0o644;tf.addfile(info,io.BytesIO(b))
 expected={p.relative_to(PAYLOAD).as_posix():(p.stat().st_size,sha(p.read_bytes())) for p in payload_files}
 checked=0
 with tarfile.open(archive,'r:gz') as tf:
  members=tf.getmembers();assert len(members)==len(expected)==len({m.name for m in members})
  for m in members:
   assert m.isfile() and '..' not in Path(m.name).parts
   b=tf.extractfile(m).read();assert (len(b),sha(b))==expected[m.name],m.name;checked+=1
 b=archive.read_bytes();digest=sha(b)
 write(OUT/(STEM+'.sha256'),f'{digest}  {archive.name}\n'.encode())
 write(OUT/(STEM+'.bytes'),f'{len(b)}\n'.encode())
 write(OUT/(STEM+'.tar_contents.txt'),('\n'.join(expected)+'\n').encode())
 result={'status':'LOCAL_ARCHIVE_MEMBER_HASH_VERIFICATION_PASS','archive':archive.as_posix(),'bytes':len(b),'sha256':digest,'members':checked,'source_files':len(records),'source_bytes':sum(r['bytes'] for r in records),'excluded_files':len(excluded),'included_extensions':dict(Counter(Path(r['path']).suffix for r in records)),'secret_pattern_findings':0,'checkpoint_files':0,'array_files':0,'source_files_modified':False}
 jwrite(OUT/'archive_verification_v1.json',result)
 print(json.dumps(result,ensure_ascii=True))

if __name__=='__main__': main()
