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


def add_switch(asd, name=None):
    if is_preview():
        mw = main_window()

        if not hasattr(mw, "tunables"):
            mw.tunables = []
            mw.tunables_names = []
            mw.reload_before_signal.connect(clear_tunables)

        mw.tunables += [asd]
        if name is None:
            n2 = [f"{len(mw.tunables)}"] * len(asd)
        else:
            n2 = name
        mw.tunables_names += [n2]


def wrap_error(nd, lmbda):
    try:
        return lmbda()
    except:
        import traceback
        var = traceback.format_exc()
        print(var)
        return nd.std.BlankClip().text.Text(f"{var}")


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


def clear_tunables():
    if is_preview():
        m = main_window()
        if hasattr(m, "tunables"):
            delattr(m, "tunables")
            delattr(m, "tunables_names")


class Tunables(AbstractPlugin, QWidget):
    _config = PluginConfig('dev.jsaowji.tunables', 'Tunables')

    def setup_ui(self) -> None:
        self.main.reload_after_signal.connect(self.reload_after)

        self.update_list()

    def reload_after(self):
        QWidget().setLayout(self.layout())
        self.update_list()

    def update_list(self):
        lst = []
        for tun, nam in zip(self.main.tunables, self.main.tunables_names):
            for i, a in enumerate(tun):
                if isinstance(a, bool):
                    fe = QCheckBox()
                    fe.setChecked(a)

                    def asd(a, b, c, d):
                        a[b] = c.isChecked()
                        d.main.switch_frame(d.main.current_output.last_showed_frame)

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

                    def asd(a, b, c, d):
                        a[b] = int(c.value())
                        d.main.switch_frame(d.main.current_output.last_showed_frame)

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

                    def asd(a, b, c, d):
                        a[b] = c.value()
                        d.main.switch_frame(d.main.current_output.last_showed_frame)

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

    def tunable(self, input_clip: vs.VideoNode, v: list[int | float | bool], nam: list[str], lm: callable[vs.VideoNode, list[int | float | bool]]) -> vs.VideoNode:
        if is_preview():
            add_switch(v, nam)
            if True or (not input_clip.is_inspectable(0)):
                raw_frameeval = make_frameval(lambda a=input_clip, b=v, we=wrap_error: we(
                    a, lambda: lm(a, b).text.Text(f"{b}")))
                core.std.SetVideoCache(raw_frameeval, 0)

                return raw_frameeval
            else:
                def cache_clips(n, a, b, lm, nam, cache={}):
                    print(f"{n} for {nam}")
                    b = tuple(b)
                    if not b in cache:
                        rnd = wrap_error(a, lambda: lm(a, b))
                        core.std.SetVideoCache(rnd, 0)
                        lel = rnd.text.Text(f"{b}                       ")
                        core.std.SetVideoCache(lel, 0)
                        search_for_node(lel, a, 0)
                        search_for_node(rnd, a, 0)
                        cache[b] = lel
                    return cache[b]
                fanc = partial(cache_clips, a=input_clip, b=v, lm=lm, nam=nam)
                n0 = fanc(0)
                cached = core.std.FrameEval(n0, fanc, clip_src=[input_clip])
                core.std.SetVideoCache(cached, 0)

                search_for_node(cached, input_clip, 0)

                return cached
        else:
            assert False
            return lm(input_clip, v)


def search_for_node(current: vs.VideoNode, to_search: vs.VideoNode, dpth, kp=[]):
    disab = False
    # pad = " " * dpth
    lst = list(current._dependencies)

    # print(lst)

    for _, d in enumerate(lst):
        kp += [d]
        # print(pad,dpth,"dep[",i,"]",d, d._inputs)
        if search_for_node(d, to_search, dpth + 1):
            disab = True
        if d == to_search:
            disab = True
    if disab:
        # print("disable",current._name)
        core.std.SetVideoCache(current, 0)
    return disab
