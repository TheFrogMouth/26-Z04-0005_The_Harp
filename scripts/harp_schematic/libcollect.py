import glob, re, sys, json
sys.path.insert(0,'/tmp/claude-0/-home-user/35c4c21e-f4e1-555a-91e9-65d2bcae4470/scratchpad')
WS=' \t\r\n'
def top_children(s, start):
    i=start+1; out=[]
    while True:
        while s[i] in ' \t\r\n': i+=1
        if s[i]==')': return out
        if s[i]!='(':
            while s[i] not in WS+'()': i+=1
            continue
        a=i; d=0
        while True:
            ch=s[i]
            if ch=='"':
                i+=1
                while s[i]!='"':
                    if s[i]=='\\': i+=1
                    i+=1
            elif ch=='(': d+=1
            elif ch==')':
                d-=1
                if d==0: break
            i+=1
        out.append(s[a:i+1]); i+=1
def lib_blocks(path):
    s=open(path).read()
    i=s.find('\n\t(lib_symbols')
    if i<0: return {}
    i=s.index('(',i)
    res={}
    for b in top_children(s,i):
        m=re.match(r"\(symbol\s+\"([^\"]*)\"",b)
        if not m: continue
        name=m.group(1)
        res[name]=b
    return res
srcs=sorted(glob.glob('/home/user/25-Z01-0001_DSP_Development_Board/hardware/kicad/dsp_board/*.kicad_sch')+
            glob.glob('/home/user/26-A03-0003_The_Relic/kicad/the_relic/*.kicad_sch')+
            glob.glob('/home/user/26-A02-0001_The_Alchemist/kicad/the_alchemist/*.kicad_sch'))
allb={}
for p in srcs:
    for k,v in lib_blocks(p).items():
        allb.setdefault(k,(p,v))
if __name__=='__main__':
    for k,(p,v) in sorted(allb.items()):
        print(f"{k:55s} {p.split('/')[-1]}")
