import os,socket,json,hashlib,base64,stat,time,io,tarfile,subprocess,shutil
from pathlib import Path
START=time.monotonic();created=[];created_dirs=[];phase='IDENTITY'
M=json.loads(base64.b64decode('ewogICJzY2hlbWEiOiAiYmNzcC1yZXNlYXJjaC1wcmlvcml0eS1taW5pbWFsLWluc3RhbGxhdGlvbi12MSIsCiAgInN0YXR1cyI6ICJQUkVQQVJFRF9OT1RfREVQTE9ZRUQiLAogICJleHBlY3RlZF9pZGVudGl0eSI6IHsKICAgICJob3N0bmFtZSI6ICJzaHUtY29tbW9uLTI1NzIxNDUyLW5vdGVib29rLTAxZHQwOC0wIiwKICAgICJ1aWQiOiAxMDAwLAogICAgInByb2plY3QiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5UciIsCiAgICAiZ3B1X3V1aWQiOiAiR1BVLWU3NjNkMzg5LWI0YzItNGRjOC05NTcxLWQ3MzQzZWMzMjhiMSIsCiAgICAiZ3B1X25hbWUiOiAiTlZJRElBIEdlRm9yY2UgUlRYIDQwOTAgRCIsCiAgICAiZHJpdmVyX3ZlcnNpb24iOiAiNTcwLjE5MCIsCiAgICAibnZpZGlhX3NtaV9tZW1vcnlfdG90YWxfTWlCIjogMjQ1NjQsCiAgICAicHl0aG9uX3JlYWxwYXRoIjogIi9vcHQvY29uZGEvZW52cy9hZGFwb2ludHItbWFtYmEvYmluL3B5dGhvbjMuMTAiLAogICAgInB5dGhvbl92ZXJzaW9uIjogIjMuMTAuMjAiLAogICAgInRvcmNoX3ZlcnNpb24iOiAiMi40LjErY3UxMTgiLAogICAgIm51bXB5X3ZlcnNpb24iOiAiMi4yLjYiLAogICAgInRpbW1fdmVyc2lvbiI6ICIxLjAuMjciLAogICAgIm1lbW9yeV9xdWVyeV9zZW1hbnRpY3MiOiAiU01JIHBoeXNpY2FsIFVVSUQvcm91bmRlZCBtZW1vcnkgc2VwYXJhdGUgZnJvbSB0b3JjaCBsb2dpY2FsIGN1ZGE6MC9wcm9wZXJ0aWVzLiBEbyBub3QgZGVtYW5kIGJ5dGUgZXF1YWxpdHkgYmV0d2VlbiB0aGUgdHdvIGludGVyZmFjZXM7IHJlcXVpcmUgb25lIHZpc2libGUgbG9naWNhbCBkZXZpY2UgbWFwcGVkIHZpYSB0aGUgZml4ZWQgVVVJRCBhbmQgcmVjb3JkIHRvcmNoIGNhcGFjaXR5LiIKICB9LAogICJwcm9qZWN0IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIiLAogICJuZXdfZGlyZWN0b3J5IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9nZW92MV90cmFpbmluZ19mb2xkY184MTkyX3NlZWQwX3YxL2V2aWRlbmNlL3Jlc2VhcmNoX3ByaW9yaXR5XzAxZHQwOF92MSIsCiAgImZpbGVzIjogWwogICAgewogICAgICAiYXJjaGl2ZV9tZW1iZXIiOiAiYmNzcF90cmFpbmluZ19lbnRyeV9yZXNlYXJjaF92NS5weSIsCiAgICAgICJzb3VyY2UiOiB7CiAgICAgICAgInBhdGgiOiAiRTpcXENvZGV4XFwyMDI2LTA2LTA2XFxtYW1iYS1jY2YtYy0xLWhpZ2gtcmVzb2x1dGlvblxcb3V0cHV0c1xcY3JhbmlhbF9iY3NwX2dlb3YxXzIwMjYxMDI0XFxyZXNvdXJjZV9yZWJpbmRfaW1wbGVtZW50YXRpb25fdjFcXG1vbml0b3JfZGlhZ25vc3RpY192M1xccmVzZWFyY2hfcHJpb3JpdHlfbW9uaXRvcl92NFxcbmV3X2NvbnRhaW5lcl90cmFpbmluZ192MVxcYmNzcF90cmFpbmluZ19lbnRyeV9yZXNlYXJjaF92NS5weSIsCiAgICAgICAgImJ5dGVzIjogMTYwNTksCiAgICAgICAgInNoYTI1NiI6ICJhMDFhOWMzYzNlMmRiZTU4MmRiNGYyYTE5Njc3MWFlMmNkNzU1YWFiMjBmMjBmMWM5ZGQzNGYzZjljZTM3ZGNlIgogICAgICB9LAogICAgICAidGFyZ2V0IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9nZW92MV90cmFpbmluZ19mb2xkY184MTkyX3NlZWQwX3YxL2Jjc3BfdHJhaW5pbmdfZW50cnlfcmVzZWFyY2hfdjUucHkiLAogICAgICAiYnl0ZXMiOiAxNjA1OSwKICAgICAgInNoYTI1NiI6ICJhMDFhOWMzYzNlMmRiZTU4MmRiNGYyYTE5Njc3MWFlMmNkNzU1YWFiMjBmMjBmMWM5ZGQzNGYzZjljZTM3ZGNlIgogICAgfSwKICAgIHsKICAgICAgImFyY2hpdmVfbWVtYmVyIjogImJjc3BfdHJhaW5pbmdfY29udHJhY3RfMDFkdDA4X3YzLnB5IiwKICAgICAgInNvdXJjZSI6IHsKICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXHJlc291cmNlX3JlYmluZF9pbXBsZW1lbnRhdGlvbl92MVxcbW9uaXRvcl9kaWFnbm9zdGljX3YzXFxyZXNlYXJjaF9wcmlvcml0eV9tb25pdG9yX3Y0XFxuZXdfY29udGFpbmVyX3RyYWluaW5nX3YxXFxiY3NwX3RyYWluaW5nX2NvbnRyYWN0XzAxZHQwOF92My5weSIsCiAgICAgICAgImJ5dGVzIjogMTY1MzEsCiAgICAgICAgInNoYTI1NiI6ICIwOGE5YWYzNjFlZjAyNzljZmNjZjI3ZjlkMDk0MDIwNTAxYmZjYzk4NTk2OTJjYTY0MzIyZDhkZDRjN2ZkNDk5IgogICAgICB9LAogICAgICAidGFyZ2V0IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9nZW92MV90cmFpbmluZ19mb2xkY184MTkyX3NlZWQwX3YxL2Jjc3BfdHJhaW5pbmdfY29udHJhY3RfMDFkdDA4X3YzLnB5IiwKICAgICAgImJ5dGVzIjogMTY1MzEsCiAgICAgICJzaGEyNTYiOiAiMDhhOWFmMzYxZWYwMjc5Y2ZjY2YyN2Y5ZDA5NDAyMDUwMWJmY2M5ODU5NjkyY2E2NDMyMmQ4ZGQ0YzdmZDQ5OSIKICAgIH0sCiAgICB7CiAgICAgICJhcmNoaXZlX21lbWJlciI6ICJyZWFkb25seV9pZGVudGl0eV9hc3NldHNfMDFkdDA4X3YxLmpzb24iLAogICAgICAic291cmNlIjogewogICAgICAgICJwYXRoIjogIkU6XFxDb2RleFxcMjAyNi0wNi0wNlxcbWFtYmEtY2NmLWMtMS1oaWdoLXJlc29sdXRpb25cXG91dHB1dHNcXGNyYW5pYWxfYmNzcF9nZW92MV8yMDI2MTAyNFxccmVzb3VyY2VfcmViaW5kX2ltcGxlbWVudGF0aW9uX3YxXFxtb25pdG9yX2RpYWdub3N0aWNfdjNcXHJlc2VhcmNoX3ByaW9yaXR5X21vbml0b3JfdjRcXG5ld19jb250YWluZXJfdHJhaW5pbmdfdjFcXHJlYWRvbmx5X2lkZW50aXR5X2Fzc2V0c18wMWR0MDhfdjEuanNvbiIsCiAgICAgICAgImJ5dGVzIjogMTA1MTQsCiAgICAgICAgInNoYTI1NiI6ICJlZmRmM2I1MjFkNjYxMjkxYWY4OGJlN2ZlZmY5ZThiZDhjZjgzZGQ0OTlkNGE1YTkzY2U2Yzg3OTllNTFkODVjIgogICAgICB9LAogICAgICAidGFyZ2V0IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9nZW92MV90cmFpbmluZ19mb2xkY184MTkyX3NlZWQwX3YxL2V2aWRlbmNlL3Jlc2VhcmNoX3ByaW9yaXR5XzAxZHQwOF92MS9yZWFkb25seV9pZGVudGl0eV9hc3NldHNfMDFkdDA4X3YxLmpzb24iLAogICAgICAiYnl0ZXMiOiAxMDUxNCwKICAgICAgInNoYTI1NiI6ICJlZmRmM2I1MjFkNjYxMjkxYWY4OGJlN2ZlZmY5ZThiZDhjZjgzZGQ0OTlkNGE1YTkzY2U2Yzg3OTllNTFkODVjIgogICAgfSwKICAgIHsKICAgICAgImFyY2hpdmVfbWVtYmVyIjogInJlc291cmNlX3JlYmluZF8wMWR0MDhfdjEuanNvbiIsCiAgICAgICJzb3VyY2UiOiB7CiAgICAgICAgInBhdGgiOiAiRTpcXENvZGV4XFwyMDI2LTA2LTA2XFxtYW1iYS1jY2YtYy0xLWhpZ2gtcmVzb2x1dGlvblxcb3V0cHV0c1xcY3JhbmlhbF9iY3NwX2dlb3YxXzIwMjYxMDI0XFxyZXNvdXJjZV9yZWJpbmRfaW1wbGVtZW50YXRpb25fdjFcXG1vbml0b3JfZGlhZ25vc3RpY192M1xccmVzZWFyY2hfcHJpb3JpdHlfbW9uaXRvcl92NFxcbmV3X2NvbnRhaW5lcl90cmFpbmluZ192MVxccmVzb3VyY2VfcmViaW5kXzAxZHQwOF92MS5qc29uIiwKICAgICAgICAiYnl0ZXMiOiAzNTk0LAogICAgICAgICJzaGEyNTYiOiAiNzczMGY2NmExNjViZDEwZDkwODZmMDFmYWQxMGVkYmRlNjEwNjJlZTQyY2IyZjg0MzFjMTJmNTFkZmI3ZjU5YSIKICAgICAgfSwKICAgICAgInRhcmdldCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfZ2VvdjFfdHJhaW5pbmdfZm9sZGNfODE5Ml9zZWVkMF92MS9ldmlkZW5jZS9yZXNlYXJjaF9wcmlvcml0eV8wMWR0MDhfdjEvcmVzb3VyY2VfcmViaW5kXzAxZHQwOF92MS5qc29uIiwKICAgICAgImJ5dGVzIjogMzU5NCwKICAgICAgInNoYTI1NiI6ICI3NzMwZjY2YTE2NWJkMTBkOTA4NmYwMWZhZDEwZWRiZGU2MTA2MmVlNDJjYjJmODQzMWMxMmY1MWRmYjdmNTlhIgogICAgfSwKICAgIHsKICAgICAgImFyY2hpdmVfbWVtYmVyIjogImxvY2FsX1AzXzAxZHQwOF92MS5qc29uIiwKICAgICAgInNvdXJjZSI6IHsKICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXHJlc291cmNlX3JlYmluZF9pbXBsZW1lbnRhdGlvbl92MVxcbW9uaXRvcl9kaWFnbm9zdGljX3YzXFxyZXNlYXJjaF9wcmlvcml0eV9tb25pdG9yX3Y0XFxuZXdfY29udGFpbmVyX3RyYWluaW5nX3YxXFxsb2NhbF9QM18wMWR0MDhfdjEuanNvbiIsCiAgICAgICAgImJ5dGVzIjogMTcwOCwKICAgICAgICAic2hhMjU2IjogIjFlYjhkZmMyOGFmODgwMzI4MjAzZDE1MzU3OWY5ZmFhM2Y3MWQzMmEzYzMyZDk2MmVmNGFiMjliNjIxMzJlNGUiCiAgICAgIH0sCiAgICAgICJ0YXJnZXQiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci90aGlyZF9wYXJ0eS9iY3NwX2dlb3YxX3RyYWluaW5nX2ZvbGRjXzgxOTJfc2VlZDBfdjEvZXZpZGVuY2UvcmVzZWFyY2hfcHJpb3JpdHlfMDFkdDA4X3YxL2xvY2FsX1AzXzAxZHQwOF92MS5qc29uIiwKICAgICAgImJ5dGVzIjogMTcwOCwKICAgICAgInNoYTI1NiI6ICIxZWI4ZGZjMjhhZjg4MDMyODIwM2QxNTM1NzlmOWZhYTNmNzFkMzJhM2MzMmQ5NjJlZjRhYjI5YjYyMTMyZTRlIgogICAgfSwKICAgIHsKICAgICAgImFyY2hpdmVfbWVtYmVyIjogInJlc2VhcmNoX3ByaW9yaXR5X3BvbGljeV92NF96aC5tZCIsCiAgICAgICJzb3VyY2UiOiB7CiAgICAgICAgInBhdGgiOiAiRTpcXENvZGV4XFwyMDI2LTA2LTA2XFxtYW1iYS1jY2YtYy0xLWhpZ2gtcmVzb2x1dGlvblxcb3V0cHV0c1xcY3JhbmlhbF9iY3NwX2dlb3YxXzIwMjYxMDI0XFxyZXNvdXJjZV9yZWJpbmRfaW1wbGVtZW50YXRpb25fdjFcXG1vbml0b3JfZGlhZ25vc3RpY192M1xccmVzZWFyY2hfcHJpb3JpdHlfbW9uaXRvcl92NFxccmVzZWFyY2hfcHJpb3JpdHlfcG9saWN5X3Y0X3poLm1kIiwKICAgICAgICAiYnl0ZXMiOiAyOTY0LAogICAgICAgICJzaGEyNTYiOiAiYWYxODIwYTBkNDdiYjUzYjIzZjNjYTViNWFiOGYwMGIwNjI2NTBjZmE3M2ZkNGE3OGFhNTI5ZjhiZjBkZDc2OCIKICAgICAgfSwKICAgICAgInRhcmdldCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfZ2VvdjFfdHJhaW5pbmdfZm9sZGNfODE5Ml9zZWVkMF92MS9ldmlkZW5jZS9yZXNlYXJjaF9wcmlvcml0eV8wMWR0MDhfdjEvcmVzZWFyY2hfcHJpb3JpdHlfcG9saWN5X3Y0X3poLm1kIiwKICAgICAgImJ5dGVzIjogMjk2NCwKICAgICAgInNoYTI1NiI6ICJhZjE4MjBhMGQ0N2JiNTNiMjNmM2NhNWI1YWI4ZjAwYjA2MjY1MGNmYTczZmQ0YTc4YWE1MjlmOGJmMGRkNzY4IgogICAgfQogIF0sCiAgInJ1bGVzIjogWwogICAgIkJlZm9yZSB3cml0aW5nIHJlY2hlY2sgY3VycmVudCBpZGVudGl0eSxhcmNoaXZlIGhhc2gsYWxsIHNpeCB0YXJnZXRzIGFic2VudCBhbmQgYWxsIHBhcmVudHMgc2FmZSIsCiAgICAiQ3JlYXRlIG9ubHkgdGhlIG9uZSBuZXcgZXZpZGVuY2UgZGlyZWN0b3J5OyB1c2UgZXhjbHVzaXZlIG5vLWZvbGxvdyBmaWxlIGNyZWF0aW9uLG5ldmVyIG92ZXJ3cml0ZSIsCiAgICAiVmVyaWZ5IGFsbCBzaXggaW5zdGFsbGVkIHNpemVzL2hhc2hlcyBhbmQgdHdvIHJldXNlZCBtb2R1bGVzIGJlZm9yZSB0cmFpbmluZyBjb250cm9sbGVyIiwKICAgICJObyBpbnN0YWxsYXRpb24gc2NyaXB0cyBvciBtb2RlbC9kYXRhIGNoYW5nZXMiLAogICAgIkFueSBwYXJ0aWFsIG9yIGFtYmlndW91cyBmYWlsdXJlIHN0b3BzO2RvIG5vdCByZXRyeSBhdXRvbWF0aWNhbGx5IgogIF0KfQo='))
SCOPE_SHA='16655f4494fe2458619129958a370d240866a15b339ec2d40b595d827b675f0a'
ARCHIVE='/home/jovyan/bcsp_research_priority_01dt08_v1.tar.gz'
ARCHIVE_SIZE=16964
ARCHIVE_SHA='95be77da95f46945e0b713badeca823098cbb8bc84b3a5348597ba03e60da899'
NEW_DIR=Path(M['new_directory']);PROJECT=Path(M['project'])

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def event(value):
    print(json.dumps(value, ensure_ascii=True), flush=True)

