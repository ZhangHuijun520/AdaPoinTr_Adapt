from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_launch_once_v2.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9lltv2zYYhu/1K9is682gSKRkHQqogyzLsRHb8iynXbENBEmRthqdqoOXDP3xox07sZsCOxTxnUR+h/d5SYn84ZVG00KjpFkrDW+Byjuly0lzC3TbVlgCtHWZc+1TubknhUYSUpVp0db4z7K+1ebyeVkrv4FXQJ08RII/wJcvgN+lLYAInkzti/xzxFdt/nPCXtf/zdOyctV8V7LGalKkJMOUNRUWXZblJKfkJWpqcfAL7sc4GOCCtOmG44RveFZWOS9ajHRkQQhNvEFfNc9vk7QGagVU9TsVHEqp5yJR+F1V1i0IbgY+fj+Ox/1JiAfh+3EQxt7V/EZNCGXMcW2VMMtVuSBMNU3DUYkFHSvhxCWEPBXpT/wYf4gW1/HcD0IcRLPh+Mp7a+qu9dY5hEXTOZ7dTPFytAj9Qew9ipheT749Ec3D2a70N2fnH5ejaDaIZssPi/Ey7H9chkE0CD34WHc+6fvBdTgbeP5qdTT6oG8wXnhnslvLq4yVhUhXJ8YHfjCSto9jX9r/pHs5nZ9TW5tXp5aO/HgUh+HA0w/joyEe3fRxNBxOxrNjpQt/Fg+jxTRcxM9nt1nRNDwbyFpgRtiaH/r/OrjaW3xWGScalnJrRrPHlT7jqtZpWxZ7Q7an0k9c0bqm3h1VbZrzspMnldqkq4Jk3jJcTOXbbZplKhEtr71eA2yk6w3QyqrV5OZNiMaLTfOkWX1QtK1X3bfrsjAuoQ7UMVBjoPb/zZ+sXad1gitSt/fajrNhn/d0Vc2TlLWpRDimeowSZVfnZcKzgw/7BBl0Wd1LlJp/7njTvoyMZ6twFMfvOOt2T3sJW0mfmrJ4EqU2a4J6FmDcpCa1bESQ67qGaSOY6FQXUFCEOEFGwiFlJhSJ6zpCuCaHumE5gkNOOe8RWZF00vk6/YtsO74MrFz7ti4z7TnqSfMjzJPxA6zes7krgQ3XgYgR3nMpERI8SQRyDYdKKGImiAkbQkM3CRLUcbhjcYvalkzc2tcV2517bsx92+N1fBg5oAnTpdB1dIkgqJHoyHQkld6ToMhJbAGJi0xTODrsOVS3LeImNIEWoj1kcN1E4N25/goZ6Qq2vpS1AHr3Bio1817/vL+0KlUtmwpw8WPze3EBLl7X7OJ8yra3KszkF33Z3rXK7o61U6D8DbX660U='))
assert hashlib.sha256(b).hexdigest() == '3fe2dcf7c80b7626036d075184d381dc15b1bb77e5c5b2b8e5ef65deabc5686a'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '3fe2dcf7c80b7626036d075184d381dc15b1bb77e5c5b2b8e5ef65deabc5686a'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))