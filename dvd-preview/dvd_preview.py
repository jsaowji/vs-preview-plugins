from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget, QLineEdit, QTextEdit
from vspreview.core import Frame, HBoxLayout, VBoxLayout, PushButton, FrameEdit, Notches, CheckBox
from vspreview.plugins import AbstractPlugin, PluginConfig
from vssource import IsoFile

__all__ = [
    'DVDPreview'
]

# worse than mpv-dvd-browser tbh


class DVDPreview(AbstractPlugin, QWidget):
    _config = PluginConfig('dev.jsaowji.dvdpreviewplugin', 'DVDPreview')

    def setup_ui(self) -> None:
        self.setAcceptDrops(True)

        self.status = QTextEdit("Nothing here")
        self.dvdpath = QLineEdit()
        self.dvdpath.setPlaceholderText("dvdpath")

        self.open_button = PushButton("Open", clicked=self.dvd_open)
        self.open_title = PushButton("Open Title", clicked=self.dvd_title)
        self.iso = None
        self.title = None

        self.title_num = FrameEdit()
        self.angle_num = FrameEdit()

        self.current_chapter_label = QLabel("Current Chapter: -1")
        self.current_chapter = -1

        self.chapter_cell_checkbox = CheckBox("Chapters or cells")
        self.chapter_cell_checkbox.setChecked(True)
        self.chapter_cell_checkbox.stateChanged.connect(self.update_notches)

        self.title_layout = HBoxLayout([])

        self.split_from = FrameEdit()
        self.split_to = FrameEdit()
        self.split_audio_idx = FrameEdit()
        self.split_audio_path = QLineEdit()
        self.split_audio_path.setPlaceholderText("audio path / json path")
        self.split_demuxac3 = PushButton("DemuxAc3", clicked=self.btn_split_demux_ac3_clicked)
        self.split_renderwav = PushButton("RenderWav", clicked=self.btn_split_renderwav_clicked)
        self.audio_offset_label = QLabel("Audiooffset: 0")
        self.save_json_button = PushButton("Save Json", clicked=self.dvd_save_json)

        VBoxLayout(self, [
            HBoxLayout([
                self.dvdpath, self.open_button,
            ]),
            HBoxLayout([
                QLabel("titlenum"), QLabel("anglenum")
            ]),
            HBoxLayout([
                self.title_num, self.angle_num, self.chapter_cell_checkbox, self.open_title,
            ]),

            self.current_chapter_label,

            self.title_layout,
            self.status,

            HBoxLayout([
                self.split_audio_path,
                self.save_json_button,
            ]),
            # HBoxLayout([
            #    QLabel("from"),QLabel("to"),QLabel("audio")
            # ]),
            HBoxLayout([
                QLabel("from/to/audioindex"), self.split_from, self.split_to, self.split_audio_idx, self.split_demuxac3, self.split_renderwav
            ]),
            self.audio_offset_label
        ])

    def btn_split_renderwav_clicked(self):
        fromy, toy, audioy = self.split_from.value().value, self.split_to.value().value, self.split_audio_idx.value().value
        splt = self.title.split_range(fromy, toy, audioy)
        import vsmuxtools
        vsmuxtools.audio_async_render(splt.audio, open(self.split_audio_path.text(), "wb"))

    def btn_split_demux_ac3_clicked(self):
        fromy, toy, audioy = self.split_from.value().value, self.split_to.value().value, self.split_audio_idx.value().value
        if self.title._audios[audioy].startswith("ac3"):
            splt = self.title.split_range(fromy, toy, audioy)
            offst = splt.ac3(self.split_audio_path.text(), audioy)
            offst = round(offst * 1000 * 10) / 10
            self.audio_offset_label.setText(f"Offset: {offst} ms")

    def dvd_open(self):
        try:
            self.iso = IsoFile(self.dvdpath.text())
            self.status.setText(str(self.iso))
            self.title_num.setMinimum(1)
            self.title_num.setMaximum(self.iso.title_count)
            self.angle_num.setMinimum(1)
        except:
            self.iso = None

    def dvd_save_json(self):
        try:
            import json
            json.dump(self.iso.json, open(self.split_audio_path.text(), "wt"))
        except:
            pass

    def dvd_title(self):
        try:
            self.title = self.iso.get_title(int(self.title_num.value()), angle_nr=int(self.angle_num.value()))
        except:
            self.title = None
            return
        self.add_output(self.title.video)

        self.status.setText(str(self.iso) + "\n\n" + str(self.title))

        self.split_from.setMinimum(1)
        self.split_from.setMaximum(len(self.title.chapters) - 1)

        self.split_to.setMinimum(1)
        self.split_to.setMaximum(len(self.title.chapters) - 1)

    def on_current_frame_changed(self, frame: Frame) -> None:
        if self.title is not None:
            self.current_chapter_label.setText("Current Chapter: -1")

            for i, c in enumerate(self.title.chapters):
                if frame.value <= c:
                    # i because its smaller last but i is next but chapters start at 1
                    self.current_chapter_label.setText(f"Current Chapter: {i}")
                    self.current_chapter = i
                    # self.main.timeline.update_notches(self)
                    self.update_notches()
                    break

    def add_output(self, new_node):
        prevnode = self.main.outputs[self.main.current_output.index].with_node(new_node)

        self.main.outputs.items.append(prevnode)
        idxx = len(self.main.outputs.items) - 1
        prevnode.index = idxx
        prevnode.name = f"title: {self.title_num.value()}"

        self.main.refresh_video_outputs()
        self.update_notches()
        self.main.switch_output(idxx)

    def update_notches(self):
        self.main.timeline.update_notches(self)

    def get_notches(self) -> Notches:
        nchs = Notches([], Qt.GlobalColor.magenta)

        if self.title is not None:
            oo = self.title.chapters if self.chapter_cell_checkbox.isChecked() else self.title.cell_changes

            def rangecalc(rng):
                return min(24 * 5, int(max(1, rng / 20)))

            ii = self.current_chapter - 1
            if ii >= 0:
                iiend = min(ii + 1, len(self.title.chapters) - 1)
                rng = self.title.chapters[iiend] - self.title.chapters[ii]
                for a in list(range(self.title.chapters[ii], self.title.chapters[iiend], rangecalc(rng))):
                    nchs.add(a, Qt.GlobalColor.cyan)

            real_chapts = []
            for c in oo:
                for i in range(-20, 20, 1):
                    real_chapts += [c + i]

            for i in real_chapts:
                nchs.add(i, Qt.GlobalColor.magenta)

        return nchs

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            try:
                self.dvdpath.setText(f)
                self.dvd_open()
                break
            except:
                pass
