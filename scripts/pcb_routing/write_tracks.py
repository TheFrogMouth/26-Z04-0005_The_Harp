"""Write routed tracks and vias (build/routes.json) into the board file.

Removes every track and via already on the board first, so it can be rerun.
Usage: python3 write_tracks.py [routes.json]
"""
import os, sys, json, re, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kpcb, nets


def uid():
    return str(uuid.uuid4())


def block_re(name):
    return re.compile(r'\n\t\(%s\n.*?\n\t\)' % name, re.S)


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def render(items):
    out = []
    for w in items:
        if w['type'] == 'via':
            d, dr = nets.VIA
            out.append('\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n\t\t(layers "F.Cu" "B.Cu")\n'
                       '\t\t(net "%s")\n\t\t(uuid "%s")\n\t)' % (fmt(w['x']), fmt(w['y']), fmt(d), fmt(dr), w['net'], uid()))
        else:
            for (x1, y1), (x2, y2) in zip(w['pts'], w['pts'][1:]):
                if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
                    continue
                out.append('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n'
                           '\t\t(net "%s")\n\t\t(uuid "%s")\n\t)' % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), fmt(w['w']),
                                                                   w['layer'], w['net'], uid()))
    return out


def main(src):
    items = json.load(open(src))
    t = open(kpcb.PCB).read()
    t = block_re('segment').sub('', t)
    t = block_re('via').sub('', t)
    # tracks go after the last footprint, before the board graphics, as KiCad saves them
    k = t.find('\n\t(gr_')
    body = render(items)
    t = t[:k] + '\n' + '\n'.join(body) + t[k:]
    open(kpcb.PCB, 'w').write(t)
    print('segments', sum(1 for b in body if b.startswith('\t(segment')), 'vias', sum(1 for b in body if b.startswith('\t(via')))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(kpcb.BUILD, 'routes.json'))
