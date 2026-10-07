#!/usr/bin/env python3
"""Write the Harp schematic from harp_spec.py and the hand layouts in layouts/.

    python3 build_layout.py [SHEET ...]      # default: every sheet with a layout, plus the top sheet

Then re-reads every written sheet, traces its nets and compares them pin by
pin with the spec (same check as build.py), and runs the layout checks.
"""
import sys, os, re, importlib
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
import schgen
from schgen import POWER_NETS
from harp_spec import SHEETS
from layout import Layout, number_power
from kisch import parse, sheet_nets
from collections import defaultdict

OUT = os.path.join(S, '..', '..', 'kicad', 'the_harp')
PROJECT = 'The Harp'
ROOT_UUID = '596641a7-eeca-47a8-9244-68f1910acd88'

use = defaultdict(set)
for sh in SHEETS:
    for p in sh.parts:
        for n in p.pins.values():
            if n and n not in POWER_NETS:
                use[n].add(sh.name)
GLOB = {n for n, s in use.items() if len(s) > 1}


def module_name(sheet):
    return re.sub(r'[^a-z0-9]+', '_', sheet.name.lower()).strip('_')


def verify(sheet, path, allow_local=()):
    """Pin-by-pin: every spec net is one node, no node holds two spec nets, every rail and
    global net carries its name, every None pin has a no-connect, nothing extra."""
    root = parse(open(path).read())
    pins, labels = sheet_nets(root)
    bad = []
    spec = {}
    for p in sheet.parts:
        for nb, n in p.pins.items():
            spec[(p.ref, nb)] = n
    # nodes joined by a power symbol or global label of the same name are one net
    alias = {}
    byname = {}
    for node, labs in labels.items():
        for kind, name in labs:
            if kind in ('global', 'power', 'local') and name != 'PWR_FLAG':
                alias[node] = byname.setdefault(name, node)
    node_of = {}
    for ref, nb, nm, node in pins:
        node_of.setdefault((ref, nb), set()).add(alias.get(node, node))
    merged = defaultdict(set)
    for node, labs in labels.items():
        merged[alias.get(node, node)] |= labs
    labels = merged
    for k in spec:
        if k not in node_of:
            bad.append('MISSING PIN %s' % (k,))
    for k in node_of:
        if k not in spec:
            bad.append('EXTRA PIN %s' % (k,))
    # stacked pins (several VSS at one point) share a node; a pin may appear once per unit drawing
    net_nodes = defaultdict(set)
    for k, n in spec.items():
        for node in node_of.get(k, ()):
            net_nodes[n].add(node)
    node_nets = defaultdict(set)
    for n, nodes in net_nodes.items():
        for node in nodes:
            node_nets[node].add(n)
    for n, nodes in net_nodes.items():
        if n is not None and len(nodes) > 1:
            bad.append('net %s is split into %d pieces' % (n, len(nodes)))
    for node, nets in node_nets.items():
        if len(nets) > 1:
            bad.append('short: %s on one node' % sorted(map(str, nets)))
    for n, nodes in net_nodes.items():
        names = set()
        kinds = set()
        for node in nodes:
            for kind, name in labels.get(node, ()):
                kinds.add(kind)
                if kind in ('global', 'power') and name != 'PWR_FLAG':
                    names.add(name)
        if n is None:
            if kinds - {'nc'}:
                bad.append('a no-connect pin is wired: %s' % sorted(kinds))
            continue
        if n in POWER_NETS or n in GLOB:
            if names != {n}:
                bad.append('net %s carries names %s' % (n, sorted(names)))
        else:
            if names:
                bad.append('local net %s carries names %s' % (n, sorted(names)))
        if 'local' in kinds and n not in allow_local:
            bad.append('net %s has a local label' % n)
    return bad


def main(names):
    texts, outs, layouts = [], [], []
    for sh in SHEETS:
        if names and sh.name not in names:
            continue
        mod = module_name(sh)
        try:
            m = importlib.import_module('layouts.' + mod)
        except ModuleNotFoundError as e:
            if names:
                raise
            print('%-22s no layout (layouts/%s.py)' % (sh.name, mod))
            continue
        L = Layout(sh, GLOB, PROJECT, ROOT_UUID)
        m.layout(L)
        texts.append(L.emit())
        outs.append(sh)
        layouts.append(L)
    if not names:
        texts = number_power(texts)
        import top_sheet
        open(os.path.join(OUT, 'The Harp.kicad_sch'), 'w').write(top_sheet.build(SHEETS, ROOT_UUID, PROJECT))
        print('top sheet written')
    ok = True
    for sh, t, L in zip(outs, texts, layouts):
        path = os.path.join(OUT, sh.fname)
        open(path, 'w').write(t)
        bad = verify(sh, path, getattr(L, 'allow_local', ()))
        probs, cross = L.check()
        print('%-22s parts %3d wires %3d junctions %2d crossings %d netlist %s layout %s'
              % (sh.name, len(L.placed), len(L.wires), len(L.junctions()), cross,
                 'OK' if not bad else 'BAD', 'OK' if not probs else '%d warnings' % len(probs)))
        for b in bad:
            print('   NET  ', b)
            ok = False
        for p in probs:
            print('   WARN ', p)
    return ok


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1:]) else 1)
