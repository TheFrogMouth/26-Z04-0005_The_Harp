"""Draw the routed board from the board file: F.Cu, B.Cu and In2.Cu, tracks coloured by net class.

Usage: python3 render.py [out.png]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kpcb, nets, check
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle

POUR = {'+3V3': '#ff9900', '+5V': '#cc0000', '+9V': '#0055cc'}
COL = {'GND': '#7a7a7a', 'RAIL': '#9467bd', 'POWER': '#d62728', 'AUDIO': '#1f77b4', 'DIGITAL': '#ff7f0e', 'CTRL': '#2ca02c', None: '#c8c8c8'}


def kind(n):
    return nets.kind(n) if n and not n.startswith('unconnected') else None


def main(out):
    text, tree, fps, pads = kpcb.load()
    segs, vias = check.tracks(tree)
    o = kpcb.outline(tree)
    fig, axs = plt.subplots(1, 3, figsize=(24, 13.5))
    for ax, L in zip(axs, ['F.Cu', 'B.Cu', 'In2.Cu']):
        ax.add_patch(MP(o, fill=False, color='k', lw=1))
        for p in pads:
            if L not in p['layers'] or p['kind'] == 'np_thru_hole':
                continue
            ax.add_patch(MP(kpcb.pad_polygon(p), color=COL[kind(p['net'])], alpha=0.35, lw=0))
        for z in kpcb.findall(tree, 'zone'):          # pours on this layer
            if kpcb.find(z, 'layer')[1] == L and L != 'In1.Cu':
                zp = [(float(c[1]), float(c[2])) for c in kpcb.find(kpcb.find(z, 'polygon'), 'pts') if isinstance(c, list)]
                zn = kpcb.find(z, 'net')[1]
                ax.add_patch(MP(zp, color=POUR.get(zn, '#999999'), alpha=0.28, lw=0.5, ec=POUR.get(zn, '#999999')))
        for s in segs:
            if s['layer'] != L:
                continue
            ax.plot([s['a'][0], s['b'][0]], [s['a'][1], s['b'][1]], color=COL[kind(s['net'])],
                    lw=s['w'] * 72 / 25.4 * 2.2, solid_capstyle='round')
        for v in vias:
            ax.add_patch(Circle((v['x'], v['y']), v['d'] / 2, color=COL[kind(v['net'])], ec='k', lw=0.3))
        for f in fps:
            if f['side'] == L[0] or L == 'In2.Cu':
                pass
        ax.set_xlim(119, 178); ax.set_ylim(145, 46); ax.set_aspect(1)
        ax.set_title('%s (top view)' % L); ax.tick_params(labelsize=6)
    handles = [plt.Line2D([], [], color=c, lw=3, label=k) for k, c in COL.items() if k]
    axs[0].legend(handles=handles, loc='upper left', fontsize=8)
    plt.tight_layout()
    plt.savefig(out, dpi=90)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(kpcb.BUILD, 'routed.png'))
