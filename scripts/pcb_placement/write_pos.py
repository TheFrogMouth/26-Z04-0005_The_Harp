import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
import sys, json, re
sys.path.insert(0,HERE)
from pcbread import footprints, PCB
pos=json.load(open(os.path.join(OUT, 'pos.json')))
t=open(PCB).read(); moved=0
for f in sorted(footprints(t), key=lambda f:-f['s']):
    r=f['ref']
    if r not in pos: continue
    fx,fy,a=pos[r]; b=f['b']
    m=re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',b)
    X,Y,A0=float(m.group(1)),float(m.group(2)),float(m.group(3) or 0)
    nx,ny=round(148.5+fx,4),round(105-fy,4); d=(a-A0)%360
    if abs(nx-X)<1e-6 and abs(ny-Y)<1e-6 and d==0: continue
    nb=b[:m.start()]+'\n\t\t(at %g %g%s)'%(nx,ny,(' %g'%a) if a%360 else '')+b[m.end():]
    if d:
        nb=re.sub(r'(\n\t\t\t\(at )([-\d.]+ [-\d.]+)(?: ([-\d.]+))?\)',lambda mm:'%s%s %g)'%(mm.group(1),mm.group(2),(float(mm.group(3) or 0)+d)%360),nb)
    t=t[:f['s']]+nb+t[f['e']:]; moved+=1
open(PCB,'w').write(t); print('moved',moved)
