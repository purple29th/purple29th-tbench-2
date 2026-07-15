import sys,struct
def solve(p):
 d=open(p,"rb").read(); assert d[:4]==b"CSG1"; nc=struct.unpack_from("<I",d,8)[0]; ec=struct.unpack_from("<I",d,12)[0]; root=struct.unpack_from("<I",d,16)[0]; fail=struct.unpack_from("<I",d,20)[0]; off=64; nodes={}
 for _ in range(nc): nid,t,w=struct.unpack_from("<iBi",d,off)[:3]; nodes[nid]=(t,w); off+=16
 children={}
 for _ in range(ec): a,b=struct.unpack_from("<ii",d,off); off+=8; children.setdefault(a,[]).append(b)
 stack=[fail]; seen=set(); total=0
 while stack:
  n=stack.pop()
  if n in seen: continue
  seen.add(n)
  if n in nodes:
   t,w=nodes[n]; total+=w
   if t==1: continue
   for ch in children.get(n,[]): stack.append(ch)
  else:
   for ch in children.get(n,[]): stack.append(ch)
 return total
if __name__=="__main__": print(solve(sys.argv[1]) if len(sys.argv)>1 else 0)
