import os
HERE = os.path.dirname(os.path.abspath(__file__))
import sys, json, math; sys.path.insert(0,HERE)
from place import L, padpos
from collections import defaultdict
def score(pos):
    P=defaultdict(list)
    for r,(fx,fy,a) in pos.items():
        for p,px,py in padpos(r,fx,fy,a):
            if p['net']: P[p['net']].append((px,py))
    tot=0; ana=0
    for n,pts in P.items():
        if n in ('GND','+3V3','+5V','+9V','VDDA') or n.startswith('unconnected') or len(pts)<2: continue
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; hp=(max(xs)-min(xs))+(max(ys)-min(ys))
        tot+=hp
        if n.startswith(('/ADC Driver','/Analog','/Codec','ADC_','DAC_','EFFECT','VCOM','IN','IN_R')): ana+=hp
    return round(tot), round(ana)
if __name__=='__main__':
    print(score(json.load(open(sys.argv[1]))))
