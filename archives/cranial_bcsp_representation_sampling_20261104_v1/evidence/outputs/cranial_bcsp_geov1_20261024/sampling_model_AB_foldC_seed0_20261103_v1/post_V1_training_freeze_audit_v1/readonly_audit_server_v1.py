"""Read-only stdlib audit of this one finished training attempt; no model imports."""
import os,socket,json,hashlib,stat,time,math,subprocess
from pathlib import Path
from collections import Counter
import base64
SCOPE_RAW=base64.b64decode('ew0KICAic2NoZW1hIjogImJjc3Atc2FtcGxpbmctZmlyc3QtbW9kZWwtZXhlY3V0aW9uLXNjb3BlLXYxIiwNCiAgInN0YXR1cyI6ICJBV0FJVElOR19FWFBMSUNJVF9VU0VSX0FVVEhPUklaQVRJT04iLA0KICAiZXhlY3V0aW9uX2F1dGhvcml6ZWQiOiBmYWxzZSwNCiAgInN0YWdlIjogIkJDU1BfU0FNUExJTkdfQUJfVjEiLA0KICAic2NvcGUiOiAiYWZ0ZXIgdXNlciB1cGxvYWQ6IGV4YWN0IG5vbi1vdmVyd3JpdGUgaW5zdGFsbGF0aW9uIG9mIHBhaXJlZCBkYXRhIGFuZCBmb3VyIGltcGxlbWVudGF0aW9uIGZpbGVzLCB0aGVuIG9uZSBmcmVzaCBWMSBGb2xkQyBzZWVkMCB0cmFpbmluZyBvbmx5IiwNCiAgInJ1bl9pZCI6ICJiY3NwX3NhbXBsaW5nX2FiX2ZvbGRDX1YxX2luODE5Ml9vdXQ4MTkyX3NlZWQwX3RyYWluX3YxIiwNCiAgInRyYWluaW5nX3J1bnNfYXV0aG9yaXplZF9ieV90aGlzX3BlbmRpbmdfc2NvcGUiOiAxLA0KICAicGxhbm5lZF9wYWlyX3RvdGFsX3J1bnMiOiAyLA0KICAiY2FuZGlkYXRlX3RyYWluaW5nX2F1dGhvcml6ZWQiOiBmYWxzZSwNCiAgImlkZW50aXR5Ijogew0KICAgICJob3N0bmFtZSI6ICJzaHUtY29tbW9uLTI1NzIxNDUyLW5vdGVib29rLXYyaXdzYS0wIiwNCiAgICAidWlkIjogMTAwMCwNCiAgICAicHJvamVjdCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyIiwNCiAgICAiZ3B1X3V1aWQiOiAiR1BVLTM0YTFiOTk2LTJiZDctODhlNi05ZGNhLTE2NGI3MThjYWVhNiIsDQogICAgImdwdV9uYW1lIjogIk5WSURJQSBHZUZvcmNlIFJUWCA0MDkwIEQiLA0KICAgICJkcml2ZXJfdmVyc2lvbiI6ICI1NzAuMTkwIiwNCiAgICAibnZpZGlhX3NtaV9tZW1vcnlfdG90YWxfTWlCIjogMjQ1NjQsDQogICAgInB5dGhvbl9yZWFscGF0aCI6ICIvb3B0L2NvbmRhL2VudnMvYWRhcG9pbnRyLW1hbWJhL2Jpbi9weXRob24zLjEwIiwNCiAgICAicHl0aG9uX3ZlcnNpb24iOiAiMy4xMC4yMCIsDQogICAgInRvcmNoX3ZlcnNpb24iOiAiMi40LjErY3UxMTgiLA0KICAgICJudW1weV92ZXJzaW9uIjogIjIuMi42IiwNCiAgICAidGltbV92ZXJzaW9uIjogIjEuMC4yNyIsDQogICAgIm1lbW9yeV9xdWVyeV9zZW1hbnRpY3MiOiAiU01JIHBoeXNpY2FsIFVVSUQvcm91bmRlZCBtZW1vcnkgc2VwYXJhdGUgZnJvbSB0b3JjaCBsb2dpY2FsIGN1ZGE6MC9wcm9wZXJ0aWVzLiBEbyBub3QgZGVtYW5kIGJ5dGUgZXF1YWxpdHkgYmV0d2VlbiB0aGUgdHdvIGludGVyZmFjZXM7IHJlcXVpcmUgb25lIHZpc2libGUgbG9naWNhbCBkZXZpY2UgbWFwcGVkIHZpYSB0aGUgZml4ZWQgVVVJRCBhbmQgcmVjb3JkIHRvcmNoIGNhcGFjaXR5LiINCiAgfSwNCiAgImlubmVyX3JlcXVlc3QiOiB7DQogICAgInBhdGgiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci90aGlyZF9wYXJ0eS9iY3NwX3NhbXBsaW5nX2FiX2ZvbGRjX3NlZWQwX3YxL2NvbnRyb2xfVjFfdjEvdHJhaW5pbmdfZW50cnlfcmVxdWVzdF92MS5qc29uIiwNCiAgICAiYnl0ZXMiOiA1NjE0LA0KICAgICJzaGEyNTYiOiAiYTNhMjg3MDI0OGU3YTA3NTkzNjJmNmRlYzMzN2NlNjc2OGU4ZWRmYWJiNTg1ZThkNjNkZWYxZWQzYTkwYTY4MCINCiAgfSwNCiAgInNjaWVudGlmaWNfY29uZmlnIjogew0KICAgICJwYXRoIjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9zYW1wbGluZ19hYl9mb2xkY19zZWVkMF92MS9ldmlkZW5jZS9zdGF0aWNfdHJhaW5pbmdfY29uZmlnX3YxLmpzb24iLA0KICAgICJieXRlcyI6IDIxMTgsDQogICAgInNoYTI1NiI6ICJlMGVjNTljMjBmZGJjOWEwODA5NTMyMjMzNzYwYTViNGFjMWMxMTZmNmY0ZTgzMTU5NDhlZjkxN2UwNzgxMzZhIg0KICB9LA0KICAib3JkZXJfcGxhbiI6IHsNCiAgICAicGF0aCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEvZXZpZGVuY2Uvc2hhcmVkX29yZGVyX2ZvbGRDX3NlZWQwX3YxLmpzb24iLA0KICAgICJieXRlcyI6IDEyNDg1MDYsDQogICAgInNoYTI1NiI6ICI2YWI0MjQxNzdkNTIyN2JkMzQ1ODVhNzEwZWVkY2E1NzhhY2RkMmVlYjIyNmJlYzEwY2RmYzg2ZWU4OWNlYzlkIg0KICB9LA0KICAibG9jYWxfUDMiOiB7DQogICAgInBhdGgiOiAiRTpcXENvZGV4XFwyMDI2LTA2LTA2XFxtYW1iYS1jY2YtYy0xLWhpZ2gtcmVzb2x1dGlvblxcb3V0cHV0c1xcY3JhbmlhbF9iY3NwX2dlb3YxXzIwMjYxMDI0XFxzYW1wbGluZ19tb2RlbF9BQl9mb2xkQ19zZWVkMF8yMDI2MTEwM192MVxcbG9jYWxfUDNfdjEuanNvbiIsDQogICAgInNoYTI1NiI6ICI5NjE2ZjhkYzZiMzE3ZGM5YjlhMjFmOWY4N2EwNjRlZGJjY2NiOGFkMmJhNTdmZTM4ODU0ZjQ3ZWZhMTA5YzIyIg0KICB9LA0KICAidHJhaW5pbmdfY291bnRzIjogew0KICAgICJzb3VyY2VzIjogNjMsDQogICAgImNhc2VzIjogMzE1LA0KICAgICJpbnB1dCI6IDgxOTIsDQogICAgInRhcmdldCI6IDgxOTIsDQogICAgImJhdGNoIjogOCwNCiAgICAidHJhdmVyc2FscyI6IDEwMCwNCiAgICAidXBkYXRlcyI6IDM5MDAsDQogICAgImV4cG9zdXJlcyI6IDMxMjAwLA0KICAgICJkcm9wcGVkX2V4cG9zdXJlcyI6IDMwMA0KICB9LA0KICAicmVzb3VyY2VzX3Blcl9ydW4iOiB7DQogICAgIndhbGxfc2Vjb25kcyI6IDg2NDAwLA0KICAgICJSU1NfYnl0ZXMiOiA4NTg5OTM0NTkyLA0KICAgICJkZXZpY2VfTWlCIjogMjI1MjgsDQogICAgInRvcmNoX3BlYWtfYnl0ZXMiOiAyMTQ3NDgzNjQ4MCwNCiAgICAib3V0cHV0X2J5dGVzIjogMjE0NzQ4MzY0OCwNCiAgICAibWluaW11bV9mcmVlX2Rpc2tfYnl0ZXMiOiA0Mjk0OTY3Mjk2DQogIH0sDQogICJ0cmFuc3BvcnQiOiB7DQogICAgImZpbGVzIjogWw0KICAgICAgew0KICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXHNhbXBsaW5nX21vZGVsX0FCX2ZvbGRDX3NlZWQwXzIwMjYxMTAzX3YxXFx0cmFuc3BvcnRfdjFcXGJjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEudGFyLmd6IiwNCiAgICAgICAgImZpbGVuYW1lIjogImJjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEudGFyLmd6IiwNCiAgICAgICAgImJ5dGVzIjogOTkzMzY0ODMsDQogICAgICAgICJzaGEyNTYiOiAiZTEwY2YwMzUzNjI2NTk3NmI5YzQyY2E2ZDg1ZGE1NGVmZGExMmVmZDg0MzExZWE2ZDNlNGZhYTZhZmFjMzdhOCIsDQogICAgICAgICJ1cGxvYWRfZGlyZWN0b3J5IjogIi9ob21lL2pvdnlhbiINCiAgICAgIH0sDQogICAgICB7DQogICAgICAgICJwYXRoIjogIkU6XFxDb2RleFxcMjAyNi0wNi0wNlxcbWFtYmEtY2NmLWMtMS1oaWdoLXJlc29sdXRpb25cXG91dHB1dHNcXGNyYW5pYWxfYmNzcF9nZW92MV8yMDI2MTAyNFxcc2FtcGxpbmdfbW9kZWxfQUJfZm9sZENfc2VlZDBfMjAyNjExMDNfdjFcXHRyYW5zcG9ydF92MVxcYmNzcF9zYW1wbGluZ19hYl9mb2xkY19zZWVkMF92MS50YXIuZ3ouc2hhMjU2IiwNCiAgICAgICAgImZpbGVuYW1lIjogImJjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEudGFyLmd6LnNoYTI1NiIsDQogICAgICAgICJieXRlcyI6IDEwNSwNCiAgICAgICAgInNoYTI1NiI6ICI4YmQwM2Y1ZGY4MDgxOTExNjYwNjA5NGZhY2M4Mjg3MWI5ZGZlZjlmYzY4OTMyY2MyNTczNzgwZjM2N2I2ZjJmIiwNCiAgICAgICAgInVwbG9hZF9kaXJlY3RvcnkiOiAiL2hvbWUvam92eWFuIg0KICAgICAgfSwNCiAgICAgIHsNCiAgICAgICAgInBhdGgiOiAiRTpcXENvZGV4XFwyMDI2LTA2LTA2XFxtYW1iYS1jY2YtYy0xLWhpZ2gtcmVzb2x1dGlvblxcb3V0cHV0c1xcY3JhbmlhbF9iY3NwX2dlb3YxXzIwMjYxMDI0XFxzYW1wbGluZ19tb2RlbF9BQl9mb2xkQ19zZWVkMF8yMDI2MTEwM192MVxcdHJhbnNwb3J0X3YxXFxiY3NwX3NhbXBsaW5nX2FiX2ZvbGRjX3NlZWQwX3YxLmJ5dGVzIiwNCiAgICAgICAgImZpbGVuYW1lIjogImJjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEuYnl0ZXMiLA0KICAgICAgICAiYnl0ZXMiOiA5LA0KICAgICAgICAic2hhMjU2IjogImQ5NDAxZWVmMDAxN2ZmYmRhODZmNDE2ZTI4ZjFkZDQ2NjAxMjZiNzc0YTcwNjFjOWE4YWM0YmVkMjEwMmY0ZTkiLA0KICAgICAgICAidXBsb2FkX2RpcmVjdG9yeSI6ICIvaG9tZS9qb3Z5YW4iDQogICAgICB9LA0KICAgICAgew0KICAgICAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXHNhbXBsaW5nX21vZGVsX0FCX2ZvbGRDX3NlZWQwXzIwMjYxMTAzX3YxXFx0cmFuc3BvcnRfdjFcXGJjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEuY29udGVudHMuc2hhMjU2IiwNCiAgICAgICAgImZpbGVuYW1lIjogImJjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEuY29udGVudHMuc2hhMjU2IiwNCiAgICAgICAgImJ5dGVzIjogODAzNTIsDQogICAgICAgICJzaGEyNTYiOiAiODZkZjg1Mjc4NWU3N2UzZTg0MGEwZmIxMDI0Zjk0MzljODhkMWUwMDg4MjM0NDZkMjE4YWIxM2JhZTU0MGUwMSIsDQogICAgICAgICJ1cGxvYWRfZGlyZWN0b3J5IjogIi9ob21lL2pvdnlhbiINCiAgICAgIH0sDQogICAgICB7DQogICAgICAgICJwYXRoIjogIkU6XFxDb2RleFxcMjAyNi0wNi0wNlxcbWFtYmEtY2NmLWMtMS1oaWdoLXJlc29sdXRpb25cXG91dHB1dHNcXGNyYW5pYWxfYmNzcF9nZW92MV8yMDI2MTAyNFxcc2FtcGxpbmdfbW9kZWxfQUJfZm9sZENfc2VlZDBfMjAyNjExMDNfdjFcXHRyYW5zcG9ydF92MVxcYmNzcF9zYW1wbGluZ19hYl9mb2xkY19zZWVkMF92MS5jb250ZW50cy5zaGEyNTYuc2hhMjU2IiwNCiAgICAgICAgImZpbGVuYW1lIjogImJjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEuY29udGVudHMuc2hhMjU2LnNoYTI1NiIsDQogICAgICAgICJieXRlcyI6IDExNCwNCiAgICAgICAgInNoYTI1NiI6ICJlN2I2NTBhZDY1NTc4MmZmYzhkY2Q1NDlmMGI1OTUzZDRiNDgyNDAxMGNkYzgzZDdiNmI0YjNjZmYyMjUwOWUxIiwNCiAgICAgICAgInVwbG9hZF9kaXJlY3RvcnkiOiAiL2hvbWUvam92eWFuIg0KICAgICAgfQ0KICAgIF0sDQogICAgImFyY2hpdmVfc2hhMjU2IjogImUxMGNmMDM1MzYyNjU5NzZiOWM0MmNhNmQ4NWRhNTRlZmRhMTJlZmQ4NDMxMWVhNmQzZTRmYWE2YWZhYzM3YTgiLA0KICAgICJtZW1iZXJzIjogNjQ3LA0KICAgICJpbnN0YWxsYXRpb25fbWFwcGluZyI6IHsNCiAgICAgICJwYXRoIjogIkU6XFxDb2RleFxcMjAyNi0wNi0wNlxcbWFtYmEtY2NmLWMtMS1oaWdoLXJlc29sdXRpb25cXG91dHB1dHNcXGNyYW5pYWxfYmNzcF9nZW92MV8yMDI2MTAyNFxcc2FtcGxpbmdfbW9kZWxfQUJfZm9sZENfc2VlZDBfMjAyNjExMDNfdjFcXG5vbl9vdmVyd3JpdGVfaW5zdGFsbGF0aW9uX21hcHBpbmdfdjEuanNvbiIsDQogICAgICAic2hhMjU2IjogIjZjODk4ZDc1OTk3Zjg2YjI3M2UzN2JmOGRlNzUyZGI5YWM3ODE4ZTRhZWIzMDYyZTMxNzU0OTM5YzQ5ZmY0YTQiDQogICAgfQ0KICB9LA0KICAiZnV0dXJlX3BhdGhzIjogew0KICAgICJjb250cm9sIjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9zYW1wbGluZ19hYl9mb2xkY19zZWVkMF92MS9jb250cm9sX1YxX3YxIiwNCiAgICAiYXV0aG9yaXphdGlvbiI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3Bfc2FtcGxpbmdfYWJfZm9sZGNfc2VlZDBfdjEvY29udHJvbF9WMV92MS9hdXRob3JpemF0aW9uX3YxLmpzb24iLA0KICAgICJydW50aW1lIjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9zYW1wbGluZ19hYl9mb2xkY19zZWVkMF92MS9jb250cm9sX1YxX3YxL3J1bnRpbWVfdjEuanNvbiIsDQogICAgImxhdW5jaGVyIjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9zYW1wbGluZ19hYl9mb2xkY19zZWVkMF92MS9jb250cm9sX1YxX3YxL2xhdW5jaF9vbmNlX3YxLnNoIiwNCiAgICAibGF1bmNoX2F0dGVtcHQiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci90aGlyZF9wYXJ0eS9iY3NwX3NhbXBsaW5nX2FiX2ZvbGRjX3NlZWQwX3YxL2NvbnRyb2xfVjFfdjEvbGF1bmNoX2F0dGVtcHRfdjEuanNvbiIsDQogICAgIm91dHB1dCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL2xvZ3MvY3JhbmlhbF9iY3NwX3NhbXBsaW5nX2FiX3YxL2Jjc3Bfc2FtcGxpbmdfYWJfZm9sZENfVjFfaW44MTkyX291dDgxOTJfc2VlZDBfdHJhaW5fdjEiLA0KICAgICJsb2ciOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci9sb2dzL2NyYW5pYWxfYmNzcF9zYW1wbGluZ19hYl92MS9iY3NwX3NhbXBsaW5nX2FiX2ZvbGRDX1YxX2luODE5Ml9vdXQ4MTkyX3NlZWQwX3RyYWluX3YxL2xhdW5jaC5sb2ciLA0KICAgICJQSUQiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci9sb2dzL2NyYW5pYWxfYmNzcF9zYW1wbGluZ19hYl92MS9iY3NwX3NhbXBsaW5nX2FiX2ZvbGRDX1YxX2luODE5Ml9vdXQ4MTkyX3NlZWQwX3RyYWluX3YxL3dvcmtlci5waWQiLA0KICAgICJleGl0X2NvZGUiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci9sb2dzL2NyYW5pYWxfYmNzcF9zYW1wbGluZ19hYl92MS9iY3NwX3NhbXBsaW5nX2FiX2ZvbGRDX1YxX2luODE5Ml9vdXQ4MTkyX3NlZWQwX3RyYWluX3YxL2V4aXRfY29kZS50eHQiLA0KICAgICJjaGVja3BvaW50IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvbG9ncy9jcmFuaWFsX2Jjc3Bfc2FtcGxpbmdfYWJfdjEvYmNzcF9zYW1wbGluZ19hYl9mb2xkQ19WMV9pbjgxOTJfb3V0ODE5Ml9zZWVkMF90cmFpbl92MS9ja3B0LWxhc3QucHRoIiwNCiAgICAiY29tcGxldGlvbiI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL2xvZ3MvY3JhbmlhbF9iY3NwX3NhbXBsaW5nX2FiX3YxL2Jjc3Bfc2FtcGxpbmdfYWJfZm9sZENfVjFfaW44MTkyX291dDgxOTJfc2VlZDBfdHJhaW5fdjEvY29tcGxldGlvbi5qc29uIiwNCiAgICAidG11eCI6ICJiY3NwX3NhbXBsaW5nX2FiX2ZvbGRjX3YxX3NlZWQwX3RyYWluX3YxIg0KICB9LA0KICAibGF1bmNoZXJfY29udHJhY3QiOiB7DQogICAgImVudmlyb25tZW50Ijogew0KICAgICAgIkNVREFfVklTSUJMRV9ERVZJQ0VTIjogIkdQVS0zNGExYjk5Ni0yYmQ3LTg4ZTYtOWRjYS0xNjRiNzE4Y2FlYTYiLA0KICAgICAgIkNVQkxBU19XT1JLU1BBQ0VfQ09ORklHIjogIjo0MDk2OjgiLA0KICAgICAgIk9NUF9OVU1fVEhSRUFEUyI6ICIyIiwNCiAgICAgICJNS0xfTlVNX1RIUkVBRFMiOiAiMiIsDQogICAgICAiT1BFTkJMQVNfTlVNX1RIUkVBRFMiOiAiMiIsDQogICAgICAiUFlUSE9ORE9OVFdSSVRFQllURUNPREUiOiAiMSIsDQogICAgICAiTVBMQkFDS0VORCI6ICJBZ2ciLA0KICAgICAgIk1QTENPTkZJR0RJUiI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL2xvZ3MvY3JhbmlhbF9iY3NwX3NhbXBsaW5nX2FiX3YxL2Jjc3Bfc2FtcGxpbmdfYWJfZm9sZENfVjFfaW44MTkyX291dDgxOTJfc2VlZDBfdHJhaW5fdjEvbXBsY29uZmlnIiwNCiAgICAgICJDVURBX0NBQ0hFX0RJU0FCTEUiOiAiMSINCiAgICB9LA0KICAgICJweXRob24iOiAiL29wdC9jb25kYS9lbnZzL2FkYXBvaW50ci1tYW1iYS9iaW4vcHl0aG9uMy4xMCIsDQogICAgImZsYWdzIjogWw0KICAgICAgIi1JIiwNCiAgICAgICItUyIsDQogICAgICAiLUIiDQogICAgXSwNCiAgICAiZW50cnkiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci90aGlyZF9wYXJ0eS9iY3NwX3NhbXBsaW5nX2FiX2ZvbGRjX3NlZWQwX3YxL2ltcGxlbWVudGF0aW9uL2Jjc3Bfc2FtcGxpbmdfdHJhaW5pbmdfZW50cnlfdjEucHkiLA0KICAgICJlbnRyeV9zaGEyNTYiOiAiNjgwMmRhMmUzOGMzNjU5ODMyOWJlYjhhNzFhOTYzNTI0ZWFiZDkxNDAxYzVmMGQ1OGQ3OTk3MTNiZTRlYjc3OSIsDQogICAgImV4dGVybmFsX3RpbWVvdXRfc2Vjb25kcyI6IDg2NDAwLA0KICAgICJraWxsX2FmdGVyX3NlY29uZHMiOiA1LA0KICAgICJvcmRlciI6ICJ2ZXJpZnkgYWxsIHNvdXJjZS9lbnZpcm9ubWVudC9yZXNvdXJjZSBnYXRlczsgY3JlYXRlIGFuZCB2ZXJpZnkgcGFyZW50cyBiZWZvcmUgcmVkaXJlY3Q7IGNsYWltIGV4Y2x1c2l2ZSBhdHRlbXB0IGJlZm9yZSBzaW5nbGUgdG11eCBsYXVuY2g7IHByb3BhZ2F0ZSB0cnVlIGV4aXQgY29kZSBpbmNsdWRpbmcgUG93ZXJTaGVsbCBleGl0IExBU1RFWElUQ09ERSIsDQogICAgIm9uZV93YXlfbWF0ZXJpYWxpemF0aW9uIjogImZyb3plbiBpbm5lciByZXF1ZXN0IC0+IGV4cGxpY2l0IGF1dGhvcml6YXRpb24gYmluZHMgaW5uZXIvZnVsbCBzY29wZSBoYXNoZXMgLT4gY29tcHV0ZSBhdXRob3JpemF0aW9uIFNIQSAtPiBydW50aW1lIGJpbmRzIHJlcXVlc3QgYW5kIGF1dGhvcml6YXRpb24gLT4gc2luZ2xlIGxhdW5jaGVyOyBubyByZXZlcnNlIGhhc2ggZWRnZXMiDQogIH0sDQogICJzY2llbnRpZmljX3Jpc2tfZGlzY2xvc3VyZSI6IFsNCiAgICAiQm90aCBhcm1zIGhhdmUgYSBuZXcgY29tbW9uIGZpeGVkIGlucHV0LXBlcm11dGF0aW9uIHBvbGljeSwgdGhlcmVmb3JlIG5vIGRpcmVjdCByZXVzZSBvZiBoaXN0b3JpY2FsIHdlaWdodHMgYXMgbWFpbiBtYXRjaGVkIGFybSIsDQogICAgIlJlYWQtb25seSBpZGVudGl0eS9wcm92aWRlciBtYXRjaCBpcyBub3QgY3VycmVudCBDVURBIHZlcmlmaWNhdGlvbjsgdW5jaGFuZ2VkIGFyaXRobWV0aWMgdXNlcyBoaXN0b3JpY2FsIEdQVSBldmlkZW5jZSIsDQogICAgIkNQVSB0ZXN0cyBpbmNsdWRlIFJBTSBhdXRob3JpemF0aW9uIGZpeHR1cmVzLCBub3QgbGl2ZSBzZXJ2ZXIgZXhlY3V0aW9uIiwNCiAgICAiTW9uaXRvcmVkIHJlc291cmNlIHN0b3BwaW5nIG9ubHksIG5vIHN0cmljdCBQSUQgb3duZXJzaGlwIG9yIGV4Y2x1c2l2ZSBjZ3JvdXAgZ3VhcmFudGVlIg0KICBdLA0KICAiY29tcGxldGlvbl9ib3VuZGFyeSI6ICJzdG9wIGFmdGVyIHRoaXMgb25lIFYxIGF0dGVtcHQuIEluZGVwZW5kZW50IHBvc3QtdHJhaW5pbmcgZnJlZXplIGF1ZGl0IGFuZCBleGFjdCBpbml0aWFsaXphdGlvbiBldmlkZW5jZSByZXF1aXJlIHRoZSBuZXh0IGV4cGxpY2l0IHNjb3BlOyBjYW5kaWRhdGUgcmVxdWVzdCBpcyBub3QgeWV0IGNyZWF0ZWQuIiwNCiAgImZvcmJpZGRlbiI6IFsNCiAgICAibm8gY2FuZGlkYXRlIHRyYWluaW5nIiwNCiAgICAibm8gZGV2ZWxvcG1lbnQgcGF5bG9hZC9ldmFsdWF0aW9uIiwNCiAgICAibm8gQk5DYWwiLA0KICAgICJubyBGb2xkRC9Ta3VsbEZpeC9NVUcvTWFtYmEgY2hhbmdlcyIsDQogICAgIm5vIHJlc3VtZS9yZXRyeSIsDQogICAgIm5vIGRlcGVuZGVuY3kgZG93bmxvYWQvcmVidWlsZCBvciBlbnZpcm9ubWVudCB1cGdyYWRlOyBubyBjaGFuZ2VzIHRvIGZyb3plbiBtb2RlbC9wcm92aWRlciBzb3VyY2VzIiwNCiAgICAibm8gb2xkLWZpbGUgb3ZlcndyaXRlL2RlbGV0ZSINCiAgXSwNCiAgInN1cGVyc2VkZXMiOiB7DQogICAgInBhdGgiOiAiVjFfdHJhaW5pbmdfZXhlY3V0aW9uX3JlcXVlc3RfdjEuanNvbiIsDQogICAgInNoYTI1NiI6ICI4YmZjZjZiMDk2ZTdhZDUyYWZkMTFjNDMwZDYzNmYwZjdjMmJkZDA4NDFjMzYzZmI4NjBmODEzOGExOWY3ZmU3IiwNCiAgICAicmVhc29uIjogImNsYXJpZnkgZGVwZW5kZW5jeS9tb2RlbC1zb3VyY2UgcHJvaGliaXRpb24gd2hpbGUgYWxsb3dpbmcgdGhlIGV4cGxpY2l0bHkgbWFwcGVkIG5ldyB0b29scy9kYXRhIGluc3RhbGxhdGlvbiIsDQogICAgInYxX2F1dGhvcml6ZWRfb3JfZXhlY3V0ZWQiOiBmYWxzZQ0KICB9DQp9')
EXPECTED_CONTROL=[{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_sampling_ab_foldc_seed0_v1/control_V1_v1/training_entry_request_v1.json', 'bytes': 5614, 'sha256': 'a3a2870248e7a0759362f6dec337ce6768e8edfabb585e8d63def1ed3a90a680'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_sampling_ab_foldc_seed0_v1/control_V1_v1/authorization_v1.json', 'bytes': 603, 'sha256': '1ea3c04bff3f008124bc72f9e824e93ed4f4f91fa83392a8d3d4c31cce6dc954'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_sampling_ab_foldc_seed0_v1/control_V1_v1/runtime_v1.json', 'bytes': 224, 'sha256': '690242387a7b93bff6e914ff73655b64b47faca2fce0baa0a6fb9ca230c7c398'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_sampling_ab_foldc_seed0_v1/control_V1_v1/launch_once_v1.sh', 'bytes': 1899, 'sha256': 'fc1830955a67d1cc66087525ed2a4975eed7e8a220b63f8b7ed0b80b1bef853a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_sampling_ab_foldc_seed0_v1/control_V1_v1/launch_attempt_v1.json', 'bytes': 366, 'sha256': 'ff13df531895fbed01c83765f82184e96f5a5888e7ea9f6dc3360395098b46de'}]
START=time.monotonic();TOTAL=0;cache={};checks={};rows=[];READ_STAMPS={}
ROOT=Path('/home/jovyan/adapointr_work/PoinTr')
CODE=ROOT/'third_party/bcsp_sampling_ab_foldc_seed0_v1'
CONTROL=CODE/'control_V1_v1'
OUT=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_ab_foldC_V1_in8192_out8192_seed0_train_v1')
SCOPE='4a889afad90b1a8a52fcb75691c71990d03af8b7d120a96608ac4b9b85cb7a62'

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
 if str(p) in cache:
  value=cache[str(p)]
  if binding:need(value[0]['bytes']==binding['bytes'] and value[0]['sha256']==binding['sha256'],'cached binding mismatch: '+str(p))
  return value
 parents(p);st=p.lstat();need(stat.S_ISREG(st.st_mode),'nonregular: '+str(p))
 limit=536870912 if checkpoint else 16777216
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
 check('correct_sampling_stage',q['stage']==complete['stage']=='BCSP_SAMPLING_AB_V1' and q['arm']=='V1' and q['paired_initialization'] is None)
 check('completion_exact_counts',complete['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100))
 check('completion_update_traversal_exposure',complete['optimizer_updates']==3900 and complete['traversals']==100 and complete['case_exposures']==31200)
 check('BNCal_evaluation_resume_false',all(complete[k] is False for k in ['bncal_executed','evaluation_executed','resume']))
 checkpoint=read(OUT/'ckpt-last.pth',checkpoint=True)[0]
 check('checkpoint_SHA256_matches_completion',checkpoint['sha256']==complete['checkpoint_sha256'])
 fold=js(q['QC']['fold_binding']['path'])['folds']['C']
 manifest={x['case_id']:x for x in map(json.loads,read(q['QC']['manifests']['V1']['path'])[1].decode().splitlines())}
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
 candidate=js(q['QC']['qualified_receipt']['path']);check('V1_qualified_arm',candidate['arm']=='V1')
 other={r['case_id']:r for r in map(json.loads,read(q['QC']['manifests']['Morton_area_stratified8k']['path'])[1].decode().splitlines())}
 check('candidate315_metadata_ready',len(other)==315 and set(other)==set(fold['train_case_ids']))
 candidate_bytes=0
 candidate_root=Path(str(q['data_root']).rsplit('/',1)[0])/'Morton_area_stratified8k'
 for cid,a in manifest.items():
  b=other[cid]
  need(all(a[k]==b[k] for k in ['case_id','source_id','target_array_sha256','normalization','common_point_order_sha256']),'candidate target/frame/order pairing')
  need(b['source_id'] in fold['train_sources'] and b['sampler_arm']=='Morton_area_stratified8k' and b['n_input']==b['n_target']==8192,'candidate training scope')
  rel=Path(b['point_path']);need(not rel.is_absolute() and '..' not in rel.parts,'candidate relative path')
  row,_=read(candidate_root/rel);need(row['sha256']==b['sha256'],'candidate file hash');candidate_bytes+=row['bytes']
 check('candidate315_stream_hashes_match_frozen_manifest',True)
 candidate_control=CODE/'control_Morton_v1'
 candidate_output=OUT.parent/'bcsp_sampling_ab_foldC_Morton_in8192_out8192_seed0_train_v1'
 check('new_candidate_control_and_output_absent',not candidate_control.exists() and not candidate_control.is_symlink() and not candidate_output.exists() and not candidate_output.is_symlink())
 candidate_tmux=subprocess.run(['tmux','has-session','-t','bcsp_sampling_ab_foldc_morton_seed0_train_v1'],capture_output=True,timeout=5)
 check('new_candidate_tmux_absent',candidate_tmux.returncode==1)
 gpu=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,timeout=10)
 need(gpu.returncode==0,'current GPU metadata query')
 observed=[s.strip() for s in gpu.stdout.decode().strip().split(',')]
 check('same_gpu_identity_for_future_paired_request',observed[:4]==[q['identity']['gpu_uuid'],q['identity']['gpu_name'],q['identity']['driver_version'],str(q['identity']['nvidia_smi_memory_total_MiB'])])
 check('all_hashed_files_stable_atime_excluded',all(stamp(Path(p).lstat())==record for p,record in READ_STAMPS.items()))
 check('result_tree_stable_atime_excluded',tree()==before)
 check('no_failure_markers',not (OUT/'failure.json').exists() and not (OUT/'startup_failure.json').exists())
 print(json.dumps(dict(status='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS',checks=checks,completion=complete,checkpoint=checkpoint,output_manifest=[r for r in rows if str(OUT)+'/' in r['path']],all_bound_files=[r for r in rows if not r['path'].endswith('.npz')],initialization=initialization,optimizer_defaults=defaults,candidate_readiness=dict(files=315,stream_hashed_bytes=candidate_bytes,control_absent=True,output_absent=True,tmux_absent=True),current_GPU_metadata=observed,
 counts=dict(metric_records=len(metrics),epochs=100,updates=3900,case_exposures=sum(case.values()),dropped_exposures=sum(drops.values()),resource_records=len(resources)),
 resource_summary=dict(peak_allocated=max(r['peak_allocated'] for r in resources),peak_reserved=max(r['peak_reserved'] for r in resources),device_peak_MiB=max(r['device_MiB'] for r in resources),RSS_peak=max(r['RSS'] for r in resources),PID_warning_records=sum(bool(r['PID_warning']) for r in resources)),
 loss_summary=dict(first=losses[0],last=losses[-1],last_epoch_mean=sum(losses[-39:])/39,interpretation='Training loss only;not development or clinical performance'),
 exact_source_runtime_binding_verified=True,checkpoint_loaded=False,checkpoint_stream_hashed=True,initialization_weights_reconstructed=False,NPZ_decoded=False,model_imported=False,forward_calls=0,server_writes=0,hashed_bytes=TOTAL,elapsed_seconds=time.monotonic()-START,
 limitations=['Forward/backward/scheduler counters are corroborated by pinned runtime and completion; no independent GPU trace','No strict GPU process ownership guarantee by approved policy','BNCal/evaluation false is supported by pinned execution path and completion flags; no independent OS-wide file-access trace'])),flush=True)
except BaseException as exc:
 print(json.dumps(dict(status='AUDIT_FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks,all_bound_files=[r for r in rows if not r['path'].endswith('.npz')],server_writes=0,checkpoint_loaded=False,forward_calls=0)),flush=True)
 raise
