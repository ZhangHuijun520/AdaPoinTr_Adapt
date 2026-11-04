"""Read-only stdlib audit of this one finished training attempt; no model imports."""
import os,socket,json,hashlib,stat,time,math,subprocess
from pathlib import Path
from collections import Counter
import base64
SCOPE_RAW=base64.b64decode('ewogICJzY2hlbWEiOiAiYmNzcC1ibHVlLW5vaXNlLWZpcnN0LW1vZGVsLWV4ZWN1dGlvbi1zY29wZS12MSIsCiAgInN0YXR1cyI6ICJBV0FJVElOR19FWFBMSUNJVF9VU0VSX0FVVEhPUklaQVRJT04iLAogICJleGVjdXRpb25fYXV0aG9yaXplZCI6IGZhbHNlLAogICJzdGFnZSI6ICJCQ1NQX0JMVUVfTk9JU0VfQUJfVjEiLAogICJydW5faWQiOiAiYmNzcF9ibHVlX25vaXNlX2ZvbGRDX0V1Y2xpZGVhbl9lbGltaW5hdGlvbl9pbjgxOTJfb3V0ODE5Ml9zZWVkMF90cmFpbl92MSIsCiAgInNjb3BlIjogImFmdGVyIG1hbnVhbCB1cGxvYWQgYW5kIGV4cGxpY2l0IGNvbXBsZXRlLWhhc2ggYXV0aG9yaXphdGlvbjogZml4ZWQgbm9uLW92ZXJ3cml0ZSBpbnN0YWxsYXRpb24sIHRoZW4gZXhhY3RseSBvbmUgZnJlc2ggRXVjbGlkZWFuIEZvbGRDIHNlZWQwIHRyYWluaW5nOyBncmFwaCBhcm0gZGF0YSBpbnN0YWxsZWQgb25seSwgbm8gZ3JhcGggdHJhaW5pbmcgYXV0aG9yaXplZCIsCiAgInRyYWluaW5nX3J1bnNfYXV0aG9yaXplZF9ieV90aGlzX3BlbmRpbmdfc2NvcGUiOiAxLAogICJwbGFubmVkX3BhaXJfdG90YWxfcnVucyI6IDIsCiAgImNhbmRpZGF0ZV90cmFpbmluZ19hdXRob3JpemVkIjogZmFsc2UsCiAgImlkZW50aXR5IjogewogICAgImhvc3RuYW1lIjogInNodS1jb21tb24tMjU3MjE0NTItbm90ZWJvb2stdjJpd3NhLTAiLAogICAgInVpZCI6IDEwMDAsCiAgICAicHJvamVjdCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyIiwKICAgICJncHVfdXVpZCI6ICJHUFUtMzRhMWI5OTYtMmJkNy04OGU2LTlkY2EtMTY0YjcxOGNhZWE2IiwKICAgICJncHVfbmFtZSI6ICJOVklESUEgR2VGb3JjZSBSVFggNDA5MCBEIiwKICAgICJkcml2ZXJfdmVyc2lvbiI6ICI1NzAuMTkwIiwKICAgICJudmlkaWFfc21pX21lbW9yeV90b3RhbF9NaUIiOiAyNDU2NCwKICAgICJweXRob25fcmVhbHBhdGgiOiAiL29wdC9jb25kYS9lbnZzL2FkYXBvaW50ci1tYW1iYS9iaW4vcHl0aG9uMy4xMCIsCiAgICAicHl0aG9uX3ZlcnNpb24iOiAiMy4xMC4yMCIsCiAgICAidG9yY2hfdmVyc2lvbiI6ICIyLjQuMStjdTExOCIsCiAgICAibnVtcHlfdmVyc2lvbiI6ICIyLjIuNiIsCiAgICAidGltbV92ZXJzaW9uIjogIjEuMC4yNyIsCiAgICAibWVtb3J5X3F1ZXJ5X3NlbWFudGljcyI6ICJTTUkgcGh5c2ljYWwgVVVJRC9yb3VuZGVkIG1lbW9yeSBzZXBhcmF0ZSBmcm9tIHRvcmNoIGxvZ2ljYWwgY3VkYTowL3Byb3BlcnRpZXMuIERvIG5vdCBkZW1hbmQgYnl0ZSBlcXVhbGl0eSBiZXR3ZWVuIHRoZSB0d28gaW50ZXJmYWNlczsgcmVxdWlyZSBvbmUgdmlzaWJsZSBsb2dpY2FsIGRldmljZSBtYXBwZWQgdmlhIHRoZSBmaXhlZCBVVUlEIGFuZCByZWNvcmQgdG9yY2ggY2FwYWNpdHkuIgogIH0sCiAgImlubmVyX3JlcXVlc3QiOiB7CiAgICAicGF0aCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfYmx1ZV9ub2lzZV9hYl9mb2xkY19zZWVkMF92MS9jb250cm9sX0V1Y2xpZGVhbl92MS90cmFpbmluZ19lbnRyeV9yZXF1ZXN0X3YxLmpzb24iLAogICAgImJ5dGVzIjogNTY1MSwKICAgICJzaGEyNTYiOiAiY2ZmNzQzMTViZjFlNWNkNGYyZDYyMTcyZjY0NmQ4Y2ViOGM5NDAzMWVlYjczNTk2MTg0ZGFkZjVmYzc5YTgwZCIKICB9LAogICJzY2llbnRpZmljX2NvbmZpZyI6IHsKICAgICJwYXRoIjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9ibHVlX25vaXNlX2FiX2ZvbGRjX3NlZWQwX3YxL2V2aWRlbmNlL3N0YXRpY190cmFpbmluZ19jb25maWdfdjEuanNvbiIsCiAgICAiYnl0ZXMiOiAyMTIwLAogICAgInNoYTI1NiI6ICIxOGFhM2Q5NDFjYTg5NTdmYzFlY2FmYmNkMWEwNTRiNGU2ZWEzMjZkMzY0MWNiNjk1NWJhMjA0NzM2YzRkNzEzIgogIH0sCiAgIm9yZGVyX3BsYW4iOiB7CiAgICAicGF0aCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfYmx1ZV9ub2lzZV9hYl9mb2xkY19zZWVkMF92MS9ldmlkZW5jZS9zaGFyZWRfb3JkZXJfZm9sZENfc2VlZDBfdjEuanNvbiIsCiAgICAiYnl0ZXMiOiAxMjQ4NTA2LAogICAgInNoYTI1NiI6ICI2YWI0MjQxNzdkNTIyN2JkMzQ1ODVhNzEwZWVkY2E1NzhhY2RkMmVlYjIyNmJlYzEwY2RmYzg2ZWU4OWNlYzlkIgogIH0sCiAgInJlc291cmNlX3JlYmluZCI6IHsKICAgICJwYXRoIjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9ibHVlX25vaXNlX2FiX2ZvbGRjX3NlZWQwX3YxL2V2aWRlbmNlL3Jlc291cmNlX2JpbmRpbmdfdjEuanNvbiIsCiAgICAiYnl0ZXMiOiAyMDU5LAogICAgInNoYTI1NiI6ICJlMDMzNjY2ZjA5N2JmYzQ1NzIzN2YzYWUzYzM2ZDgxYWM3M2Q0N2RhMTBkNzM1M2EwYjk4NWZhZjcxZDBlMzYyIgogIH0sCiAgImxvY2FsX1AzIjogewogICAgInBhdGgiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci90aGlyZF9wYXJ0eS9iY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEvZXZpZGVuY2UvbG9jYWxfUDNfdjEuanNvbiIsCiAgICAiYnl0ZXMiOiAxMTMyLAogICAgInNoYTI1NiI6ICJiN2RkOTZmMzhmYzk1MzBiZGIzMTEwZGZiNzc1ZmQ1ZDFjNzkyMzFmYWU0NWYwZjgwZGM2ZDBiOWMyYWI5MDlmIgogIH0sCiAgInRyYWluaW5nX2NvdW50cyI6IHsKICAgICJzb3VyY2VzIjogNjMsCiAgICAiY2FzZXMiOiAzMTUsCiAgICAiaW5wdXQiOiA4MTkyLAogICAgInRhcmdldCI6IDgxOTIsCiAgICAiYmF0Y2giOiA4LAogICAgInRyYXZlcnNhbHMiOiAxMDAsCiAgICAidXBkYXRlcyI6IDM5MDAsCiAgICAiZXhwb3N1cmVzIjogMzEyMDAsCiAgICAiZHJvcHBlZF9leHBvc3VyZXMiOiAzMDAKICB9LAogICJyZXNvdXJjZXNfcGVyX3J1biI6IHsKICAgICJ3YWxsX3NlY29uZHMiOiA4NjQwMCwKICAgICJSU1NfYnl0ZXMiOiA4NTg5OTM0NTkyLAogICAgImRldmljZV9NaUIiOiAyMjUyOCwKICAgICJ0b3JjaF9wZWFrX2J5dGVzIjogMjE0NzQ4MzY0ODAsCiAgICAib3V0cHV0X2J5dGVzIjogMjE0NzQ4MzY0OCwKICAgICJtaW5pbXVtX2ZyZWVfZGlza19ieXRlcyI6IDQyOTQ5NjcyOTYKICB9LAogICJ0cmFuc3BvcnQiOiB7CiAgICAiZmlsZXMiOiBbCiAgICAgIHsKICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXGJsdWVfbm9pc2VfbW9kZWxfcGFpcl9mb2xkQ19zZWVkMF8yMDI2MTEwNF92MVxcZmlyc3RfdHJhaW5pbmdfcmVxdWVzdF92MlxcdHJhbnNwb3J0X3YxXFxiY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEudGFyLmd6IiwKICAgICAgICAiZmlsZW5hbWUiOiAiYmNzcF9ibHVlX25vaXNlX2FiX2ZvbGRjX3NlZWQwX3YxLnRhci5neiIsCiAgICAgICAgImJ5dGVzIjogOTkzNzcxNTUsCiAgICAgICAgInNoYTI1NiI6ICJlNWM0NjE5NWY3NWViNjcyYTY5ZmVhNTg3NjdhMzUyZDE2YzUzNGVjYjViZTIxMGIyNGIwZWFiM2I2ZmYxN2Q0IiwKICAgICAgICAidXBsb2FkX2RpcmVjdG9yeSI6ICIvaG9tZS9qb3Z5YW4iCiAgICAgIH0sCiAgICAgIHsKICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXGJsdWVfbm9pc2VfbW9kZWxfcGFpcl9mb2xkQ19zZWVkMF8yMDI2MTEwNF92MVxcZmlyc3RfdHJhaW5pbmdfcmVxdWVzdF92MlxcdHJhbnNwb3J0X3YxXFxiY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEudGFyLmd6LnNoYTI1NiIsCiAgICAgICAgImZpbGVuYW1lIjogImJjc3BfYmx1ZV9ub2lzZV9hYl9mb2xkY19zZWVkMF92MS50YXIuZ3ouc2hhMjU2IiwKICAgICAgICAiYnl0ZXMiOiAxMDcsCiAgICAgICAgInNoYTI1NiI6ICJlZDVlMzU5YzUwZDNkM2Y2NjdhYjQ5YmY3NDE3MTUzYWE0NzFjOTc1OWUyMTFmNGZjMzc5MTBjMjU0NmU1OWY4IiwKICAgICAgICAidXBsb2FkX2RpcmVjdG9yeSI6ICIvaG9tZS9qb3Z5YW4iCiAgICAgIH0sCiAgICAgIHsKICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXGJsdWVfbm9pc2VfbW9kZWxfcGFpcl9mb2xkQ19zZWVkMF8yMDI2MTEwNF92MVxcZmlyc3RfdHJhaW5pbmdfcmVxdWVzdF92MlxcdHJhbnNwb3J0X3YxXFxiY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEuYnl0ZXMiLAogICAgICAgICJmaWxlbmFtZSI6ICJiY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEuYnl0ZXMiLAogICAgICAgICJieXRlcyI6IDksCiAgICAgICAgInNoYTI1NiI6ICJlYjc3YzMyN2E0N2I5NzcyZGE3MjVkYzQ2Y2I4NmY4ODcwN2Q3ZDBlNTY0NWYzNzhiZGRjZGQ4NDc3OGVhMWI4IiwKICAgICAgICAidXBsb2FkX2RpcmVjdG9yeSI6ICIvaG9tZS9qb3Z5YW4iCiAgICAgIH0sCiAgICAgIHsKICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXGJsdWVfbm9pc2VfbW9kZWxfcGFpcl9mb2xkQ19zZWVkMF8yMDI2MTEwNF92MVxcZmlyc3RfdHJhaW5pbmdfcmVxdWVzdF92MlxcdHJhbnNwb3J0X3YxXFxiY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEuY29udGVudHMuc2hhMjU2IiwKICAgICAgICAiZmlsZW5hbWUiOiAiYmNzcF9ibHVlX25vaXNlX2FiX2ZvbGRjX3NlZWQwX3YxLmNvbnRlbnRzLnNoYTI1NiIsCiAgICAgICAgImJ5dGVzIjogODMxOTYsCiAgICAgICAgInNoYTI1NiI6ICIwOTA5ZDljZjNkYzA5MDMwMzE0MjVkMGY1OTA5MWQzNjU5Y2U2NDU0OGI2Y2I5ZmE2ZjNlNTZiYTEyODk0YmZhIiwKICAgICAgICAidXBsb2FkX2RpcmVjdG9yeSI6ICIvaG9tZS9qb3Z5YW4iCiAgICAgIH0sCiAgICAgIHsKICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXGJsdWVfbm9pc2VfbW9kZWxfcGFpcl9mb2xkQ19zZWVkMF8yMDI2MTEwNF92MVxcZmlyc3RfdHJhaW5pbmdfcmVxdWVzdF92MlxcdHJhbnNwb3J0X3YxXFxiY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEuY29udGVudHMuc2hhMjU2LnNoYTI1NiIsCiAgICAgICAgImZpbGVuYW1lIjogImJjc3BfYmx1ZV9ub2lzZV9hYl9mb2xkY19zZWVkMF92MS5jb250ZW50cy5zaGEyNTYuc2hhMjU2IiwKICAgICAgICAiYnl0ZXMiOiAxMTYsCiAgICAgICAgInNoYTI1NiI6ICI3MjNkZTZhMmQ5OTU0NDIzY2MxYjg3NTllNjVjZDczNjEyZjExODUyNDJlNmI5ODFiMDJlNmVhOWRjZjAyZDllIiwKICAgICAgICAidXBsb2FkX2RpcmVjdG9yeSI6ICIvaG9tZS9qb3Z5YW4iCiAgICAgIH0KICAgIF0sCiAgICAiYXJjaGl2ZV9zaGEyNTYiOiAiZTVjNDYxOTVmNzVlYjY3MmE2OWZlYTU4NzY3YTM1MmQxNmM1MzRlY2I1YmUyMTBiMjRiMGVhYjNiNmZmMTdkNCIsCiAgICAibWVtYmVycyI6IDY1MCwKICAgICJpbnN0YWxsYXRpb25fbWFwcGluZyI6IHsKICAgICAgInBhdGgiOiAiRTpcXENvZGV4XFwyMDI2LTA2LTA2XFxtYW1iYS1jY2YtYy0xLWhpZ2gtcmVzb2x1dGlvblxcb3V0cHV0c1xcY3JhbmlhbF9iY3NwX2dlb3YxXzIwMjYxMDI0XFxibHVlX25vaXNlX21vZGVsX3BhaXJfZm9sZENfc2VlZDBfMjAyNjExMDRfdjFcXGZpcnN0X3RyYWluaW5nX3JlcXVlc3RfdjJcXG5vbl9vdmVyd3JpdGVfaW5zdGFsbGF0aW9uX21hcHBpbmdfdjEuanNvbiIsCiAgICAgICJzaGEyNTYiOiAiMWM1ZmI4ZjBjMjgwMDQ0NGIxNzE4MjFhZThjOTkyNzljNDQ3NzBhMDM5OGM1MGM4YzZlODVkZWExNWNjOTliNSIKICAgIH0KICB9LAogICJmdXR1cmVfcGF0aHMiOiB7CiAgICAiY29udHJvbCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfYmx1ZV9ub2lzZV9hYl9mb2xkY19zZWVkMF92MS9jb250cm9sX0V1Y2xpZGVhbl92MSIsCiAgICAiYXV0aG9yaXphdGlvbiI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfYmx1ZV9ub2lzZV9hYl9mb2xkY19zZWVkMF92MS9jb250cm9sX0V1Y2xpZGVhbl92MS9hdXRob3JpemF0aW9uX3YxLmpzb24iLAogICAgInJ1bnRpbWUiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci90aGlyZF9wYXJ0eS9iY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEvY29udHJvbF9FdWNsaWRlYW5fdjEvcnVudGltZV92MS5qc29uIiwKICAgICJsYXVuY2hlciI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfYmx1ZV9ub2lzZV9hYl9mb2xkY19zZWVkMF92MS9jb250cm9sX0V1Y2xpZGVhbl92MS9sYXVuY2hfb25jZV92MS5zaCIsCiAgICAibGF1bmNoX2F0dGVtcHQiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci90aGlyZF9wYXJ0eS9iY3NwX2JsdWVfbm9pc2VfYWJfZm9sZGNfc2VlZDBfdjEvY29udHJvbF9FdWNsaWRlYW5fdjEvbGF1bmNoX2F0dGVtcHRfdjEuanNvbiIsCiAgICAib3V0cHV0IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvbG9ncy9jcmFuaWFsX2Jjc3BfYmx1ZV9ub2lzZV9hYl92MS9iY3NwX2JsdWVfbm9pc2VfZm9sZENfRXVjbGlkZWFuX2VsaW1pbmF0aW9uX2luODE5Ml9vdXQ4MTkyX3NlZWQwX3RyYWluX3YxIiwKICAgICJsb2ciOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci9sb2dzL2NyYW5pYWxfYmNzcF9ibHVlX25vaXNlX2FiX3YxL2Jjc3BfYmx1ZV9ub2lzZV9mb2xkQ19FdWNsaWRlYW5fZWxpbWluYXRpb25faW44MTkyX291dDgxOTJfc2VlZDBfdHJhaW5fdjEvbGF1bmNoLmxvZyIsCiAgICAiUElEIjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvbG9ncy9jcmFuaWFsX2Jjc3BfYmx1ZV9ub2lzZV9hYl92MS9iY3NwX2JsdWVfbm9pc2VfZm9sZENfRXVjbGlkZWFuX2VsaW1pbmF0aW9uX2luODE5Ml9vdXQ4MTkyX3NlZWQwX3RyYWluX3YxL3dvcmtlci5waWQiLAogICAgImV4aXRfY29kZSI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL2xvZ3MvY3JhbmlhbF9iY3NwX2JsdWVfbm9pc2VfYWJfdjEvYmNzcF9ibHVlX25vaXNlX2ZvbGRDX0V1Y2xpZGVhbl9lbGltaW5hdGlvbl9pbjgxOTJfb3V0ODE5Ml9zZWVkMF90cmFpbl92MS9leGl0X2NvZGUudHh0IiwKICAgICJjaGVja3BvaW50IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvbG9ncy9jcmFuaWFsX2Jjc3BfYmx1ZV9ub2lzZV9hYl92MS9iY3NwX2JsdWVfbm9pc2VfZm9sZENfRXVjbGlkZWFuX2VsaW1pbmF0aW9uX2luODE5Ml9vdXQ4MTkyX3NlZWQwX3RyYWluX3YxL2NrcHQtbGFzdC5wdGgiLAogICAgImNvbXBsZXRpb24iOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci9sb2dzL2NyYW5pYWxfYmNzcF9ibHVlX25vaXNlX2FiX3YxL2Jjc3BfYmx1ZV9ub2lzZV9mb2xkQ19FdWNsaWRlYW5fZWxpbWluYXRpb25faW44MTkyX291dDgxOTJfc2VlZDBfdHJhaW5fdjEvY29tcGxldGlvbi5qc29uIiwKICAgICJ0bXV4IjogImJjc3BfYmx1ZV9ub2lzZV9mb2xkY19ldWNsaWRlYW5fc2VlZDBfdHJhaW5fdjEiCiAgfSwKICAibGF1bmNoZXJfY29udHJhY3QiOiB7CiAgICAiZW52aXJvbm1lbnQiOiB7CiAgICAgICJDVURBX1ZJU0lCTEVfREVWSUNFUyI6ICJHUFUtMzRhMWI5OTYtMmJkNy04OGU2LTlkY2EtMTY0YjcxOGNhZWE2IiwKICAgICAgIkNVQkxBU19XT1JLU1BBQ0VfQ09ORklHIjogIjo0MDk2OjgiLAogICAgICAiT01QX05VTV9USFJFQURTIjogIjIiLAogICAgICAiTUtMX05VTV9USFJFQURTIjogIjIiLAogICAgICAiT1BFTkJMQVNfTlVNX1RIUkVBRFMiOiAiMiIsCiAgICAgICJQWVRIT05ET05UV1JJVEVCWVRFQ09ERSI6ICIxIiwKICAgICAgIk1QTEJBQ0tFTkQiOiAiQWdnIiwKICAgICAgIk1QTENPTkZJR0RJUiI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL2xvZ3MvY3JhbmlhbF9iY3NwX2JsdWVfbm9pc2VfYWJfdjEvYmNzcF9ibHVlX25vaXNlX2ZvbGRDX0V1Y2xpZGVhbl9lbGltaW5hdGlvbl9pbjgxOTJfb3V0ODE5Ml9zZWVkMF90cmFpbl92MS9tcGxjb25maWciLAogICAgICAiQ1VEQV9DQUNIRV9ESVNBQkxFIjogIjEiLAogICAgICAiVE1QRElSIjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvbG9ncy9jcmFuaWFsX2Jjc3BfYmx1ZV9ub2lzZV9hYl92MS9iY3NwX2JsdWVfbm9pc2VfZm9sZENfRXVjbGlkZWFuX2VsaW1pbmF0aW9uX2luODE5Ml9vdXQ4MTkyX3NlZWQwX3RyYWluX3YxL3RtcCIKICAgIH0sCiAgICAicHl0aG9uIjogIi9vcHQvY29uZGEvZW52cy9hZGFwb2ludHItbWFtYmEvYmluL3B5dGhvbjMuMTAiLAogICAgImZsYWdzIjogWwogICAgICAiLUkiLAogICAgICAiLVMiLAogICAgICAiLUIiCiAgICBdLAogICAgImVudHJ5IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9ibHVlX25vaXNlX2FiX2ZvbGRjX3NlZWQwX3YxL2ltcGxlbWVudGF0aW9uL2Jjc3BfYmx1ZV9ub2lzZV90cmFpbmluZ19lbnRyeV92MS5weSIsCiAgICAiZW50cnlfc2hhMjU2IjogIjlhZjEyZjQxYzI5ZmNhZDU0MzU4ZmJhZDM0NDE0YzA5NjZkMTI4OWZkY2E0ZDUwYzZlMWM0Y2YzZWQwYTU0YjEiLAogICAgImV4dGVybmFsX3RpbWVvdXRfc2Vjb25kcyI6IDg2NDAwLAogICAgImtpbGxfYWZ0ZXJfc2Vjb25kcyI6IDUsCiAgICAidHJhbnNwb3J0IjogIm9yaWdpbmFsIGZpbGUgYnl0ZXMgQmFzZTY0IHdpdGggYnl0ZS9TSEEyNTYgdmVyaWZpY2F0aW9uOyByYXcgc3Rkb3V0L3N0ZGVyciBjYXB0dXJlOyB1c2UgV1NMIC0tZXhlYzsgUG93ZXJTaGVsbCBwcm9wYWdhdGVzIExBU1RFWElUQ09ERSIsCiAgICAib3JkZXIiOiAicmVjaGVjayB1cGxvYWQvc291cmNlL3Jlc291cmNlL2Fic2VuY2UgZ2F0ZXM7IHZhbGlkYXRlIGFuZCBjcmVhdGUgbG9nIHBhcmVudHMgYmVmb3JlIHJlZGlyZWN0aW9uOyBvbmUtd2F5IGF1dGhvcml6YXRpb24gdGhlbiBydW50aW1lOyBjbGFpbSBleGNsdXNpdmUgYXR0ZW1wdCBiZWZvcmUgZXhhY3RseSBvbmUgZml4ZWQgdG11eCBsYXVuY2giLAogICAgIm9uZV93YXlfbWF0ZXJpYWxpemF0aW9uIjogImlubmVyL2Z1bGwgcmVxdWVzdCBoYXNoZXMgLT4gZXhwbGljaXQgYXV0aG9yaXphdGlvbiAtPiBhdXRob3JpemF0aW9uIFNIQTI1NiAtPiBydW50aW1lIC0+IGxhdW5jaGVyOyBubyByZXZlcnNlIHJ1bnRpbWUgaGFzaCBpbiBhdXRob3JpemF0aW9uIgogIH0sCiAgInNjaWVudGlmaWNfcmlza19kaXNjbG9zdXJlIjogWwogICAgIlJlYWQtb25seSBzb3VyY2UgbWF0Y2ggaXMgbm90IGN1cnJlbnQgQ1VEQSBjZXJ0aWZpY2F0aW9uOyBwcmlvciBHUFUgZXZpZGVuY2UgcmV0YWluZWQgd2l0aG91dCByZXBlYXRlZCBwcmVmbGlnaHQiLAogICAgIkNQVSBtZXRhZGF0YSBhbmQgUkFNIGdyYW50IGNoZWNrcyBkbyBub3QgZXhlY3V0ZSBhY3R1YWwgbW9kZWwgaW5pdGlhbGl6YXRpb24vb3B0aW1pemVyIiwKICAgICJSZXNvdXJjZSBtb25pdG9yaW5nIHdpdGggdW5jaGFuZ2VkIHRocmVzaG9sZHM7IG5vIGRlZGljYXRlZCBjZ3JvdXAgb3Igc3RyaWN0IFNNSS1QSUQgb3duZXJzaGlwIiwKICAgICJTZXJ2ZXIgaXMgbm90IGEgR2l0IGNoZWNrb3V0OyBhbGwzMCBleGFjdCBzZWxlY3RlZCBzb3VyY2UvcHJvdmlkZXIvZW52aXJvbm1lbnQgYXNzZXRzIG1hdGNoZWQiLAogICAgIlNhbXBsaW5nIGhhcyBleHBsb3JhdG9yeSBnZW9tZXRyeSBldmlkZW5jZSBvbmx5OyBubyBtb2RlbCBhY2N1cmFjeSBiZW5lZml0IGNsYWltZWQiCiAgXSwKICAiY29tcGxldGlvbl9ib3VuZGFyeSI6ICJTdG9wIGFmdGVyIHRoZSBvbmUgRXVjbGlkZWFuIGF0dGVtcHQuIEluZGVwZW5kZW50IHBvc3QtdHJhaW5pbmcgZnJlZXplIGF1ZGl0IGFuZCBiYXNlbGluZSBpbml0aWFsaXphdGlvbiBldmlkZW5jZSByZXF1aXJlZCBiZWZvcmUgYSBzZXBhcmF0ZWx5IGF1dGhvcml6ZWQgZ3JhcGggcmVxdWVzdC4iLAogICJmb3JiaWRkZW4iOiBbCiAgICAibm8gZ3JhcGggb3IgZXh0cmEgdHJhaW5pbmciLAogICAgIm5vIGRldmVsb3BtZW50IHBheWxvYWQvZXZhbHVhdGlvbiIsCiAgICAibm8gQk5DYWwiLAogICAgIm5vIEZvbGREL1NrdWxsRml4L01VRy9NYW1iYSBjaGFuZ2VzIiwKICAgICJubyByZXN1bWUgb3IgYXV0b21hdGljIHJldHJ5IiwKICAgICJubyBkZXBlbmRlbmN5IGRvd25sb2FkL2J1aWxkL2luc3RhbGwgb3IgZW52aXJvbm1lbnQgdXBncmFkZTsgbm8gZnJvemVuIG1vZGVsL3Byb3ZpZGVyIHNvdXJjZSBjaGFuZ2VzIiwKICAgICJubyBvbGQtZmlsZSBvdmVyd3JpdGUvZGVsZXRlIiwKICAgICJubyB1c2Ugb2YgcHJvdmVuYW5jZSBXaW5kb3dzIHBhdGhzIGluIHNlcnZlciBjb21tYW5kcyIKICBdCn0=')
EXPECTED_CONTROL=[{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_blue_noise_ab_foldc_seed0_v1/control_Euclidean_v1/training_entry_request_v1.json', 'bytes': 5651, 'sha256': 'cff74315bf1e5cd4f2d62172f646d8ceb8c94031eeb73596184dadf5fc79a80d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_blue_noise_ab_foldc_seed0_v1/control_Euclidean_v1/authorization_v1.json', 'bytes': 592, 'sha256': '831ef816fbb5d01eb82432752f4b5ad9d4dbf139768bb67374e10a0354324e16'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_blue_noise_ab_foldc_seed0_v1/control_Euclidean_v1/runtime_v1.json', 'bytes': 224, 'sha256': '94fba9010f6247028797f355c0d79537031f2cc8a3376a406e7831b059d5e665'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_blue_noise_ab_foldc_seed0_v1/control_Euclidean_v1/launch_once_v1.sh', 'bytes': 2030, 'sha256': 'ab244d32b6b7aac8d8489772a5d6c1e96fee332f0fcf911765acae60d7d48798'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_blue_noise_ab_foldc_seed0_v1/control_Euclidean_v1/launch_attempt_v1.json', 'bytes': 384, 'sha256': 'f755f55a98597eab6b51048723943ee8ba54e3b8259f7e5561781c9f42d6a403'}]
START=time.monotonic();TOTAL=0;cache={};checks={};rows=[];READ_STAMPS={}
ROOT=Path('/home/jovyan/adapointr_work/PoinTr')
CODE=ROOT/'third_party/bcsp_blue_noise_ab_foldc_seed0_v1'
CONTROL=CODE/'control_Euclidean_v1'
OUT=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_noise_foldC_Euclidean_elimination_in8192_out8192_seed0_train_v1')
SCOPE='40a45089ed847261d9477993118b406048dadd09d15e492a402b455bddfdad74'

