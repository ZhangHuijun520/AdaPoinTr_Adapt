"""Read-only report/source verification and document delivery manifest."""
from pathlib import Path
import hashlib,json,re
S=Path(__file__).resolve().parent
def digest(p):
 b=p.read_bytes()
 return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
sources=json.loads((S/'source_evidence_manifest_v1.json').read_text(encoding='utf-8'))['sources']
for key,item in sources.items():
 actual=digest(Path(item['path']))
 assert all(actual[k]==item[k] for k in ('bytes','sha256')),key
validation=json.loads((S/'report_content_validation_v1.json').read_text(encoding='utf-8'))
md=Path(validation['report']['path']);actual=digest(md)
assert actual==validation['report']
hv=json.loads((S/'HTML_reading_copy_validation_v1.json').read_text(encoding='utf-8'))
hp=md.with_suffix('.html')
assert digest(hp)['sha256']==hv['html_sha256']
assert hv['source_markdown_sha256']==actual['sha256']
assert all(x['status']=='SVG' for x in hv['formulae'])
assert hv['embedded_PNG']==2 and hv['external_script_tags']==0
text=md.read_text(encoding='utf-8')
assert not re.search(r'\{\{[^}]+\}\}',text)
for target in re.findall(r'\]\((E:/[^)]+)\)',text):
 assert Path(target).exists(),target
names=[md.name,hp.name,'verified_report_values_v1.json','source_evidence_manifest_v1.json','report_content_validation_v1.json','training_loss_log_interpretation_v1.json','HTML_reading_copy_validation_v1.json']
result={'status':'ROUND_SCIENTIFICALLY_CLOSED_REPORT_DELIVERED','date_Asia_Shanghai':'2026-11-12','verified_frozen_source_count':len(sources),'deliverables':[digest(S/n) for n in names],'checks':{'frozen_sources_unchanged':True,'report_and_reading_copy_hashes_match':True,'seven_formulae_rendered':True,'local_markdown_evidence_links_exist':True},'boundary':{'new_training':0,'new_scoring':0,'server_operations':0,'GitHub_push':False,'checkpoint_long_term_archive_completed_by_this_task':False,'next_stage_authorized_by_report':False},'limitations':['HTML browser visual QA not performed; structural checks completed.','Scientific closure does not imply stable superiority or clinical validation.']}
with (S/'delivery_manifest_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':result['status'],'sources_verified':len(sources),'report_bytes':actual['bytes'],'report_sha256':actual['sha256']},ensure_ascii=False))
