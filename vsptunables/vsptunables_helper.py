from vstools import vs, core
from typing import Callable, cast

__all__ = [
    'tunable',
    'seperator'
]

def tunable(clip: vs.VideoNode, v: list[int | bool | float], nam: list[str], lm: Callable[[vs.VideoNode, list[int | bool | float]], vs.VideoNode]) -> vs.VideoNode:
    assert len(v) == len(nam)

    try:
        from vspreview.api import is_preview
        from vspreview.core import main_window
    except:
        return lm(clip, v)

    if is_preview():
        return cast(vs.VideoNode, main_window().plugins["dev.jsaowji.tunables"].tunable(clip, v, nam, lm)) # type: ignore
    else:
        return lm(clip, v)

def seperator() -> None:
    tunable(core.std.BlankClip(width=720, height=480), [0], ["----"], lambda a, b: a)
