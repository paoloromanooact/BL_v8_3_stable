import importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'python'))
s=importlib.util.spec_from_file_location('feas',R/'scripts/sft_observed_feasibility.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
k=dict(CTYPE1='CRLN-CEA',CTYPE2='CRLT-CEA',CUNIT1='degree',CUNIT2='degree',CRPIX1=400.5,CRPIX2=300.5,CRVAL1=15.,CRVAL2=15.,CDELT1=.03,CDELT2=.03,CROTA2=0.)
a=m.feasibility(k,dict(k,CRVAL1=15.4),2.)
b=m.feasibility(k,dict(k,CRVAL1=375.4),2.)
c=m.feasibility(dict(k,CRVAL1=375.),dict(k,CRVAL1=15.4),2.)
x=dict(baseline=a,control_plus_360=b,primary_plus_360=c,area_differences=[b[0]-a[0],c[0]-a[0]])
print(json.dumps(x,indent=2));Path('/tmp/bl_sft_evening_review/GEOMETRY.json').write_text(json.dumps(x,indent=2)+'\n')