def need(ok,message):
 if not ok:raise ValueError(message)
def check(name,ok):
 checks[name]=bool(ok);need(ok,name)
def stamp(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns)
def parents(p):
 for a in p.parents:need(stat.S_ISDIR(a.lstat().st_mode),'linked/non-directory parent: '+str(a))
def read(p,binding=None,checkpoint=False):
 global TOTAL
 p=Path(p)
 special_python=str(p)=='/opt/conda/envs/adapointr-mamba/bin/python3.10'
 if special_python:need(binding is not None and binding['bytes']==17331920 and binding['sha256']=='01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d','exact frozen Python binary binding')
 if str(p) in cache:
  value=cache[str(p)]
  if binding:need(value[0]['bytes']==binding['bytes'] and value[0]['sha256']==binding['sha256'],'cached binding mismatch: '+str(p))
  return value
 parents(p);st=p.lstat();need(stat.S_ISREG(st.st_mode),'nonregular: '+str(p))
 if special_python:need(st.st_size==17331920,'exact frozen Python binary size')
 limit=17331920 if special_python else (536870912 if checkpoint else 16777216)
 need(st.st_size<=limit and TOTAL+st.st_size<=805306368,'read byte budget: '+str(p))
 digest=hashlib.sha256();parts=[]
 with p.open('rb') as f:
  while True:
   data=f.read(1048576)
   if not data:break
   TOTAL+=len(data);need(TOTAL<=805306368 and time.monotonic()-START<120,'audit byte/time budget')
   digest.update(data)
   if not checkpoint:parts.append(data)
 need(stamp(st)==stamp(p.lstat()),'file changed while hashing: '+str(p))
 row=dict(path=str(p),bytes=st.st_size,sha256=digest.hexdigest(),uid=st.st_uid,mode=oct(stat.S_IMODE(st.st_mode)),mtime_ns=st.st_mtime_ns,inode=st.st_ino)
 if binding:need(row['bytes']==binding['bytes'] and row['sha256']==binding['sha256'],'binding mismatch: '+str(p))
 need(len(rows)<512,'bounded exact file count');READ_STAMPS[str(p)]=stamp(st);rows.append(row);value=(row,b''.join(parts) if not checkpoint else None)
 cache[str(p)]=value;return value
