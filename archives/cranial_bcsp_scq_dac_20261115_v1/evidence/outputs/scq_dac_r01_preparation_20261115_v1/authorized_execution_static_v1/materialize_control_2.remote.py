from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b85decode('c-p;I+m4$!7{2Ez+-|qMs2H%p94gTj0Wv|8gfwK@t#((IF(#oyfO43fRDJk$GD#<yt+a<Wy+9%U?eAn``==*Ll9x(C+m+Pv4#>Qh`ZaBDfNGi&OM$Yg)?E2e-EL^9(3I9yUUm)nvubXXnRs6`(r@4ikjM8u!5`rBXTb0B4nPD?N_&uh?(vA`KM&aJ`oH6pqFT1!G+1E`Epu9sgtaxv`l49Vbwba9sl?tJ;=3N1Ly|SsCtf0zAQc%9LQHPqBhK|rnm0hMfh>O`@c~LcvjK_U)m760@7j0C+b|9X<AC_V+t3SQ=W=!}YnGNmXi-@+EGFAJ*JNlIRAw~Qct#T|OU(z6!Pt$-yJ&tD&s;AcUNjwsm(D9)wT)NSp<6VWk?Hk>EJpLd^<xJe3X`kx*9*}snC_szTAjULjH0O@O&9Ox;UXBkUj$y{2hJCBli7ISdRM{JciiRjsP$f-AI_cgrmU>%f>mXfFHiFJTyG@O4r5oO{vdZTnf(As-MT&vaOB3LI0$@4J+zO8WOO|s(Qr5pr^f>4?lc}o^GPs||6bjWiYCFi^{+C*C|mIZ?XUjjKF}Y*enPzv%PyLJna=Z1U6XfJxwpSPR$g*R>Dy*^)^z!rSG_oD<ThWHv~U)|d?Nnc<V7LVtmBP?TVSYa3zVwv6tON-s_^o*eNZaj>)688n{HK=+67dB90EB8^5EZWN!==MQc}~V+bBDCE&E7P%18rGtURu90kjc?i+Uq8H~eGI+wOZ39%ak#IP1GyB)R9=@_uNm@_|`yR}^7GZ0<JAI8_aks?bsqw6F<n-BPg)EgkdiPl^%KQ)DGJXNHMYh!SXu4HN3r5{R@HK{oj(x@G*Hj>H6ZO;so-1V>g*+7E^p%TkNknw}aI8>X2V++dld+mI)jk(f}kIYN4ZbrWOT##usbn&>b|Y>c>$w-NQ_cCDSm${zZ7KJHr%@=a=Bm2zD?FjJ{!qXZ+B>y#qMZJ21BGohI$hLspdO?Ayg7&1h447sK1;Psh5(Sr6RTU`hUfL=d`Qp22QzwEDoQr!ry47~Wc{k?nvo<3{X)3XcO-cbmvQhw3hb<*y}vLlxM0-;-#!~'))
assert hashlib.sha256(b).hexdigest() == 'f4612ac70d273eed1909df4c2a6ae11bd133cd15a576d3c13fc3949e6b829300'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'f4612ac70d273eed1909df4c2a6ae11bd133cd15a576d3c13fc3949e6b829300'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_MATERIALIZED', name=p.name, sha256='f4612ac70d273eed1909df4c2a6ae11bd133cd15a576d3c13fc3949e6b829300')))