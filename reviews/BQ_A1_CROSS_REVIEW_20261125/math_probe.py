import math,json
from pathlib import Path
checks=[]
def test(name,ok,**values):
    checks.append(dict(name=name,ok=bool(ok),**values))
m=b=1.;em=eb=.005
r=(b-m)/abs(m)
first=(eb+em*(1+abs(r)))/abs(m)
finite=(eb+em*(1+abs(r)))/(abs(m)-em)
perturbed=((b+eb)-(m-em))/abs(m-em)
test('A1 first-order ratio indicator can pass 0.01 while perturbed ratio fails',first<=.01 and perturbed>.01,linear=first,actual=perturbed)
test('Finite perturbation bound covers adverse case',perturbed<=finite*(1+1e-14),bound=finite)
max_excess=0.
for m in [-2.,-.1,.1,2.]:
 for b in [-3.,-.2,.0,.2,3.]:
  em=.05*abs(m);eb=.013;r=(b-m)/abs(m)
  bound=(eb+em*(1+abs(r)))/(abs(m)-em)
  for sm in [-1.,1.]:
   for sb in [-1.,1.]:
    q=((b+sb*eb)-(m+sm*em))/abs(m+sm*em)
    max_excess=max(max_excess,abs(q-r)-bound)
test('Finite bound covers deterministic signed perturbation grid',max_excess<=1e-12,excess=max_excess)
test('Buffer 11 is not independence guarantee under phi .98',.75**11<.05 and .98**11>.8,rho075=.75**11,rho098=.98**11)
nu=4.;t_scale=math.sqrt((nu-2)/nu)
test('Fixed t4 scale preserves prescribed marginal variance',abs(t_scale*t_scale*nu/(nu-2)-1)<1e-14)
# y = k*s + beta*a*s; a2=c*a+d -> k2=k-beta*d/c beta2=beta/c
k,beta,a,s,c,d=24.,-3.,1.7,.3,2.,.5
k2=k-beta*d/c; beta2=beta/c
test('Activity affine transformation preserves mean',math.isclose((k+beta*a)*s,(k2+beta2*(c*a+d))*s,abs_tol=1e-14))
result=dict(scope='Deterministic mathematical checks only; no observed inputs, PDE solution or posterior fit',passed=sum(c['ok'] for c in checks),total=len(checks),checks=checks)
# Reference JSON is immutable; this check prints the recomputed results.
print(json.dumps(result,indent=2))
assert all(c['ok'] for c in checks)
