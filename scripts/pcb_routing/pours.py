"""Replace the rail tracks on In2.Cu with copper pours (zones): one region each for +3V3, +5V, +9V.

1. The rails' existing tracks on In2.Cu (a valid planar layout, from Freerouting) are the backbone
   of each pour: they already join every via and through-hole pin of their rail.
2. Every other point of In2 goes to the nearest backbone (distance transform); each region is pulled
   in 0.12 mm so different rails never touch, the backbone is added back, then the result is smoothed,
   held 0.5 mm from the board edge and written as zones (holes split off: a zone outline has none).
3. The fill is imitated (foreign copper plus 0.2 mm cleared, 0.25 mm minimum width) and every
   terminal is checked to be joined to the rest of its rail.

The In2 tracks of the rails are removed from the board. In KiCad press B to fill; the fill makes
the clearances and the antipads round foreign vias. Needs the tracks to be there: rerun only from
a board file that still has them (the script refuses otherwise).

Usage: python3 pours.py        (edits the board file in place)
"""
import os, sys, re, uuid, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from scipy import ndimage as ndi
from shapely.geometry import Polygon, MultiPolygon, Point, LineString, box
from shapely.ops import unary_union
from skimage.graph import MCP_Geometric
import kpcb, nets, check, regions

RES = 0.1
import math
RAILS = ['+9V', '+5V', '+3V3']                # zone priorities 0, 1, 2
BRIDGE_ORDER = ['+5V', '+3V3', '+9V']
CLR = 0.2                                     # zone clearance to other nets
HOLE = 0.3                                    # copper pull-back from a hole's edge
EDGE = 0.5
MINW = 0.25
HUG = 1.5                                     # bridge paths hug obstacles and edges, leaving the middle open
GAP = 0.12                                    # each region is pulled in by this, so rails keep 0.24+


def terminals(pads, vias, net):
    out = []
    for v in vias:
        if v['net'] == net:
            out.append((v['x'], v['y']))
    for p in pads:
        if p['net'] == net and p['kind'] == 'thru_hole':
            out.append((p['x'], p['y']))
    return out


def obstacles(pads, vias):
    """Foreign copper on In2 as (geometry, net): vias, through-hole pads (real shapes), mounting holes."""
    out = []
    for v in vias:
        out.append((Point(v['x'], v['y']).buffer(v['d'] / 2), v['net']))
    for p in pads:
        if p['kind'] == 'thru_hole':
            out.append((Polygon(kpcb.pad_polygon(p)), p['net']))
        elif p['kind'] == 'np_thru_hole':
            out.append((Point(p['x'], p['y']).buffer(p['w'] / 2 + (HOLE - CLR)), None))
    return out


class G:
    def __init__(self, outline):
        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        self.x0, self.y0 = min(xs) - 1, min(ys) - 1
        self.nx = int((max(xs) - self.x0 + 1) / RES) + 1
        self.ny = int((max(ys) - self.y0 + 1) / RES) + 1
        gx = self.x0 + np.arange(self.nx) * RES; gy = self.y0 + np.arange(self.ny) * RES
        self.X, self.Y = np.meshgrid(gx, gy)

    def cell(self, x, y):
        return int(round((y - self.y0) / RES)), int(round((x - self.x0) / RES))

    def xy(self, j, i):
        return self.x0 + i * RES, self.y0 + j * RES

    def polymask(self, poly):
        from matplotlib.path import Path
        m = np.zeros((self.ny, self.nx), bool)
        polys = list(poly.geoms) if poly.geom_type == 'MultiPolygon' else [poly]
        for p in polys:
            x0, y0, x1, y1 = p.bounds
            j0, i0 = self.cell(x0, y0); j1, i1 = self.cell(x1, y1)
            j0, i0 = max(j0 - 1, 0), max(i0 - 1, 0); j1, i1 = min(j1 + 2, self.ny), min(i1 + 2, self.nx)
            pts = np.stack([self.X[j0:j1, i0:i1].ravel(), self.Y[j0:j1, i0:i1].ravel()], 1)
            ins = Path(np.asarray(p.exterior.coords)).contains_points(pts)
            for h in p.interiors:
                ins &= ~Path(np.asarray(h.coords)).contains_points(pts)
            m[j0:j1, i0:i1] |= ins.reshape(j1 - j0, i1 - i0)
        return m


