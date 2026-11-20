"""Rehearse final MWO tools in an isolated temporary source tree. Synthetic fixtures only.
Statistical modules and data of the running validation remain untouched. No real data tree is linked.
The stages have separate synthetic fixtures; this is an integration/guard rehearsal, not calibration of M.
"""
import hashlib,os,shutil,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    protected=['scripts/t3_mwo_analysis.py','python/sharpbl/p2f_validation.py','python/sharpbl/p2f_pilot.py','python/sharpbl/p2d.py','results/T3_MWO_CATALOGUE_R4/DESIGN.csv','results/T3_MWO_DESIGN_CHECK_R4/TARGETS.json']
    before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in protected}
    commands=[['t3_mwo_stability_wiring_probe.py'],['t3_mwo_stability_recount.py','--selftest'],
              ['t3_mwo_estimate_recount.py','--selftest'],['t3_mwo_estimate_recount_review_probe.py'],
              ['t3_mwo_release_recount.py','--selftest']]
    with tempfile.TemporaryDirectory(prefix='mwo_final_sequence_') as td:
        tree=Path(td);(tree/'scripts').mkdir()
        for p in (ROOT/'scripts').glob('t3_mwo_*.py'):shutil.copyfile(p,tree/'scripts'/p.name)
        for name in ['python','docs','patches']:(tree/name).symlink_to(ROOT/name,target_is_directory=True)
        # Neither data/ nor results/ is linked: accidental real-data access fails in this tree.
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR=str(tree/'mpl'))
        for args in commands:
            r=subprocess.run([sys.executable,str(tree/'scripts'/args[0]),*args[1:]],cwd=tree,env=env,capture_output=True,text=True)
            if r.returncode:
                print(r.stdout[-5000:]);print(r.stderr[-3000:]);raise RuntimeError('stage failed: '+' '.join(args))
            print('PASS '+' '.join(args),flush=True)
    assert before=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in protected}
    print('PASS final-tool rehearsal; no production source/input changed; no real tilt read')
if __name__=='__main__':main()
