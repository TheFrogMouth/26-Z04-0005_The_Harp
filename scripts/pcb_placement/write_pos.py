"""Write build/pos.json into the board file: position, rotation and side (flipping a footprint as KiCad does:
local Y mirrored, angles negated, F./B. layers swapped, text mirrored)."""
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build')
sys.path.insert(0, HERE)
from pcbread import footprints, PCB
from geom import rot

SWAP = lambda m: m.group(0).replace('"F.', '"\x00').replace('"B.', '"F.').replace('"\x00', '"B.')

def rewrite(b, X, Y, A, flip):
    m = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', b)
    X0, Y0, A0 = float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)
    b = b[:m.start()] + '\n\t\t(at %g %g%s)' % (X, Y, (' %g' % A) if A % 360 else '') + b[m.end():]
    def at3(mm):           # pad / text positions (local) and absolute angles
        x, y, a = float(mm.group(2)), float(mm.group(3)), float(mm.group(4) or 0)
        loc = a - A0
        if flip:
            y, loc = -y, -loc
        return '%s%g %g %g)' % (mm.group(1), x, y, (loc + A) % 360)
    # (point (at x y)) markers are kept in board coordinates and take no angle: they move with the
    # footprint (rotation and flip about its origin) and are kept out of at3
    pts = []
    def hide(mm):
        x, y = float(mm.group(1)) - X0, float(mm.group(2)) - Y0
        lx, ly = rot(x, y, -A0)
        if flip:
            ly = -ly
        dx, dy = rot(lx, ly, A)
        pts.append('\t\t(point\n\t\t\t(at %g %g)' % (round(X + dx, 4), round(Y + dy, 4)))
        return '\x01%d\x01' % (len(pts) - 1)
    b = re.sub(r'\t\t\(point\n\t\t\t\(at ([-\d.]+) ([-\d.]+)(?: [-\d.]+)?\)', hide, b)
    b = re.sub(r'(\n\t\t\t\(at )([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', at3, b)
    b = re.sub('\x01(\\d+)\x01', lambda mm: pts[int(mm.group(1))], b)
    if flip:
        b = re.sub(r'(\((?:start|end|mid|center|xy) )([-\d.]+) ([-\d.]+)\)', lambda mm: '%s%s %g)' % (mm.group(1), mm.group(2), -float(mm.group(3))), b)
        b = re.sub(r'\((?:layer|layers) [^)]*\)', SWAP, b)
        b = re.sub(r'\n\t*\(render_cache .*?\n\t\t\t\)', '', b, flags=re.S)
        def mirror(mm):       # toggle (justify mirror) in each text effects block
            e = mm.group(0)
            if '(justify mirror)' in e:
                return e.replace('\n\t\t\t\t(justify mirror)', '')
            return e[:-len('\n\t\t\t)')] + '\n\t\t\t\t(justify mirror)\n\t\t\t)'
        b = re.sub(r'\n\t\t\t\(effects\n.*?\n\t\t\t\)', mirror, b, flags=re.S)
    return b

if __name__ == '__main__':
    pos = json.load(open(os.path.join(OUT, 'pos.json')))
    t = open(PCB).read(); moved = flipped = 0
    for f in sorted(footprints(t), key=lambda f: -f['s']):
        r = f['ref']
        if r not in pos: continue
        fx, fy, a, side = pos[r]
        layer = re.search(r'\n\t\t\(layer "([^"]+)"\)', f['b']).group(1)[0]
        flip = side != layer
        nb = rewrite(f['b'], round(148.5 + fx, 4), round(105 - fy, 4), a, flip)
        if nb != f['b']:
            t = t[:f['s']] + nb + t[f['e']:]; moved += 1; flipped += flip
    open(PCB, 'w').write(t)
    print('rewritten', moved, 'flipped', flipped)
