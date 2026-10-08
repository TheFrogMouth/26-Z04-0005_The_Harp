import os
HERE = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE, '..', 'harp_schematic'))
import importlib, place; importlib.reload(place)
from place import L, bbox, padpos, face_of, in_board
from kisch import parse
from pcbread import PCB
parse(open(PCB).read())
top=[]; th=[]
for r in L:
    fx,fy,a=face_of(r)
    if not (-28<fx<28 and -38<fy<57): print('OFF', r)
    if L[r]['layer']=='F.Cu': top.append((r,bbox(r,fx,fy,a)))
    else:
        for p,px,py in padpos(r,fx,fy,a):
            if p['kind']=='thru_hole': s=max(p['w'],p['h'])/2; th.append((r,(px-s,px+s,py-s,py+s)))
ov=[(top[i][0],top[j][0]) for i in range(len(top)) for j in range(i+1,len(top))
    if top[i][1][0]<top[j][1][1]-1e-3 and top[i][1][1]>top[j][1][0]+1e-3 and top[i][1][2]<top[j][1][3]-1e-3 and top[i][1][3]>top[j][1][2]+1e-3]
pad=[(r,q) for r,a in top for q,b in th if a[0]<b[1] and a[1]>b[0] and a[2]<b[3] and a[3]>b[2]]
edge=[r for r,c in top if not in_board(c)]
MOD=(-19,19,-26.25,-13.75)
tall=[r for r,c in top if r in ('K401','C502','C508') and c[0]<MOD[1] and c[1]>MOD[0] and c[2]<MOD[3] and c[3]>MOD[2]]
print('top courtyard overlaps:',ov); print('top courtyards over underside TH pads:',sorted(set(pad))); print('outside board:',edge); print('tall parts under OLED:',tall)
