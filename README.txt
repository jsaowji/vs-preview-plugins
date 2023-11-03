# how to install 
symlink the .pys into your .vspreview/plugins as .ppy


For tunables it is advised to have the helper in pythonpath / site-packages

example for tunables

```python
from vsptunables_helper import tunable
from vstools import vs,core,set_output
clip = ....

clip.set_output(0)

def rekt_lvls(a,b):
    from rekt import rektlvls

    return rektlvls(a, colnum=[0,1,2,3],colval=b)
def rekt_lvls2(a,b):
    from rekt import rektlvls

    return rektlvls(a, colnum=[-1,-2,-3,-4],colval=b)
def filborder(a:vs.VideoNode,b):
    return a.fb.FillBorders(b[0],b[1],mode=["repeat","mirror","fillmargins","fixborders"][b[2]])

clip = tunable(clip, [0,70,48,24],["0","1","2","3"], rekt_lvls)
clip = tunable(clip, [0,50,23,0], ["0","1","2","3"], rekt_lvls2)
set_output(clip,"lvls",cache=False)
```