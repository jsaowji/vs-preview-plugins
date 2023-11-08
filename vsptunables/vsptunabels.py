from __future__ import annotations

from vspreview.plugins import AbstractPlugin, PluginConfig

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget, QDoubleSpinBox, QCheckBox, QScrollArea
from vspreview.core import HBoxLayout, VBoxLayout, FrameEdit, Stretch, PushButton, Frame
from vspreview.main import MainWindow
from functools import partial
from vstools import vs, core
from typing import Callable, Any, Sequence
from stgpytools import iterate

__all__ = [
    'Tunables',
]

class Tunables(AbstractPlugin, QWidget):
    _config = PluginConfig('dev.jsaowji.tunables', 'Tunables')
    tunables: list[list[int | bool | float]]
    tunables_names: list[list[str]]
    tunables_nodes: list[tuple[vs.VideoNode, vs.VideoNode]]
    caches: list[dict[Any, Any]]

    def __init__(self, main: MainWindow) -> None:
        super().__init__(main)

        self.clear_tunables()

        self.main.reload_before_signal.connect(self.clear_tunables)


    def setup_ui(self) -> None:
        self.main.reload_after_signal.connect(self.reload_after)

        self.update_list()

    def reload_after(self) -> None:
        QWidget().setLayout(self.layout())
        self.update_list()

    def update_list(self) -> None:
        lst = []
        for tun, nam in zip(self.tunables, self.tunables_names):
            for i, a in enumerate(tun):
                if isinstance(a, bool):
                    fe1 = QCheckBox()
                    fe1.setChecked(a)

                    def asd1(a: list[int | bool | float], b: int, c: QCheckBox, d: Tunables) -> None:
                        a[b] = c.isChecked()

                        d.flush_all_caches()

                    fna = partial(asd1, a=tun, b=i, c=fe1, d=self)
                    fe1.stateChanged.connect(fna)
                    lst += [HBoxLayout([
                        QLabel(f"{nam[i]}"), fe1
                    ])]
                elif isinstance(a, int):
                    fe2 = FrameEdit()
                    fe2.setMinimum(Frame(-100000000))
                    fe2.setMaximum(Frame(100000000))
                    fe2.setValue(Frame(a))

                    def asd2(a: list[int | bool | float], b: int, c: FrameEdit, d: Tunables) -> None:
                        a[b] = int(c.value())

                        d.flush_all_caches()
               
                    fna = partial(asd2, a=tun, b=i, c=fe2, d=self)
                    fe2.valueChanged.connect(fna)
                    lst += [HBoxLayout([
                        QLabel(f"{nam[i]}"), fe2
                    ])]
                elif isinstance(a, float):
                    fe3 = QDoubleSpinBox()
                    fe3.setMinimum(-1.175494e38)
                    fe3.setMaximum(1.175494e38)

                    fe3.setSingleStep(0.1)
                    fe3.setValue(a)

                    def asd(a: list[int | bool | float], b: int, c: QDoubleSpinBox, d: Tunables) -> None:
                        a[b] = c.value()

                        d.flush_all_caches()                            
                        

                    fna = partial(asd, a=tun, b=i, c=fe3, d=self)
                    fe3.valueChanged.connect(fna)
                    lst += [HBoxLayout([
                        QLabel(f"{nam[i]}"), fe3
                    ])]

        self.scrolla = QScrollArea()
        self.widget = QWidget()
        self.vbox = VBoxLayout([ PushButton("Clear node cache",clicked=self.clear_node_cache)] + lst + [Stretch(0)])

        self.widget.setLayout(self.vbox)

        self.scrolla.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn) # type: ignore
        self.scrolla.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # type: ignore
        self.scrolla.setWidgetResizable(True)
        self.scrolla.setWidget(self.widget)

        VBoxLayout(self, [self.scrolla])
    
    def flush_all_caches(self) -> None:
        # Does not work
        #from vstools.utils.vs_proxy import clear_cache
        #clear_cache()

        clear_cache()

        self.main.switch_frame(self.main.current_output.last_showed_frame)

    def clear_node_cache(self) -> None:
        for a in self.caches:
            a.clear()

    def clear_tunables(self) -> None:
        self.tunables = []
        self.tunables_names = []
        self.tunables_nodes = []
        self.caches = []

    def tunable(self, input_clip: vs.VideoNode, v: list[int | float | bool], nam: list[str] | None, lm: Callable[[vs.VideoNode, Sequence[int | float | bool]], vs.VideoNode]) -> vs.VideoNode:
        assert isinstance(v,list)
        
        self.tunables += [v]

        if nam is None:
            nam = [f"{len(self.tunables)}"] * len(v)
        else:
            assert len(nam) == len(v)
        
        self.tunables_names += [nam]

        reta: vs.VideoNode

        if True:
            def cache_clips(n:int, a: vs.VideoNode, b: list[int | float | bool], lm: Callable[[vs.VideoNode, Sequence[int | float | bool]], vs.VideoNode], nam2: list[str], cache: dict[Any, vs.VideoNode]) -> vs.VideoNode:
                #print(f"{n} for {b} {nam2}")
                b2 = tuple(b)
                if not b2 in cache:
                    rnd = wrap_error(a, lambda: lm(a, b2))
                    lel = rnd.text.Text(f"{b2}        {nam2}               ")
                    cache[b2] = lel
                return cache[b2]
            cache: dict[Any, vs.VideoNode] = {}
            self.caches += [cache]
            fanc = partial(cache_clips, a=input_clip, b=v, lm=lm, nam2=nam,cache=cache)
            n0 = fanc(0)

            cached = core.std.FrameEval(n0, fanc, clip_src=[input_clip])

            reta = cached

        self.tunables_nodes += [ (input_clip,reta) ]
        return reta