def js(p,binding=None):return json.loads(read(p,binding)[1])
def canonical(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def tree():
 found={}
 for p in [OUT,*OUT.rglob('*')]:
  need(len(found)<32,'inventory entry cap');s=p.lstat()
  need(stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode),'linked/special output: '+str(p))
  found[str(p)]=stamp(s)
 return found
EXPECTED_INITIALIZATION={'parameter_sha256': 'c864e2f77fc7c5999cf1df615ed720f4fc10ae0a6d19888e28e5058879f70a99', 'persistent_state_sha256': '9649b96c1f1287fa7d5670815b3e48798ab1a3883bb200f5a9db027980852f37', 'order_sha256': '349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f', 'seed': 0}
try:
 check('current_hostname_uid',socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000)
 parents(OUT);before=tree()
 names={'ckpt-last.pth','completion.json','exit_code.txt','exposure.json','initialization.json','launch.log','metrics.jsonl','optimizer_actual_defaults.json','order_plan.json','resources.jsonl','worker.pid'}
 check('exact_output_file_set',{p.name for p in OUT.iterdir() if p.is_file()}==names)
 check('exact_output_directory_set',{p.name for p in OUT.iterdir() if p.is_dir()}=={'tmp'} and not list((OUT/'tmp').iterdir()))
 for name in sorted(names):read(OUT/name,checkpoint=name=='ckpt-last.pth')
 scope=json.loads(SCOPE_RAW)
 check('full_authorized_execution_scope_hash',hashlib.sha256(SCOPE_RAW).hexdigest()==SCOPE)
 check('exact_control_file_set',{p.name for p in CONTROL.iterdir()}=={'training_entry_request_v1.json','authorization_v1.json','runtime_v1.json','launch_once_v1.sh','launch_attempt_v1.json'})
 for r in EXPECTED_CONTROL:read(r['path'],r)
 check('five_controls_match_authorized_materialization',len(EXPECTED_CONTROL)==5)
 q=js(CONTROL/'training_entry_request_v1.json');qhash=cache[str(CONTROL/'training_entry_request_v1.json')][0]['sha256']
 check('inner_request_hash',qhash==scope['inner_request']['sha256'])
 auth=js(CONTROL/'authorization_v1.json');runtime=js(CONTROL/'runtime_v1.json')
 check('one_way_authorization_runtime',auth['explicit_user_authorization'] is True and auth['request_sha256']==qhash and SCOPE in auth['user_authorization_text'] and runtime==dict(schema='bcsp-training-runtime-v1',request_sha256=qhash,authorization_sha256=cache[str(CONTROL/'authorization_v1.json')][0]['sha256']))
 check('single_attempt_claim',js(CONTROL/'launch_attempt_v1.json')['request_sha256']==qhash)
 pins=[q['static_config'],q['order_plan'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),q['QC']['verification'],q['QC']['qualified_receipt'],q['resource_rebind'],q['preflight_scope'],q['GPU_audit'],*q['implementation'].values()]
 for r in pins:read(r['path'],r)
 static=js(q['static_config']['path']);plan=js(OUT/'order_plan.json');complete=js(OUT/'completion.json');exposure=js(OUT/'exposure.json')
 check('exit_code_zero',read(OUT/'exit_code.txt')[1].strip()==b'0')
 tm=subprocess.run(['/usr/bin/tmux','has-session','-t',scope['future_paths']['tmux']],capture_output=True,timeout=5)
 check('fixed_tmux_absent',tm.returncode==1)
 pid=int(read(OUT/'worker.pid')[1]);check('worker_not_live',not Path('/proc/'+str(pid)).exists())
 check('frozen_order_bytes',read(OUT/'order_plan.json')[0]['sha256']==q['order_plan']['sha256'])
 order_hash=canonical(plan)
 check('order_canonical_binding',complete['order_sha256']==exposure['order_sha256']==js(OUT/'initialization.json')['order_sha256']==order_hash)
 check('correct_sampling_stage',q['stage']==complete['stage']=='BCSP_BLUE_NOISE_AB_V1' and q['arm']=='Euclidean_elimination' and q['paired_initialization'] is None)
 check('completion_exact_counts',complete['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100))
 check('completion_update_traversal_exposure',complete['optimizer_updates']==3900 and complete['traversals']==100 and complete['case_exposures']==31200)
 check('BNCal_evaluation_resume_false',all(complete[k] is False for k in ['bncal_executed','evaluation_executed','resume']))
 checkpoint=read(OUT/'ckpt-last.pth',checkpoint=True)[0]
 check('checkpoint_SHA256_matches_completion',checkpoint['sha256']==complete['checkpoint_sha256'])
 fold=js(q['QC']['fold_binding']['path'])['folds']['C']
 manifest={x['case_id']:x for x in map(json.loads,read(q['QC']['manifests']['Euclidean_elimination']['path'])[1].decode().splitlines())}
 check('fixed315_train_allowlist',len(fold['train_case_ids'])==315 and plan['case_ids']==fold['train_case_ids'] and len(fold['train_sources'])==63 and not set(fold['train_sources'])&set(fold['dev_sources']))
 metrics=list(map(json.loads,read(OUT/'metrics.jsonl')[1].decode().splitlines()))
 check('3900_metric_records',len(metrics)==3900)
 case=Counter();source=Counter();drops=Counter();index=0;losses=[]
 for e,row in enumerate(plan['epochs']):
  need(row['epoch']==e and len(row['batches'])==39 and len(row['dropped'])==3,'order dimensions')
  for b,batch in enumerate(row['batches']):
   m=metrics[index];index+=1
   need(m['step']==index and m['epoch']==e and m['batch']==b and m['case_ids']==batch and len(batch)==8,'actual step/epoch/batch/order')
   ss=[manifest[c]['source_id'] for c in batch]
   need(m['source_ids']==ss and set(batch)<=set(fold['train_case_ids']),'actual sources/allowlist')
   need(m['optimizer_step_committed'] is True and m['clip_max_norm']==10,'commit/clip')
   need(all(math.isfinite(m[k]) for k in ['loss','loss_sparse','loss_dense','grad_norm_before_clip']),'finite numeric event')
   need(math.isclose(m['loss'],m['loss_sparse']+m['loss_dense'],rel_tol=1e-6,abs_tol=1e-7),'loss sum')
   need(len(m['LR'])==2 and all(math.isclose(v,.0001*max(.9**(e/21),.02),rel_tol=1e-12) for v in m['LR']),'LR schedule')
   need(math.isclose(m['BN_momentum'],max(.9*.5**(e/21),.01),rel_tol=1e-12),'BN momentum')
   case.update(batch);source.update(ss);losses.append(m['loss'])
  drops.update(row['dropped'])
 check('full_actual_order_numeric_LR_BN_contract',index==3900)
 check('exposure_counters_match',dict(case)==exposure['case'] and dict(source)==exposure['source'] and dict(drops)==exposure['dropped_case'])
 check('31200_exposures_300_drops',sum(case.values())==sum(source.values())==31200 and sum(drops.values())==300)
 resources=list(map(json.loads,read(OUT/'resources.jsonl')[1].decode().splitlines()))
 check('3902_resource_records',len(resources)==3902)
 for i,r in enumerate(resources):
  need((r['phase'],r['committed_step'])==(('after_step',i+1) if i<3900 else ('before_final' if i==3900 else 'after_final',3900)),'resource sequence')
  need(r['limits']==static['resources'] and r['resource_guard_passed'] is True and not r['failed_checks'] and set(r['checks'])=={'allocated_within_limit','reserved_within_limit','device_within_limit'} and all(r['checks'].values()),'resource verdict')
  need(r['peak_allocated']<=21474836480 and r['peak_reserved']<=21474836480 and r['device_MiB']<=22528 and r['RSS']<=8589934592 and r['output_bytes']<=2147483648 and r['elapsed_seconds']<=86400,'resource ceilings')
  need(r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE' and r['own_PID']==pid,'PID diagnostic contract')
 check('all_recorded_resources_pass',True)
 initialization=js(OUT/'initialization.json')
 check('recorded_initialization_seed_and_fingerprints',initialization['seed']==0 and all(isinstance(initialization[k],str) and len(initialization[k])==64 and all(c in '0123456789abcdef' for c in initialization[k]) for k in ['parameter_sha256','persistent_state_sha256']))
 defaults=js(OUT/'optimizer_actual_defaults.json')
 check('recorded_optimizer_defaults',defaults['lr']==.0001 and defaults['betas']==[.9,.999] and defaults['eps']==1e-8 and defaults['amsgrad'] is False)
 rebind=js(q['resource_rebind']['path'])
 for key in ['readonly_identity','readonly_assets']:read(rebind[key]['path'],rebind[key])
 assets=js(rebind['readonly_assets']['path'])
 check('exact30_source_provider_asset_record',assets['status']=='SELECTED30_HASH_PASS' and len(assets['assets'])==30)
 for r in assets['assets']:read(r['path'],r)
 qualified=js(q['QC']['qualified_receipt']['path'])
 check('qualified_Euclidean_arm',qualified['schema']=='bcsp-blue-noise-qualified-v1' and qualified['stage']=='BCSP_BLUE_NOISE_AB_V1' and qualified['arm']=='Euclidean_elimination')
 check('fresh_scratch_no_parent_weights',q['paired_initialization'] is None and static['training']['seed']==0 and static['training']['checkpoint']=='scratch_final_only')
 check('recorded_initialization_matches_same_model_seed0_reference',initialization==EXPECTED_INITIALIZATION)
 payload_bytes=0
 for cid,row in manifest.items():
  need(row['comparison_stage']=='BCSP_BLUE_NOISE_AB_V1' and row['comparison_split']=='train' and row['sampler_arm']=='Euclidean_elimination' and row['sampling_seed']==0,'active sampler scope')
  rel=Path(row['point_path']);need(not rel.is_absolute() and '..' not in rel.parts,'relative payload path')
  rec,_=read(Path(q['data_root'])/rel);need(rec['sha256']==row['sha256'],'active NPZ hash');payload_bytes+=rec['bytes']
 check('active315_stream_hashes_match_frozen_manifest',len(manifest)==315)
 other={x['case_id']:x for x in map(json.loads,read(q['QC']['manifests']['surface_graph']['path'])[1].decode().splitlines())}
 need(len(other)==315 and set(other)==set(manifest),'paired metadata IDs')
 for cid,a in manifest.items():
  b=other[cid];need(all(a[k]==b[k] for k in ['case_id','source_id','target_array_sha256','normalization','common_point_order_sha256']),'paired metadata target/frame/order')
 check('paired_metadata_targets_frame_point_order_equal',True)
 check('scientific_static_counts',static['stage']=='BCSP_BLUE_NOISE_AB_V1' and static['counts']==dict(cases=315,sources=63,batch=8,epochs=100,batches_per_epoch=39,updates=3900,exposures=31200))
 gpu=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,timeout=10)
 need(gpu.returncode==0,'current GPU metadata query')
 observed=[s.strip() for s in gpu.stdout.decode().strip().split(',')]
 check('same_gpu_identity_for_future_paired_request',observed[:4]==[q['identity']['gpu_uuid'],q['identity']['gpu_name'],q['identity']['driver_version'],str(q['identity']['nvidia_smi_memory_total_MiB'])])
 check('all_hashed_files_stable_atime_excluded',all(stamp(Path(p).lstat())==record for p,record in READ_STAMPS.items()))
 check('result_tree_stable_atime_excluded',tree()==before)
 check('no_failure_markers',not (OUT/'failure.json').exists() and not (OUT/'startup_failure.json').exists())
 print(json.dumps(dict(status='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS',checks=checks,completion=complete,checkpoint=checkpoint,output_manifest=[r for r in rows if str(OUT)+'/' in r['path']],all_bound_files=[r for r in rows if not r['path'].endswith('.npz')],initialization=initialization,optimizer_defaults=defaults,active_training_data=dict(files=315,stream_hashed_bytes=payload_bytes,NPZ_decoded=False),paired_graph_metadata_only=True,graph_payloads_read=False,current_GPU_metadata=observed,
 counts=dict(metric_records=len(metrics),epochs=100,updates=3900,case_exposures=sum(case.values()),dropped_exposures=sum(drops.values()),resource_records=len(resources)),
 resource_summary=dict(peak_allocated=max(r['peak_allocated'] for r in resources),peak_reserved=max(r['peak_reserved'] for r in resources),device_peak_MiB=max(r['device_MiB'] for r in resources),RSS_peak=max(r['RSS'] for r in resources),PID_warning_records=sum(bool(r['PID_warning']) for r in resources)),
 loss_summary=dict(first=losses[0],last=losses[-1],last_epoch_mean=sum(losses[-39:])/39,interpretation='Training loss only;not development or clinical performance'),
 exact_source_runtime_binding_verified=True,checkpoint_loaded=False,checkpoint_stream_hashed=True,initialization_weights_reconstructed=False,NPZ_decoded=False,model_imported=False,forward_calls=0,server_writes=0,hashed_bytes=TOTAL,elapsed_seconds=time.monotonic()-START,
 limitations=['Forward/backward/scheduler counters are corroborated by pinned runtime and completion; no independent GPU trace','No strict GPU process ownership guarantee by approved policy','BNCal/evaluation false is supported by pinned execution path and completion flags; no independent OS-wide file-access trace'])),flush=True)
except BaseException as exc:
 print(json.dumps(dict(status='AUDIT_FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks,all_bound_files=[r for r in rows if not r['path'].endswith('.npz')],server_writes=0,checkpoint_loaded=False,forward_calls=0)),flush=True)
 raise
