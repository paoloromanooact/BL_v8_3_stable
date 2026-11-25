"""Independent reachability/arithmetic check of C metadata audit tables, not a FITS recount."""
from pathlib import Path
import argparse,ast,hashlib,json
from collections import deque
import pandas as pd

def run(d):
    nodes=pd.read_csv(d/'NODES.csv');edges=pd.read_csv(d/'EDGES.csv');c=pd.read_csv(d/'CANDIDATES.csv',keep_default_na=False)
    summary=json.loads((d/'SUMMARY.json').read_text());meta=json.loads((d/'META.json').read_text());checks=[]
    def ok(name,test):checks.append(dict(name=name,ok=bool(test)))
    ok('Product hashes match stored metadata',all(hashlib.sha256((d/f).read_bytes()).hexdigest()==h for f,h in meta['products_sha256'].items()))
    ok('Nodes unique and edges reference existing nodes',nodes.node.is_unique and set(edges.node_a)|set(edges.node_b)<=set(nodes.node))
    # Reconstruct all graph edges from exported metadata; no import of audit/union-find.
    ns=nodes.to_dict('records');expected={}
    boxes={int(n['node']):ast.literal_eval(n['bbox']) for n in ns}
    for i,a in enumerate(ns):
        ab=boxes[int(a['node'])]
        for b in ns[:i]:
            bb=boxes[int(b['node'])];why=[]
            if a['harp']==b['harp']:why.append('harp')
            if pd.notna(a['family']) and a['family']==b['family']:why.append('family')
            distance=abs((sum(ab[2:])/2-sum(bb[2:])/2+180)%360-180)
            overlaps=ab[0]<=bb[1] and bb[0]<=ab[1] and distance<=(ab[3]-ab[2]+bb[3]-bb[2])/2
            if a['t0']<=b['t1'] and b['t0']<=a['t1'] and overlaps:why.append('spacetime_bbox')
            if why:expected[(int(b['node']),int(a['node']))]=';'.join(why)
    actual={(int(e.node_a),int(e.node_b)):e.causes for e in edges.itertuples(index=False)}
    ok('Edges reconstructed from exported intervals families and boxes',actual==expected and len(actual)==len(edges))
    adj={int(n):set() for n in nodes.node}
    for a,b in expected:adj[a].add(b);adj[b].add(a)
    protected=set(int(n) for n in nodes.loc[nodes.kind=='pool','node']);q=deque(protected)
    while q:
        for n in adj[q.popleft()]-protected:protected.add(n);q.append(n)
    ok('Protected status agrees with independent breadth-first traversal',all(bool(r.protected_component)==(r.node in protected) for r in c.itertuples(index=False)))
    eligible=(c.pregraph_reasons=='') & ~c.node.isin(protected)
    ok('Provisional eligibility and pair counts consistent',eligible.equals(c.metadata_eligible) and int(eligible.sum())==summary['metadata_eligible_pairs'])
    selected=c[eligible]
    remaining=set(adj);groups={};label=0
    while remaining:
        seed=min(remaining);seen={seed};todo=deque([seed])
        while todo:
            for n in adj[todo.popleft()]-seen:seen.add(n);todo.append(n)
        remaining-=seen
        for n in seen:groups[n]=label
        label+=1
    own=selected.node.map(groups)
    partition_equal=all((own.to_numpy()[:,None]==own.to_numpy()[None,:]).ravel()==(selected.component.to_numpy()[:,None]==selected.component.to_numpy()[None,:]).ravel())
    ok('Selected component partition and unique HARP counts reconstructed',partition_equal and own.nunique()==summary['metadata_eligible_components'] and selected.HARPNUM.nunique()==summary['metadata_eligible_harps'])
    counts=selected.flux_class_provisional.astype(str).value_counts().sort_index().to_dict()
    ok('Flux class counts cover all provisionally eligible pairs',counts==summary['tercile_counts'] and sum(counts.values())==len(selected))
    ok('Lag bins cover provisional sample',int((selected.gap_ns<=5400*10**9).sum())==summary['lag_1h'] and int((selected.gap_ns>5400*10**9).sum())==summary['lag_2h'])
    return dict(scope=__doc__,passed=sum(c['ok'] for c in checks),total=len(checks),checks=checks)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);a=p.parse_args();r=run(a.folder);print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed']==r['total'] else 1)
