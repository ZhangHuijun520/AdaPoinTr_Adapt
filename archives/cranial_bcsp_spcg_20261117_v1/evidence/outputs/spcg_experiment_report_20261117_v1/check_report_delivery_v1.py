# -*- coding: utf-8 -*-
"""Final document formatting and evidence cross-checks; no experiment recomputation."""
from pathlib import Path
import json,re,hashlib
O=Path(__file__).resolve().parent;report=O/'Cranial_BCSP_FullMamba_BCSP_SPCG_完整实验报告_zh_v1.md'
body=report.read_text(encoding='utf-8')
# Remove empty lines inside Markdown tables; ensure separation outside tables.
while re.search(r'(?m)(^\|[^\n]*\|\n)\n(?=\|)',body):body=re.sub(r'(?m)(^\|[^\n]*\|\n)\n(?=\|)',r'\1',body)
lines=body.splitlines();out=[]
for line in lines:
 if line.startswith('|') and out and out[-1] and not out[-1].startswith('|'):out.append('')
 if out and out[-1].startswith('|') and line and not line.startswith('|'):out.append('')
 out.append(line)
body='\n'.join(out)+'\n'
assert not any(ord(c)<32 and c not in '\n\r\t' for c in body),'unexpected control characters'
assert '\\rho_i' in body and '\\frac{1}{|N_i|}' in body and '\\tau_i' in body
facts=json.loads((O/'report_facts_v1.json').read_bytes());evidence=json.loads((O/'evidence_manifest_v1.json').read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
for x in evidence['files']:
 p=Path(x['path']);assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
assert len(re.findall(r'^## \d+\.',body,re.M))==16
for row in facts['training_matrix']:assert row['freeze']['checkpoint']['sha256'] in body
for fold in ['C','D']:
 for arm in ['G0','G1','G2']:
  m=facts['absolute_and_paired']['folds'][fold]['arms'][arm]['metrics']
  expected=f"|{fold}|{arm}|{m['E_P95_mm']:.4f}|{m['J_P95_mm']:.4f}|{m['CD_L1_mm']:.4f}|{100*m['E_coverage_2.0mm']:.2f}|{100*m['J_coverage_2.0mm']:.2f}|"
  assert expected in body
assert all(s in body for s in ['NOT_COLLECTED','跨设备','seed0','20.185363458096','32.42%','不执行新的正式E0/M/U gate'])
tables=0;in_table=False;columns=None
for line in body.splitlines():
 if line.startswith('|'):
  n=len(line.split('|'))
  if not in_table:tables+=1;columns=n
  else:assert n==columns,'table column drift: '+line
  in_table=True
 else:in_table=False
assert tables>=12
for url in re.findall(r'\]\(([^)]+)\)',body):
 if re.match(r'^[A-Z]:/',url):assert Path(url).exists(),url
report.write_text(body,encoding='utf-8',newline='\n')
check=json.loads((O/'report_consistency_review_v1.json').read_bytes());check['report']=rec(report);check.update(final_document_checks=dict(six_model_rows_exact=True,six_checkpoint_hashes_present=True,all85_evidence_files_stable=True,math_backslashes_intact=True,Markdown_tables_contiguous=True,table_count=tables,absolute_local_links_exist=True),formatting_only_revision=True)
(O/'report_consistency_review_v1.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=dict(status='COMPREHENSIVE_SPCG_REPORT_COMPLETE_VERIFIED',files=[rec(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='delivery_manifest_v1.json'])
(O/'delivery_manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(status=manifest['status'],report=rec(report),tables=tables,evidence_files=len(evidence['files'])),ensure_ascii=False))
