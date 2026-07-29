#!/usr/bin/env python3
import struct, sys

def parse(path):
    data=open(path,'rb').read()
    assert data[:4]==b"SEIS"
    off=struct.unpack_from("<I",data,8)[0]
    n=struct.unpack_from("<I",data,12)[0]
    dt=struct.unpack_from("<f",data,16)[0]
    vals=[float(v) for v in struct.unpack_from(f"<{n}h", data, off)]
    return n, dt, vals

def median(s):
    s=sorted(s); m=len(s)
    if m==0: return 0.0
    return s[m//2] if m%2 else 0.5*(s[m//2-1]+s[m//2])

def solve_one(p):
    n, dt, vals = parse(p)
    # background from first 50 samples (safe even for P at 80)
    early_n = min(50, n//10)
    early = vals[:early_n]
    bg = median(early)
    # MAD noise from early
    med = median(early)
    mad = median(sorted(abs(v-med) for v in early))
    sigma = max(2.0, 1.4826*mad)

    resid = [v-bg for v in vals]
    abs_r = [abs(x) for x in resid]

    sta_t = 0.05
    lta_t = 0.25
    sta_n = max(5, int(sta_t/dt))
    lta_n = max(sta_n*2, int(lta_t/dt))

    # cumulative sum for fast mean
    cumsum=[0.0]
    for x in abs_r:
        cumsum.append(cumsum[-1]+x)

    def mean_abs(a,b): # [a,b)
        if a<0: a=0
        if b>n: b=n
        if b<=a: return 0.0
        return (cumsum[b]-cumsum[a])/(b-a)

    sta=[0.0]*n
    lta=[0.0]*n
    ratio=[0.0]*n
    for i in range(n):
        sta[i]= mean_abs(i-sta_n+1, i+1)
        lta_start = i-sta_n - lta_n +1
        lta_end = i-sta_n+1
        if lta_end>0:
            lta[i]= mean_abs(lta_start, lta_end)
            if lta[i]<sigma*0.5:
                lta[i]=sigma*0.5
        else:
            lta[i]=sigma
        if lta[i]>0:
            ratio[i]=sta[i]/lta[i]
        else:
            ratio[i]=0

    thresh=4.0
    # we will scan and require ratio above thresh and abs above 3 sigma and sustained
    min_sustain = max(sta_n, int(0.08/dt))  # 80ms sustain
    best_onset=None
    candidates=[]
    for i in range(early_n, n):
        if ratio[i] < thresh: continue
        if abs_r[i] < 3.5*sigma: continue
        # sustain check: next min_sustain samples average ratio > thresh*0.7 and abs mean > 2 sigma
        end = min(n, i+min_sustain)
        # quick check: count how many in window above thresh*0.6
        cnt=0
        sum_r=0
        for j in range(i, end):
            if ratio[j] > thresh*0.6:
                cnt+=1
            sum_r+=abs_r[j]
        if cnt < min_sustain*0.7:
            continue
        if sum_r/min_sustain < 2.5*sigma:
            continue
        candidates.append(i)
        # backtrack to find actual onset where signal first exceeds 2 sigma
        onset=i
        back = min(i, int(0.03/dt)+sta_n)  # 30ms backtrack
        for k in range(i, max(early_n, i-back)-1, -1):
            if abs_r[k] < 2.0*sigma:
                onset=k+1
                break
        best_onset=onset
        break

    if best_onset is not None:
        print(best_onset)
        return

    # fallback brute: first sample where abs exceeds 5 sigma for sustained 20 samples
    for i in range(early_n, n-20):
        if abs_r[i] > 5*sigma:
            # check next 20 avg >3 sigma
            if sum(abs_r[i:i+20])/20 > 3*sigma:
                print(i)
                return
    print(0)

if __name__=="__main__":
    if len(sys.argv)<2:
        print(0)
    else:
        solve_one(sys.argv[1])