def budget():
    need(time.monotonic() - START < 100, 'installation time budget')

def parents(path, allow_missing=False):
    for p in reversed(path.parents):
        if allow_missing and not os.path.lexists(p):
            need(p == NEW_DIR, 'unlisted missing parent: ' + str(p))
            continue
        need(stat.S_ISDIR(p.lstat().st_mode), 'linked/non-directory parent: ' + str(p))

def absent(path, allow_missing=False):
    parents(path, allow_missing)
    need(not os.path.lexists(path), 'installation collision: ' + str(path))

def read_exact(record):
    budget()
    p = Path(record['path'])
    parents(p)
    st = p.lstat()
    need(stat.S_ISREG(st.st_mode) and st.st_size == record['bytes'], 'file type/size: ' + str(p))
    raw = p.read_bytes()
    after = p.stat()
    need((st.st_size, st.st_mtime_ns, st.st_ino) ==
         (after.st_size, after.st_mtime_ns, after.st_ino), 'file changed: ' + str(p))
    need(len(raw) == record['bytes'] and sha(raw) == record['sha256'], 'file hash: ' + str(p))
    return raw

def dirfd(path):
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise

try:
 identity=M['expected_identity']
 need(socket.gethostname()==identity['hostname'] and os.getuid()==identity['uid'],'hostname/uid')
 parents(PROJECT);need(stat.S_ISDIR(PROJECT.lstat().st_mode),'project');os.chdir(PROJECT)
 def cmd(args):
  p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True)
  return p.stdout.decode().strip()
 v=[x.strip() for x in cmd(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']).split(',')]
 need(v[:4]==[identity['gpu_uuid'],identity['gpu_name'],identity['driver_version'],str(identity['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
 need(not cmd(['/usr/bin/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']),'GPU not idle')
 phase='ARCHIVE_AND_EXISTING_ASSETS'
 archive=read_exact(dict(path=ARCHIVE,bytes=ARCHIVE_SIZE,sha256=ARCHIVE_SHA))
 rows=M['files'];need(len(rows)==len({x['target'] for x in rows})==6,'six targets')
 content={};expected={x['archive_member']:x for x in rows}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
  ms=tf.getmembers();need(len(ms)==len({x.name for x in ms})==6 and {x.name for x in ms}==set(expected),'members')
  for x in ms:
   need(x.isfile() and '/' not in x.name and '\\' not in x.name and x.size<=262144,'member type/path/size')
   r=expected[x.name];raw=tf.extractfile(x).read();need(len(raw)==r['bytes'] and sha(raw)==r['sha256'],'member hash')
   target=Path(r['target']);need(target.parent in [NEW_DIR,NEW_DIR.parent.parent],'exact installation boundary')
   content[target]=raw
 report=json.loads(next(raw for p,raw in content.items() if p.name=='readonly_identity_assets_01dt08_v1.json'))
 for r in report['frozen_assets']['manifest']:
  read_exact(dict(path=r['path'],bytes=r['expected_bytes'],sha256=r['expected_sha256']))
 phase='ALL_TARGETS_ABSENT'
 absent(NEW_DIR)
 for p in content:absent(p,allow_missing=True)
 need(shutil.disk_usage(PROJECT).free>=4294967296+sum(map(len,content.values())),'disk')
 event(dict(status='SIX_FILE_PREWRITE_PASS',scope_sha256=SCOPE_SHA,targets=6,selected_assets=30,server_writes=0))
 phase='EXCLUSIVE_INSTALLATION'
 fd=dirfd(NEW_DIR.parent)
 try:os.mkdir(NEW_DIR.name,0o700,dir_fd=fd);created_dirs.append(str(NEW_DIR))
 finally:os.close(fd)
 for p,raw in content.items():
  absent(p);fd=dirfd(p.parent)
  try:
   child=os.open(p.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644,dir_fd=fd);created.append(str(p))
   with os.fdopen(child,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  finally:os.close(fd)
 for r in rows:read_exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
 need(set(p.name for p in NEW_DIR.iterdir())=={Path(r['target']).name for r in rows if Path(r['target']).parent==NEW_DIR},'evidence set')
 event(dict(status='SIX_FILE_INSTALLATION_HASH_PASS',scope_sha256=SCOPE_SHA,created=created,directories=created_dirs,training_started=False,seconds=time.monotonic()-START))
except BaseException as exc:
 event(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),created=created,directories=created_dirs,training_started=False));raise