def main():
    text, tree, fps, pads = kpcb.load()
    outline = kpcb.outline(tree)
    board = Polygon(outline)
    segs, vias = check.tracks(tree)
    g = G(outline)
    inside = g.polymask(board.buffer(-EDGE))
    obs = obstacles(pads, vias)

    backbone, used = {}, {}
    for net in RAILS:
        parts = [LineString([w['a'], w['b']]).buffer(w['w'] / 2) for w in segs
                 if w['layer'] == 'In2.Cu' and w['net'] == net]
        if not parts:
            raise SystemExit('no In2 tracks for %s in the board file: it has been converted already' % net)
        parts += [Point(x, y).buffer(0.3) for (x, y) in terminals(pads, vias, net)]
        backbone[net] = unary_union(parts)
        used[net] = max(w['w'] for w in segs if w['layer'] == 'In2.Cu' and w['net'] == net) / 2
    # close the gaps the track layout left in a rail (its open connections): short extra paths
    def groups_of(net):
        keepout = unary_union([gm.buffer(CLR) for (gm, n) in obs if n != net])
        filled = backbone[net].difference(keepout).buffer(-MINW / 2).buffer(MINW / 2)
        comps = list(filled.geoms) if filled.geom_type == 'MultiPolygon' else [filled]
        terms = terminals(pads, vias, net)
        grp = {}
        for ti, (x, y) in enumerate(terms):
            for ci, c in enumerate(comps):
                if c.distance(Point(x, y)) < 0.05:
                    grp.setdefault(ci, []).append(ti); break
        return [(comps[ci], ts) for ci, ts in grp.items()], terms

    for net in BRIDGE_ORDER:
        for attempt in range(8):
            grp, terms = groups_of(net)
            if len(grp) <= 1:
                break
            grp.sort(key=lambda q: -len(q[1]))
            blk = ~inside
            for (gm, n) in obs:
                if n != net:
                    blk |= g.polymask(gm.buffer(CLR + 0.17))
            for other in RAILS:
                if other != net:
                    blk |= g.polymask(backbone[other].buffer(0.38))
            main_cells = g.polymask(grp[0][0])
            best = None
            for (gm, ts) in grp[1:]:
                tgt = g.polymask(gm)
                near = ndi.distance_transform_edt(~blk) * RES          # mm to the nearest blockage
                cost = np.where(blk & ~main_cells & ~tgt, 1e9, 1.0 + HUG * np.minimum(near, 6.0))
                starts = [tuple(s) for s in np.argwhere(main_cells)[::7]]
                mcp = MCP_Geometric(cost, fully_connected=True)
                cum, _ = mcp.find_costs(starts)
                cum_t = np.where(tgt, cum, np.inf)
                j, i = np.unravel_index(np.argmin(cum_t), cum_t.shape)
                if np.isfinite(cum_t[j, i]) and cum_t[j, i] < 1e8 and (best is None or cum_t[j, i] < best[0]):
                    best = (cum_t[j, i], mcp, (j, i))
            if best is None:
                print('%-5s cannot bridge %d groups' % (net, len(grp) - 1))
                break
            _, mcp, end = best
            pts = [g.xy(j, i) for (j, i) in mcp.traceback(end)]
            backbone[net] = unary_union([backbone[net], LineString(pts).buffer(0.15)])
            print('%-5s bridged a gap with %.1f mm of path' % (net, LineString(pts).length))

    label = np.zeros((g.ny, g.nx), np.int8)
    for k, net in enumerate(RAILS):
        label[g.polymask(backbone[net])] = k + 1
        print('%-5s %2d terminals, backbone %.0f mm2' % (net, len(terminals(pads, vias, net)), backbone[net].area))
    # nearest backbone owns each remaining cell
    src = label > 0
    dist, idx = ndi.distance_transform_edt(~src, return_indices=True)
    own = label[idx[0], idx[1]]
    regions_poly = {}
    for k, net in enumerate(RAILS):
        cells = (own == k + 1) & inside
        poly = cells_to_poly(g, cells).buffer(-GAP)
        poly = unary_union([poly, backbone[net]]).intersection(board.buffer(-EDGE))
        poly = poly.buffer(0.15).buffer(-0.15).simplify(0.05)
        regions_poly[net] = poly

    # imitate the fill and see which terminals end up joined
    jump = []
    for net in RAILS:
        grp, terms, lost = groups_in_fill(net, regions_poly[net], obs, pads, vias)
        print('%-5s fill: %d terminals in %d joined group(s), %d floating' % (net, len(terms), len(grp), len(lost)))
        if len(grp) > 1 or lost:
            jump += jumpers(g, net, grp, terms, lost, pads, vias, segs, jump, board)
    jump += vdda(g, pads, vias, segs, jump, board)
    write(regions_poly, jump)
    return jump


