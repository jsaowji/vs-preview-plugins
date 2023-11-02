from __future__ import annotations

from vspreview.api.info import is_preview
from vspreview.plugins import AbstractPlugin, PluginConfig

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget, QDoubleSpinBox, QCheckBox, QScrollArea
from vspreview.core import HBoxLayout, VBoxLayout, FrameEdit, Stretch, main_window
from functools import partial
from vstools import vs, core

__all__ = [
    'Tunables',
]

class Tunables(AbstractPlugin, QWidget):
    _config = PluginConfig('dev.jsaowji.tunables', 'Tunables')

    def __init__(self, main) -> None:
        super().__init__(main)

        self.clear_tunables()

        self.main.reload_before_signal.connect(self.clear_tunables)


    def setup_ui(self) -> None:
        self.main.reload_after_signal.connect(self.reload_after)

        self.update_list()

    def reload_after(self):
        QWidget().setLayout(self.layout())
        self.update_list()

    def update_list(self):
        lst = []
        for tun, nam in zip(self.tunables, self.tunables_names):
            for i, a in enumerate(tun):
                if isinstance(a, bool):
                    fe = QCheckBox()
                    fe.setChecked(a)

                    def asd(a, b, c, d:Tunables):
                        a[b] = c.isChecked()

                        d.flush_all_caches()

                    fna = partial(asd, a=tun, b=i, c=fe, d=self)
                    fe.stateChanged.connect(fna)
                    lst += [HBoxLayout([
                        QLabel(f"{nam[i]}"), fe
                    ])]
                elif isinstance(a, int):
                    fe = FrameEdit()
                    fe.setMinimum(-100000000)
                    fe.setMaximum(100000000)
                    fe.setValue(a)

                    def asd(a, b, c, d:Tunables):
                        a[b] = int(c.value())

                        d.flush_all_caches()
               
                    fna = partial(asd, a=tun, b=i, c=fe, d=self)
                    fe.valueChanged.connect(fna)
                    lst += [HBoxLayout([
                        QLabel(f"{nam[i]}"), fe
                    ])]
                elif isinstance(a, float):
                    fe = QDoubleSpinBox()
                    fe.setMinimum(-1.175494e38)
                    fe.setMaximum(1.175494e38)

                    fe.setSingleStep(0.1)
                    fe.setValue(a)

                    def asd(a, b, c, d:Tunables):
                        a[b] = c.value()

                        d.flush_all_caches()                            
                        

                    fna = partial(asd, a=tun, b=i, c=fe, d=self)
                    fe.valueChanged.connect(fna)
                    lst += [HBoxLayout([
                        QLabel(f"{nam[i]}"), fe
                    ])]

        self.scroll = QScrollArea()
        self.widget = QWidget()
        self.vbox = VBoxLayout(lst + [Stretch(0)])

        self.widget.setLayout(self.vbox)

        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        VBoxLayout(self, [self.scroll])
    
    def flush_all_caches(self):
        # Does not work
        from vstools.utils.vs_proxy import clear_cache
        clear_cache()

        self.main.switch_frame(self.main.current_output.last_showed_frame)

    def clear_tunables(self):
        self.tunables = []
        self.tunables_names = []
        self.tunables_nodes = []
        self.caches = []

    def tunable(self, input_clip: vs.VideoNode, v: list[int | float | bool], nam: list[str], lm: callable[vs.VideoNode, list[int | float | bool]]) -> vs.VideoNode:
        assert isinstance(v,list)
        
        self.tunables += [v]

        if nam is None:
            self.tunables_names += [f"{len(self.tunables)}"] * len(v)
        else:
            assert len(nam) == len(v)
            self.tunables_names += [nam]


        reta: vs.VideoNode
        #rebuild tree everytime
        if (not input_clip.is_inspectable(0)) and False:
            def make_frameval(fna) -> vs.VideoNode:
                def ina(n, b):
                    try:
                        return b()
                    except:
                        import traceback
                        var = traceback.format_exc()
                        print(var)
                a = core.std.FrameEval(fna(), partial(ina, b=fna))
                core.std.SetVideoCache(a, 0)
                return a

            raw_frameeval = make_frameval(lambda a=input_clip, b=v, we=wrap_error: we(
                a, lambda: lm(a, b).text.Text(f"{b}")))

            reta = raw_frameeval
        else:
            def cache_clips(n, a, b, lm, nam2, cache):
                #print(f"{n} for {b} {nam2}")
                b = tuple(b)
                if not b in cache:
                    rnd = wrap_error(a, lambda: lm(a, b))
                    lel = rnd.text.Text(f"{b}        {nam2}               ")
                    cache[b] = lel
                return cache[b]
            cache = {}
            self.caches += [cache]
            fanc = partial(cache_clips, a=input_clip, b=v, lm=lm, nam2=nam,cache=cache)
            n0 = fanc(0)

            cached = core.std.FrameEval(n0, fanc, clip_src=[input_clip])
            #core.std.SetVideoCache(cached, 0)

            reta = cached

        self.tunables_nodes += [ (input_clip,reta) ]
        return reta

def wrap_error(nd, lmbda):
    try:
        return lmbda()
    except:
        import traceback
        var = traceback.format_exc()
        print(var)
        return nd.std.BlankClip().text.Text(f"{var}")


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