def wrap_error(format_node: vs.VideoNode, lmbda: Callable[[], vs.VideoNode]) -> vs.VideoNode:
    try:
        return lmbda()
    except:
        import traceback
        var = traceback.format_exc()
        print(var)
        return format_node.std.BlankClip().text.Text(f"{var}")

def clear_cache() -> None:
    cache_size = int(core.max_cache_size)

    core.max_cache_size = 1

    #take up memory with fixed size cache, that wont be free
    fc = core.std.BlankClip(width=1024,height=1024,format=vs.GRAY8,length=15)
    fc.std.SetVideoCache(1,fixedsize=len(fc))
    list(fc.frames())

    # force flush all other caches
    list(iterate(fc, core.std.FlipHorizontal, 12).frames())

    del fc
    #call gc_freellist for good measure with the lower limit again
    core.max_cache_size = 1

    core.max_cache_size = cache_size


        #core.std.SetVideoCache(cached, 0)

        #rebuild tree everytime
        #this would also need graph api enable for the case where you use cached nodes between tunables
        #if (not input_clip.is_inspectable(0)) and False:
        #    def make_frameval(fna) -> vs.VideoNode:
        #        def ina(n, b):
        #            try:
        #                return b()
        #            except:
        #                import traceback
        #                var = traceback.format_exc()
        #                print(var)
        #        a = core.std.FrameEval(fna(), partial(ina, b=fna))
        #        core.std.SetVideoCache(a, 0)
        #        return a
        #    raw_frameeval = make_frameval(lambda a=input_clip, b=v, we=wrap_error: we(
        #        a, lambda: lm(a, b).text.Text(f"{b}")))
        #    reta = raw_frameeval
        #else:

#cache clearning code
#        visited = set()
#        for a in self.tunables_nodes:
#            set_caching_all_deps(a[0], [0, -1], visited)
#            set_caching_all_deps(a[1], [0, -1], visited)
#        for a in self.caches:
#            for b in a.values():
#                set_caching_all_deps(b, [0, -1], visited)
#        for a in self.main.outputs.items:
#            set_caching_all_deps(a.source.clip, [0,-1], visited)
#            set_caching_all_deps(a.prepared.clip, [0, -1], visited)
#            #if i <= self.main.current_output.index:
#            #    a.render_frame(self.main.current_output.last_showed_frame)
#def set_caching_all_deps(current: vs.VideoNode, mode, visited: set[int]):
#    if hash(current) in visited:
#        return
#    if isinstance(mode,list):
#        for a in mode:
#            core.std.SetVideoCache(current, a)
#    else:
#        core.std.SetVideoCache(current, mode)
#    for d in list(current._dependencies):
#        set_caching_all_deps(d, mode,visited)
#    visited.add(hash(current))
#
#def set_caching_between(current: vs.VideoNode, to_search: vs.VideoNode,mode:int):
#    disab = False
#    for d in list(current._dependencies):
#        if d == to_search:
#            disab = True
#            continue
#        if set_caching_between(d, to_search):
#            disab = True
#        
#    if disab:
#        core.std.SetVideoCache(current, mode)
#
#    return disab