def vdda(g, pads, vias, segs, done, board, net='VDDA'):
    """The MCU's analog supply is not a pour: join whatever pieces its tracks left apart."""
    items = []                                          # (layer(s), geometry, kind)
    for p in pads:
        if p['net'] == net:
            items.append(({p['layers'][0]}, Polygon(kpcb.pad_polygon(p)), 'pad', (p['x'], p['y'])))
    for sg in segs:
        if sg['net'] == net:
            items.append(({sg['layer']}, LineString([sg['a'], sg['b']]).buffer(sg['w'] / 2), 'trk', None))
    for v in vias:
        if v['net'] == net:
            items.append((set(kpcb.CU), Point(v['x'], v['y']).buffer(v['d'] / 2), 'via', None))
    parent = list(range(len(items)))
    def f(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            if items[a][0] & items[b][0] and items[a][1].distance(items[b][1]) < 1e-3:
                parent[f(a)] = f(b)
    comps = {}
    for i, it in enumerate(items):
        comps.setdefault(f(i), []).append(i)
    terms, grp = [], []
    for ids in comps.values():
        ps = [items[i][3] for i in ids if items[i][2] == 'pad']
        if ps:
            grp.append(list(range(len(terms), len(terms) + len(ps)))); terms += ps
    grp.sort(key=lambda q: -len(q))
    print('%-5s: %d pieces' % (net, len(grp)))
    if len(grp) < 2:
        return []
    return jumpers(g, net, grp, terms, [], pads, vias, segs, done, board, layers=('F.Cu',), w=0.2)


def groups_in_fill(net, poly, obs, pads, vias):
    """Imitate KiCad's fill of one pour: pulled back from foreign copper, thin bits dropped."""
    keepout = unary_union([gm.buffer(CLR) for (gm, n) in obs if n != net])
    filled = poly.difference(keepout).buffer(-MINW / 2).buffer(MINW / 2)
    comps = list(filled.geoms) if filled.geom_type == 'MultiPolygon' else [filled]
    terms = terminals(pads, vias, net)
    grp, lost = {}, []
    for ti, (x, y) in enumerate(terms):
        for ci, c in enumerate(comps):
            if c.distance(Point(x, y)) < 0.05:
                grp.setdefault(ci, []).append(ti); break
        else:
            lost.append(ti)
    return sorted(grp.values(), key=lambda ts: -len(ts)), terms, lost


def jumpers(g, net, grp, terms, lost, pads, vias, segs, done, board, layers=('F.Cu', 'B.Cu'), w=0.4):
    """Short tracks on F.Cu or B.Cu joining each cut-off group of a rail to its main group."""
    out = []
    need = w / 2 + nets.CLEAR[nets.kind(net)] + 0.04
    groups = [list(q) for q in grp] + [[t] for t in lost]
    cache = {}
    main = groups[0]
    for other in groups[1:]:
        pairs = sorted(((math.dist(terms[a], terms[b]), a, b) for a in main for b in other))[:8]
        done_here = False
        for d, a, b in pairs:
            for L in layers:
                key = (L, len(out))
                if key not in cache:
                    obst = []
                    for p in pads:
                        if L in p['layers'] and p['net'] != net:
                            obst.append(Polygon(kpcb.pad_polygon(p)))
                    for sg in segs + done + out:
                        if sg.get('layer') == L and sg['net'] != net:
                            obst.append(LineString([sg['a'], sg['b']] if 'a' in sg else sg['pts']).buffer(sg['w'] / 2))
                    for v in vias:
                        if v['net'] != net:
                            obst.append(Point(v['x'], v['y']).buffer(v['d'] / 2))
                    cache[key] = g.polymask(unary_union(obst).buffer(need)) | ~g.polymask(board.buffer(-(EDGE + w / 2)))
                blk = cache[key].copy()
                for t in (a, b):
                    free = np.zeros_like(blk)
                    j, i = g.cell(*terms[t])
                    free[max(j - 4, 0):j + 5, max(i - 4, 0):i + 5] = True
                    blk &= ~free
                mcp = MCP_Geometric(np.where(blk, 1e9, 1.0), fully_connected=True)
                ja, ia = g.cell(*terms[a]); jb, ib = g.cell(*terms[b])
                cum, _ = mcp.find_costs([(ja, ia)], [(jb, ib)])
                if not np.isfinite(cum[jb, ib]) or cum[jb, ib] >= 1e8 or cum[jb, ib] * RES > 45:
                    continue
                pts = [g.xy(j, i) for (j, i) in mcp.traceback((jb, ib))]
                line = LineString([terms[a]] + pts + [terms[b]]).simplify(0.03)
                out.append(dict(net=net, layer=L, w=w, pts=[tuple(c) for c in line.coords]))
                print('%-5s jumper on %s: %.1f mm, %s -> %s' % (net, L, line.length, tuple(round(v, 1) for v in terms[a]),
                                                               tuple(round(v, 1) for v in terms[b])))
                main = main + other
                done_here = True; break
            if done_here:
                break
        if not done_here:
            print('%-5s NO jumper found for the group at %s' % (net, [tuple(round(v, 1) for v in terms[t]) for t in other]))
    return out


def cells_to_poly(g, cells):
    """Outline of the grid cells as shapely geometry: traced contours, combined even-odd so holes work."""
    from skimage.measure import find_contours
    pad = np.pad(cells.astype(float), 1)
    polys = []
    for c in find_contours(pad, 0.5):
        if len(c) < 4:
            continue
        pts = [(g.x0 + (col - 1) * RES, g.y0 + (row - 1) * RES) for row, col in c]
        p = Polygon(pts)
        if not p.is_valid:
            p = p.buffer(0)
        if not p.is_empty:
            polys.append(p)
    out = Polygon()
    for p in sorted(polys, key=lambda q: -q.area):
        out = out.symmetric_difference(p)
    return out


def write(region, jump=()):
    path = kpcb.PCB
    t = open(path).read()
    # drop the rails' In2 tracks and any In2 pours from an earlier run
    def drop_tracks(m):
        b = m.group(0)
        if '(layer "In2.Cu")' in b and re.search(r'\(net "(\+3V3|\+5V|\+9V)"\)', b):
            return ''
        return b
    t = re.sub(r'\n\t\(segment\n(?:\t\t[^\n]*\n)*?\t\)', drop_tracks, t)
    t = re.sub(r'\n\t\(zone\n(?:\t\t[^\n]*\n|\t\t\t[^\n]*\n|\t\t\t\t[^\n]*\n|\t\t\t\t\t[^\n]*\n)*?\t\)',
               lambda m: '' if '(layer "In2.Cu")' in m.group(0) else m.group(0), t)
    pieces = []
    for net in RAILS:
        geoms = list(region[net].geoms) if region[net].geom_type == 'MultiPolygon' else [region[net]]
        for p in geoms:
            if p.area >= 1.0:
                pieces.append((net, Polygon(p.exterior)))      # holes filled: a smaller zone beats a bigger one
    pieces.sort(key=lambda q: -q[1].area)                      # priority = rank, the smallest zone on top
    zones = []
    for pr, (net, p) in enumerate(pieces):
        pts = ' '.join('(xy %s %s)' % (fmt(x), fmt(y)) for x, y in list(p.exterior.coords)[:-1])
        zones.append('\t(zone\n\t\t(net "%s")\n\t\t(layer "In2.Cu")\n\t\t(uuid "%s")\n\t\t(name "%s pour")\n'
                     '\t\t(hatch edge 0.5)\n\t\t(priority %d)\n\t\t(connect_pads yes\n\t\t\t(clearance %s)\n\t\t)\n'
                     '\t\t(min_thickness %s)\n\t\t(fill yes\n\t\t\t(thermal_gap 0.25)\n\t\t\t(thermal_bridge_width 0.3)\n'
                     '\t\t\t(island_removal_mode 0)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n\t\t\t\t%s\n\t\t\t)\n\t\t)\n\t)'
                     % (net, uuid.uuid4(), net, pr, fmt(CLR), fmt(MINW), pts))
    tracks = []
    for jm in jump:
        for (x1, y1), (x2, y2) in zip(jm['pts'], jm['pts'][1:]):
            tracks.append('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n'
                          '\t\t(net "%s")\n\t\t(uuid "%s")\n\t)' % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), fmt(jm['w']),
                                                                         jm['layer'], jm['net'], uuid.uuid4()))
    k = t.rfind('\n\t(embedded_fonts')
    t = t[:k] + '\n' + '\n'.join(tracks + zones) + t[k:]
    open(path, 'w').write(t)
    print('zones written: %d (%s)' % (len(zones), ', '.join('%s %d' % (n, sum(1 for q in pieces if q[0] == n)) for n in RAILS)))


def fmt(v):
    return ('%.3f' % v).rstrip('0').rstrip('.')


if __name__ == '__main__':
    main()
