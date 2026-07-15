import os,struct,subprocess,pytest
SCRIPT="/app/solve.py";HELDOUTS=["/tests/data/heldout_1.sdb","/tests/data/heldout_2.sdb","/tests/data/heldout_3.sdb"]
def ref(p):
 d=open(p,"rb").read();assert d[:4]==b"CSG1";nc=struct.unpack_from("<I",d,8)[0];ec=struct.unpack_from("<I",d,12)[0];root=struct.unpack_from("<I",d,16)[0];fail=struct.unpack_from("<I",d,20)[0];off=64;nodes={}
 for _ in range(nc):nid,t,w=struct.unpack_from("<iBi",d,off)[:3];nodes[nid]=(t,w);off+=16
 children={}
 for _ in range(ec):a,b=struct.unpack_from("<ii",d,off);off+=8;children.setdefault(a,[]).append(b)
 stack=[fail];seen=set();total=0
 while stack:
  n=stack.pop()
  if n in seen:continue
  seen.add(n)
  if n in nodes:
   t,w=nodes[n];total+=w
   if t==1:continue
   for ch in children.get(n,[]):stack.append(ch)
  else:
   for ch in children.get(n,[]):stack.append(ch)
 return total
def run(p):assert os.path.exists(SCRIPT);o=subprocess.run(["python3",SCRIPT,p],capture_output=True,text=True,timeout=60);assert o.returncode==0;return int(o.stdout.strip().split()[-1])
def test_exists():assert os.path.exists(SCRIPT)
def test_from_scratch():
 s=open(SCRIPT).read().replace(" ","")
 for b in ["networkx","igraph","importnumpy","importpandas","subprocess.","os.system","os.popen","__import__(","importlib"]:assert b not in s
@pytest.mark.parametrize("p",HELDOUTS)
def test_heldout(p):assert run(p)==ref(p)
