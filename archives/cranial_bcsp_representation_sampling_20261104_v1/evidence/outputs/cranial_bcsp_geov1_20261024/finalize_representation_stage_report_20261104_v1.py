"""Finalize document and linked-media identity checks; no scientific execution."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]
out = root / 'outputs/cranial_bcsp_geov1_20261024/representation_stage_report_20261104_v1'
manifest_path = out / 'evidence_manifest_v1.json'
verify_path = out / 'report_verification_v1.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
report = Path(manifest['report']['path'])
text = report.read_text(encoding='utf-8')

def identity(p):
    b = p.read_bytes()
    return {'path': p.as_posix(), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

for record in manifest['sources']:
    current = identity(Path(record['path']))
    assert current['bytes'] == record['bytes'] and current['sha256'] == record['sha256']

targets = re.findall(r'\]\((?:<([^>]+)>|([^\s)]+))\)', text)
local_paths = [Path(a or b) for a,b in targets]
assert all(p.is_absolute() and p.is_file() for p in local_paths)
media = [identity(p) for p in local_paths if p.suffix.lower() == '.png']
assert len(media) == 3
assert '<!-- EVIDENCE_INDEX -->' not in text
assert text.count('```') % 2 == 0
manifest['report'] = identity(report)
manifest['reused_media'] = media
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
verification = {
    'status': 'REPORT_SOURCE_LINK_AND_IDENTITY_CHECK_PASS',
    'source_reports': len(manifest['sources']),
    'source_bytes': sum(r['bytes'] for r in manifest['sources']),
    'all_source_content_unchanged': True,
    'absolute_local_file_links_verified': len(local_paths),
    'reused_figures_verified': len(media),
    'report_utf8_characters': len(text),
    'report': manifest['report'],
    'scope': 'Existing local evidence synthesis only; no model, GPU, scoring, bootstrap, raw data decoding or server operations',
    'limitations': ['Link and identity checks do not independently recompute experimental metrics', 'No newly performed visual review or anatomical adjudication; figures are reused historical diagnostics', 'Server checkpoint hashes quoted from historical frozen reports, not remeasured in this report task']
}
verify_path.write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in verification.items() if k != 'report'},ensure_ascii=True))
print('report_bytes=' + str(manifest['report']['bytes']))
print('report_sha256=' + manifest['report']['sha256'])
