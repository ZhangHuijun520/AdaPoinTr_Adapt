from pathlib import Path
import hashlib,json,zipfile
N=Path(__file__).resolve().parent;ROOT=next(p for p in N.parents if p.name=='mamba-ccf-c-1-high-resolution')
old=json.loads((N.parent/'results/results.json').read_bytes());api=ROOT.parent
tests=json.loads((N/'CPU_tests.json').read_bytes());assert tests['status']=='PASS' and tests['tests']==6 and tests['implementation_sha256']==hashlib.sha256((N/'coordinate_evidence_v1.py').read_bytes()).hexdigest()
metadata=Path('E:/dataset/MUG500plus/metadata_v20/mug500plus_files_v20.json');files=json.loads(metadata.read_bytes());official=next(x for x in files if x['name']=='A0136-A0140.zip')
archive=Path('E:/dataset/MUG500plus/raw_v20/archives/d6_development100_v1/batch_001/A0136-A0140.zip');cases=[]
with zipfile.ZipFile(archive) as z:
 for r in old['cases']:
  sid=r['source_id'];i=z.getinfo('A0136-A0140/'+sid+'/'+sid+'.stl')
  cases.append(dict(source_id=sid,clear_stl={k:r['clear_stl'][k] for k in ['path','bytes','sha256']},original_stl=dict(member=i.filename,bytes=i.file_size,CRC=i.CRC),admission=r))
scope=dict(date_Asia_Shanghai='2026-10-29',archive=dict(path=str(archive),bytes=official['size'],official_v20_md5=official['computed_md5']),cases=cases,
 implementation_sha256=hashlib.sha256((N/'coordinate_evidence_v1.py').read_bytes()).hexdigest(),local_official_metadata_sha256=hashlib.sha256(metadata.read_bytes()).hexdigest(),
 budget=dict(total_seconds=300,case_seconds=120,RSS_bytes=8589934592,counted_read_bytes=6442450944,threads=2),
 reads='Opaque checksum of single official ZIP;decode only originalSTL A0136/A0137/A0138;exact256 deterministic clear vertex samples;no other source geometry,threshold,repair or mask generation')
with (N/'scope.json').open('x') as f:json.dump(scope,f,indent=2)
print('FROZEN exact3 coordinate provenance and official archive checksum')
