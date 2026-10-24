#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##########################################################
##                       Clockoo                        ##
##                 Window and tray icon                 ##
##                 written in Python 3                  ##
##                          🌞                          ##
##       by FranzBias 2026 · github.com/FranzBias       ##
##            Licensed under the MIT License            ##
##          See LICENSE file for full license.          ##
##########################################################
# SPDX-License-Identifier: MIT
"""
clockoo_gui.py — window and tray icon of Clockoo 🐦⏰

Why this file exists: it is the friendly face of Clockoo. It edits the
config (cuckoo hours, alarms, sounds, voices) and calls
clockoo_core.apply(); the ringing itself is done by systemd timers, so
closing this window never silences an alarm.

Usage:
    clockoo_gui.py            open the window
    clockoo_gui.py --hidden   start in the tray only (autostart)

by Franz & Aldus
"""

import os
import sys
import threading
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi  # noqa: E402
gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gio, GLib, Gtk, Pango  # noqa: E402

try:
    gi.require_version("XApp", "1.0")
    from gi.repository import XApp  # noqa: E402
except (ImportError, ValueError):
    XApp = None

import clockoo_core as core               # noqa: E402
from clockoo_i18n import _, set_lang, LANGS  # noqa: E402

APP_ID = "com.bybias.Clockoo"
ICON_NAME = "clockoo"
FALLBACK_ICON = "alarm-symbolic"
LANG_NAMES = {"en": "English", "it": "Italiano", "de": "Deutsch"}


def icon_name():
    theme = Gtk.IconTheme.get_default()
    return ICON_NAME if theme and theme.has_icon(ICON_NAME) else FALLBACK_ICON


def day_names():
    return [_(d) for d in core.WEEKDAYS]


def days_summary(alarm):
    days = sorted(alarm.get("days", []))
    if not days:
        return _("Once")
    if days == list(range(7)):
        return _("Every day")
    if days == [0, 1, 2, 3, 4]:
        return _("Weekdays")
    if days == [5, 6]:
        return _("Weekend")
    names = day_names()
    return ", ".join(names[d] for d in days)


def when_text(when):
    if not when:
        return ""
    today = datetime.now().date()
    if when.date() == today:
        day = _("today")
    elif when.date() == today + timedelta(days=1):
        day = _("tomorrow")
    else:
        day = day_names()[when.weekday()] + " " + when.strftime("%d/%m")
    return "%s %s" % (day, when.strftime("%H:%M"))


def fill_voices(combo, cfg, current_id):
    """Fill a ComboBoxText with the piper voices; pick current_id, else a
    voice in the interface language. Returns the voice list."""
    from clockoo_i18n import current
    voices = core.list_voices(cfg)
    for voice_id, text, _lang in voices:
        combo.append(voice_id, text)
    if combo.set_active_id(current_id or ""):
        return voices
    for voice_id, _text, lang in voices:
        if lang.startswith(current()):
            combo.set_active_id(voice_id)
            return voices
    if voices:
        combo.set_active(0)
    return voices


def run_in_thread(func, *args):
    threading.Thread(target=func, args=args, daemon=True).start()


def message(parent, text, kind=Gtk.MessageType.WARNING, detail=None):
    dlg = Gtk.MessageDialog(transient_for=parent, modal=True,
                            message_type=kind, buttons=Gtk.ButtonsType.OK,
                            text=text)
    if detail:
        dlg.format_secondary_text(detail)
    dlg.run()
    dlg.destroy()


# ------------------------------------------------------------------ widgets

class SoundPicker(Gtk.Box):
    """Combo with every sound in the sounds folder + a ▶ test button."""

    def __init__(self, cfg, current):
        super().__init__(spacing=6)
        self.cfg = cfg
        self.combo = Gtk.ComboBoxText()
        for name in core.list_sounds(cfg):
            self.combo.append(name, os.path.splitext(name)[0].replace("_", " "))
        if not self.combo.set_active_id(current or ""):
            self.combo.set_active(0)
        self.combo.set_hexpand(True)
        play = Gtk.Button.new_from_icon_name("media-playback-start-symbolic",
                                              Gtk.IconSize.BUTTON)
        play.set_tooltip_text(_("Play"))
        play.connect("clicked", self.on_play)
        self.pack_start(self.combo, True, True, 0)
        self.pack_start(play, False, False, 0)

    def get(self):
        return self.combo.get_active_id() or ""

    def on_play(self, _btn):
        path = core.sound_path(self.cfg, self.get())
        if path:
            core.play(path)


class AlarmDialog(Gtk.Dialog):
    """Create or edit one alarm."""

    def __init__(self, parent, cfg, alarm):
        title = _("Edit alarm") if alarm.get("id") else _("New alarm")
        super().__init__(title=title, transient_for=parent, modal=True)
        self.cfg = cfg
        self.alarm = alarm
        self.set_default_size(440, -1)
        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Save"), Gtk.ResponseType.OK).get_style_context() \
            .add_class("suggested-action")
        self.set_default_response(Gtk.ResponseType.OK)

        grid = Gtk.Grid(column_spacing=12, row_spacing=10, margin=16)
        self.get_content_area().add(grid)
        row = 0

        def label(text):
            lbl = Gtk.Label(label=text, xalign=1)
            lbl.get_style_context().add_class("dim-label")
            return lbl

        self.name = Gtk.Entry(text=alarm.get("name", ""),
                              activates_default=True, hexpand=True)
        grid.attach(label(_("Name")), 0, row, 1, 1)
        grid.attach(self.name, 1, row, 1, 1)
        row += 1

        try:
            hour, minute = core.parse_time(alarm.get("time", "07:00"))
        except ValueError:
            hour, minute = 7, 0
        tbox = Gtk.Box(spacing=4)
        self.hour = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.minute = Gtk.SpinButton.new_with_range(0, 59, 1)
        for spin, value in ((self.hour, hour), (self.minute, minute)):
            spin.set_value(value)
            spin.set_wrap(True)
            spin.set_numeric(True)
            spin.connect("output", self._two_digits)
        tbox.pack_start(self.hour, False, False, 0)
        tbox.pack_start(Gtk.Label(label=":"), False, False, 0)
        tbox.pack_start(self.minute, False, False, 0)
        grid.attach(label(_("Time")), 0, row, 1, 1)
        grid.attach(tbox, 1, row, 1, 1)
        row += 1

        dbox = Gtk.Box(spacing=2)
        dbox.get_style_context().add_class("linked")
        self.days = []
        for index, name in enumerate(day_names()):
            btn = Gtk.ToggleButton(label=name)
            btn.set_active(index in alarm.get("days", []))
            dbox.pack_start(btn, True, True, 0)
            self.days.append(btn)
        hint = Gtk.Label(label=_("No day = rings once"), xalign=0)
        hint.get_style_context().add_class("dim-label")
        vdays = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vdays.pack_start(dbox, False, False, 0)
        vdays.pack_start(hint, False, False, 0)
        grid.attach(label(_("Days")), 0, row, 1, 1)
        grid.attach(vdays, 1, row, 1, 1)
        row += 1

        self.sound = SoundPicker(cfg, alarm.get("sound"))
        grid.attach(label(_("Sound")), 0, row, 1, 1)
        grid.attach(self.sound, 1, row, 1, 1)
        row += 1

        rbox = Gtk.Box(spacing=6)
        self.repeat = Gtk.SpinButton.new_with_range(1, 20, 1)
        self.repeat.set_value(int(alarm.get("repeat", 3)))
        rbox.pack_start(self.repeat, False, False, 0)
        rbox.pack_start(Gtk.Label(label=_("times")), False, False, 0)
        grid.attach(label(_("Repeat")), 0, row, 1, 1)
        grid.attach(rbox, 1, row, 1, 1)
        row += 1

        text_label = Gtk.Label(label=_("Text to read aloud (optional)"),
                               xalign=0)
        grid.attach(text_label, 0, row, 2, 1)
        row += 1
        self.text = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.text.get_buffer().set_text(alarm.get("text", ""))
        frame = Gtk.ScrolledWindow(min_content_height=70)
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.add(self.text)
        grid.attach(frame, 0, row, 2, 1)
        row += 1

        vbox = Gtk.Box(spacing=6)
        self.voice = Gtk.ComboBoxText(hexpand=True)
        voices = fill_voices(self.voice, cfg, alarm.get("voice"))
        try_btn = Gtk.Button(label="🗣 " + _("Try voice"))
        try_btn.connect("clicked", self.on_try_voice)
        vbox.pack_start(self.voice, True, True, 0)
        vbox.pack_start(try_btn, False, False, 0)
        grid.attach(label(_("Voice")), 0, row, 1, 1)
        grid.attach(vbox, 1, row, 1, 1)
        if not voices:
            hint = Gtk.Label(xalign=0, label=_("No voices found in %s")
                             % os.path.join(cfg["piper_dir"], "voices"))
            hint.get_style_context().add_class("dim-label")
            row += 1
            grid.attach(hint, 1, row, 1, 1)

        self.show_all()

    @staticmethod
    def _two_digits(spin):
        spin.set_text("%02d" % spin.get_value_as_int())
        return True

    def get_text(self):
        buf = self.text.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(),
                            False).strip()

    def on_try_voice(self, _btn):
        text = self.get_text() or self.name.get_text() or _("Alarm")
        voice = self.voice.get_active_id() or ""
        run_in_thread(core.speak, self.cfg, text, voice, True)

    def result(self):
        """Return the edited alarm dict."""
        alarm = dict(self.alarm)
        alarm["name"] = self.name.get_text().strip() or _("Alarm")
        alarm["time"] = "%02d:%02d" % (self.hour.get_value_as_int(),
                                       self.minute.get_value_as_int())
        alarm["days"] = [i for i, b in enumerate(self.days) if b.get_active()]
        alarm["date"] = None if alarm["days"] else \
            core.next_once_date(alarm["time"])
        alarm["sound"] = self.sound.get()
        alarm["repeat"] = self.repeat.get_value_as_int()
        alarm["text"] = self.get_text()
        alarm["voice"] = self.voice.get_active_id() or ""
        alarm["enabled"] = True
        return alarm


class AlarmRow(Gtk.ListBoxRow):
    def __init__(self, window, alarm):
        super().__init__()
        self.window = window
        self.alarm = alarm
        box = Gtk.Box(spacing=12, margin=10)
        self.add(box)

        clock = Gtk.Label(xalign=0)
        clock.set_markup("<span size='xx-large' weight='bold'>%s</span>"
                         % GLib.markup_escape_text(alarm["time"]))
        box.pack_start(clock, False, False, 0)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name = Gtk.Label(label=alarm.get("name") or _("Alarm"), xalign=0)
        name.set_ellipsize(Pango.EllipsizeMode.END)
        detail = days_summary(alarm)
        when = core.next_ring(alarm)
        if when:
            detail += "  ·  " + when_text(when)
        if alarm.get("text"):
            detail += "  ·  🗣"
        sub = Gtk.Label(label=detail, xalign=0)
        sub.get_style_context().add_class("dim-label")
        info.pack_start(name, False, False, 0)
        info.pack_start(sub, False, False, 0)
        box.pack_start(info, True, True, 0)

        switch = Gtk.Switch(active=bool(alarm.get("enabled")),
                            valign=Gtk.Align.CENTER)
        switch.connect("notify::active", self.on_switch)
        box.pack_start(switch, False, False, 0)

        edit = Gtk.Button.new_from_icon_name("document-edit-symbolic",
                                              Gtk.IconSize.BUTTON)
        edit.set_valign(Gtk.Align.CENTER)
        edit.connect("clicked", lambda *_a: window.edit_alarm(alarm))
        box.pack_start(edit, False, False, 0)

        delete = Gtk.Button.new_from_icon_name("user-trash-symbolic",
                                                Gtk.IconSize.BUTTON)
        delete.set_valign(Gtk.Align.CENTER)
        delete.set_tooltip_text(_("Delete"))
        delete.connect("clicked", lambda *_a: window.delete_alarm(alarm))
        box.pack_start(delete, False, False, 0)

    def on_switch(self, switch, _pspec):
        self.alarm["enabled"] = switch.get_active()
        if self.alarm["enabled"] and not self.alarm.get("days"):
            self.alarm["date"] = core.next_once_date(self.alarm["time"])
        self.window.commit()


class CountdownRow(Gtk.ListBoxRow):
    """One running countdown: remaining time (ticks every second), Cancel."""

    def __init__(self, window, item):
        super().__init__()
        self.item = item
        box = Gtk.Box(spacing=12, margin=10)
        self.add(box)

        self.clock = Gtk.Label(xalign=0)
        box.pack_start(self.clock, False, False, 0)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name = Gtk.Label(label=item.get("name") or _("Timer"), xalign=0)
        name.set_ellipsize(Pango.EllipsizeMode.END)
        try:
            end = datetime.fromisoformat(item["end"]).strftime("%H:%M:%S")
        except (KeyError, ValueError):
            end = "?"
        detail = core.format_duration(item.get("seconds", 0)) + "  ·  " + \
            _("ends at %s") % end
        if item.get("text"):
            detail += "  ·  🗣"
        sub = Gtk.Label(label=detail, xalign=0)
        sub.get_style_context().add_class("dim-label")
        info.pack_start(name, False, False, 0)
        info.pack_start(sub, False, False, 0)
        box.pack_start(info, True, True, 0)

        cancel = Gtk.Button(label=_("Cancel"), valign=Gtk.Align.CENTER)
        cancel.connect("clicked",
                       lambda *_a: window.cancel_countdown(item["id"]))
        box.pack_start(cancel, False, False, 0)
        self.update()

    def update(self):
        """Refresh the remaining time; returns the seconds left."""
        left = core.countdown_remaining(self.item)
        self.clock.set_markup("<span size='xx-large' weight='bold' "
                              "font_features='tnum'>%s</span>"
                              % core.format_duration(left))
        return left


# ------------------------------------------------------------------ window

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=core.APP_NAME)
        self.app = app
        self.cfg = app.cfg
        self.set_default_size(560, 640)
        self.set_icon_name(icon_name())
        self._cuckoo_timeout = None

        header = Gtk.HeaderBar(show_close_button=True)
        header.set_title(core.APP_NAME)
        self.header = header
        self.set_titlebar(header)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        switcher = Gtk.StackSwitcher(stack=self.stack)
        header.set_custom_title(switcher)

        add = Gtk.Button.new_from_icon_name("list-add-symbolic",
                                             Gtk.IconSize.BUTTON)
        add.set_tooltip_text(_("New alarm"))
        add.connect("clicked", lambda *_a: self.edit_alarm(None))
        header.pack_start(add)
        header.pack_end(self._settings_button())

        self.stack.add_titled(self._alarms_page(), "alarms", "⏰ " + _("Alarms"))
        self.stack.add_titled(self._timer_page(), "timer", "⏳ " + _("Timer"))
        self.stack.add_titled(self._cuckoo_page(), "cuckoo", "🐦 " + _("Cuckoo"))
        self.add(self.stack)

        self.connect("delete-event", self.on_delete)
        self.refresh_alarms()
        self.refresh_countdowns(prune=True)
        self._ticks = 0
        self._countdown_timeout = GLib.timeout_add_seconds(
            1, self._countdown_tick)
        self.connect("destroy", self._on_destroy)

    def _on_destroy(self, *_args):
        if self._countdown_timeout:
            GLib.source_remove(self._countdown_timeout)
            self._countdown_timeout = None

    # -- settings popover (interface language)

    def _settings_button(self):
        button = Gtk.MenuButton()
        button.set_image(Gtk.Image.new_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.BUTTON))
        pop = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                      margin=12)
        box.pack_start(Gtk.Label(label=_("Interface language"), xalign=0),
                       False, False, 0)
        combo = Gtk.ComboBoxText()
        combo.append("auto", _("Automatic"))
        for code in LANGS:
            combo.append(code, LANG_NAMES[code])
        combo.set_active_id(self.cfg.get("ui_lang", "auto"))
        combo.connect("changed", self.on_lang)
        box.pack_start(combo, False, False, 0)

        box.pack_start(Gtk.Label(label=_("Sounds folder"), xalign=0,
                                 margin_top=6), False, False, 0)
        chooser = Gtk.FileChooserButton(
            title=_("Sounds folder"), action=Gtk.FileChooserAction.SELECT_FOLDER)
        chooser.set_filename(str(core.sounds_folder(self.cfg)))
        chooser.connect("file-set", self.on_sounds_dir)
        box.pack_start(chooser, False, False, 0)
        bundled = Gtk.Button(label=_("Use the bundled sounds"))
        bundled.set_sensitive(bool(self.cfg.get("sounds_dir")))
        bundled.connect("clicked", lambda *_a: self.set_sounds_dir(""))
        box.pack_start(bundled, False, False, 0)

        version = Gtk.Label(label="%s %s · byBias" % (core.APP_NAME,
                                                      core.VERSION))
        version.get_style_context().add_class("dim-label")
        box.pack_start(version, False, False, 0)
        box.show_all()
        pop.add(box)
        button.set_popover(pop)
        return button

    def on_lang(self, combo):
        self.cfg["ui_lang"] = combo.get_active_id()
        core.save_config(self.cfg)
        self.app.rebuild()

    def on_sounds_dir(self, chooser):
        path = chooser.get_filename()
        if path:
            self.set_sounds_dir(path)

    def set_sounds_dir(self, path):
        """'' = bundled sounds. Stored with ~ so the config stays portable."""
        if path and os.path.realpath(path) == str(core.BUNDLED_SOUNDS):
            path = ""
        home = os.path.expanduser("~")
        if path.startswith(home + os.sep):
            path = "~" + path[len(home):]
        self.cfg["sounds_dir"] = path
        core.save_config(self.cfg)
        self.app.rebuild()            # refill every sound list

    # -- alarms page

    def _alarms_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll = Gtk.ScrolledWindow(vexpand=True,
                                    hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.alarm_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.alarm_list.connect("row-activated",
                                lambda _l, row: self.edit_alarm(row.alarm))
        placeholder = Gtk.Label(label=_("No alarms yet."), margin=40)
        placeholder.get_style_context().add_class("dim-label")
        placeholder.show()
        self.alarm_list.set_placeholder(placeholder)
        scroll.add(self.alarm_list)
        box.pack_start(scroll, True, True, 0)

        new = Gtk.Button(label="➕ " + _("New alarm"), margin=12)
        new.connect("clicked", lambda *_a: self.edit_alarm(None))
        box.pack_start(new, False, False, 0)
        return box

    def refresh_alarms(self):
        for child in self.alarm_list.get_children():
            self.alarm_list.remove(child)
        alarms = sorted(self.cfg["alarms"], key=lambda a: a.get("time", ""))
        for alarm in alarms:
            self.alarm_list.add(AlarmRow(self, alarm))
        self.alarm_list.show_all()
        alarm, when = core.next_alarm(self.cfg)
        self.header.set_subtitle(
            _("Next alarm: %s") % when_text(when) if when else _("No alarm set"))
        self.app.update_tray()

    def edit_alarm(self, alarm):
        base = alarm if alarm else core.new_alarm(
            voice="", sound=self.cfg["cuckoo"].get("sound", "bell.ogg"))
        dialog = AlarmDialog(self, self.cfg, base)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            edited = dialog.result()
            if alarm:
                alarm.clear()
                alarm.update(edited)
            else:
                self.cfg["alarms"].append(edited)
            self.commit()
        dialog.destroy()

    def delete_alarm(self, alarm):
        dlg = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text=_("Delete alarm «%s»?") % (alarm.get("name") or _("Alarm")))
        dlg.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        dlg.add_button(_("Delete"), Gtk.ResponseType.OK) \
            .get_style_context().add_class("destructive-action")
        if dlg.run() == Gtk.ResponseType.OK:
            self.cfg["alarms"] = [a for a in self.cfg["alarms"]
                                  if a["id"] != alarm["id"]]
            self.commit()
        dlg.destroy()

    def commit(self):
        errors = core.apply(self.cfg)
        self.refresh_alarms()
        if errors:
            message(self, _("systemd reported a problem"),
                    detail="\n".join(errors))

    # -- timer page

    def _timer_page(self):
        tcfg = self.cfg["timer"]
        # Explicit left margin: right-aligned labels must never touch the edge.
        grid = Gtk.Grid(column_spacing=12, row_spacing=10, margin=18,
                        margin_start=24)
        row = 0

        def label(text):
            lbl = Gtk.Label(label=text, xalign=1, margin_start=6)
            lbl.get_style_context().add_class("dim-label")
            return lbl

        def heading(text):
            lbl = Gtk.Label(xalign=0, margin_top=6)
            lbl.set_markup("<b>%s</b>" % GLib.markup_escape_text(text))
            return lbl

        self.timer_name = Gtk.Entry(hexpand=True, placeholder_text=_("Timer"))
        grid.attach(label(_("Name")), 0, row, 1, 1)
        grid.attach(self.timer_name, 1, row, 1, 1)
        row += 1

        self.timer_sound = SoundPicker(self.cfg, tcfg.get("sound"))
        grid.attach(label(_("Sound")), 0, row, 1, 1)
        grid.attach(self.timer_sound, 1, row, 1, 1)
        row += 1

        self.timer_text = Gtk.Entry(
            hexpand=True, placeholder_text=_("Text to read aloud (optional)"))
        grid.attach(label("🗣"), 0, row, 1, 1)
        grid.attach(self.timer_text, 1, row, 1, 1)
        row += 1

        self.timer_voice = Gtk.ComboBoxText(hexpand=True)
        fill_voices(self.timer_voice, self.cfg, tcfg.get("voice"))
        grid.attach(label(_("Voice")), 0, row, 1, 1)
        grid.attach(self.timer_voice, 1, row, 1, 1)
        row += 1

        grid.attach(heading(_("Quick start")), 0, row, 2, 1)
        row += 1
        presets = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,
                              homogeneous=True, max_children_per_line=6,
                              column_spacing=6, row_spacing=6)
        for minutes in core.COUNTDOWN_PRESETS:
            btn = Gtk.Button(label=_("%d min") % minutes)
            btn.connect("clicked",
                        lambda _b, m=minutes: self.start_countdown(m * 60))
            presets.add(btn)
        grid.attach(presets, 0, row, 2, 1)
        row += 1

        grid.attach(heading(_("Custom")), 0, row, 2, 1)
        row += 1
        custom = Gtk.Box(spacing=4)
        self.timer_spins = []
        for top, value, unit in ((23, 0, "h"), (59, 5, "min"), (59, 0, "s")):
            spin = Gtk.SpinButton.new_with_range(0, top, 1)
            spin.set_value(value)
            spin.set_numeric(True)
            spin.connect("output", AlarmDialog._two_digits)
            spin.connect("activate", lambda *_a: self.on_custom_start())
            custom.pack_start(spin, False, False, 0)
            custom.pack_start(Gtk.Label(label=unit), False, False, 4)
            self.timer_spins.append(spin)
        start = Gtk.Button(label="▶ " + _("Start"))
        start.get_style_context().add_class("suggested-action")
        start.connect("clicked", lambda *_a: self.on_custom_start())
        custom.pack_end(start, False, False, 0)
        grid.attach(custom, 0, row, 2, 1)
        row += 1

        grid.attach(heading(_("Running timers")), 0, row, 2, 1)
        row += 1
        self.countdown_list = Gtk.ListBox(
            selection_mode=Gtk.SelectionMode.NONE)
        self.countdown_list.get_style_context().add_class("frame")
        placeholder = Gtk.Label(label=_("No timer running."), margin=24)
        placeholder.get_style_context().add_class("dim-label")
        placeholder.show()
        self.countdown_list.set_placeholder(placeholder)
        grid.attach(self.countdown_list, 0, row, 2, 1)

        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.add(grid)
        return scroll

    def on_custom_start(self):
        hours, minutes, seconds = (s.get_value_as_int()
                                   for s in self.timer_spins)
        total = hours * 3600 + minutes * 60 + seconds
        if total > 0:
            self.start_countdown(total)

    def start_countdown(self, seconds):
        tcfg = self.cfg["timer"]
        tcfg["sound"] = self.timer_sound.get()
        tcfg["voice"] = self.timer_voice.get_active_id() or ""
        core.save_config(self.cfg)    # remember the choice for the tray
        _item, error = core.start_countdown(
            seconds, self.timer_name.get_text(), tcfg["sound"],
            self.timer_text.get_text().strip(), tcfg["voice"],
            tcfg.get("repeat", 3))
        self.refresh_countdowns()
        if error:
            message(self, _("Could not start the timer"), detail=error)

    def cancel_countdown(self, countdown_id):
        core.cancel_countdown(countdown_id)
        self.refresh_countdowns()

    def refresh_countdowns(self, prune=False):
        items = core.prune_countdowns() if prune else core.list_countdowns()
        items = sorted(items, key=lambda c: c.get("end", ""))
        self._countdown_ids = [c["id"] for c in items]
        for child in self.countdown_list.get_children():
            self.countdown_list.remove(child)
        for item in items:
            self.countdown_list.add(CountdownRow(self, item))
        self.countdown_list.show_all()

    def _countdown_tick(self):
        # The file may change behind our back (ring, tray): reread it, and
        # every 10 s also drop entries whose systemd unit is gone.
        self._ticks += 1
        if self._ticks % 10 == 0:
            self.refresh_countdowns(prune=True)
        elif [c["id"] for c in core.list_countdowns()] != self._countdown_ids:
            self.refresh_countdowns()
        elif self.is_visible():
            for row in self.countdown_list.get_children():
                row.update()
        return True

    # -- cuckoo page

    def _cuckoo_page(self):
        cuckoo = self.cfg["cuckoo"]
        grid = Gtk.Grid(column_spacing=12, row_spacing=14, margin=18)

        title = Gtk.Label(xalign=0, hexpand=True)
        title.set_markup("<b>%s</b>" % _("Hourly cuckoo"))
        self.cuckoo_switch = Gtk.Switch(active=bool(cuckoo.get("enabled")),
                                        halign=Gtk.Align.END)
        self.cuckoo_switch.connect("notify::active", self.on_cuckoo_changed)
        grid.attach(title, 0, 0, 1, 1)
        grid.attach(self.cuckoo_switch, 1, 0, 1, 1)

        hours_label = Gtk.Label(label=_("Hours"), xalign=0)
        grid.attach(hours_label, 0, 1, 2, 1)
        hours = Gtk.Grid(column_spacing=4, row_spacing=4,
                         column_homogeneous=True)
        self.hour_buttons = []
        for hour in range(24):
            btn = Gtk.ToggleButton(label="%02d" % hour)
            btn.set_active(hour in cuckoo.get("hours", []))
            btn.connect("toggled", self.on_cuckoo_changed)
            hours.attach(btn, hour % 6, hour // 6, 1, 1)
            self.hour_buttons.append(btn)
        grid.attach(hours, 0, 2, 2, 1)

        quick = Gtk.Box(spacing=6)
        for text, picker in ((_("All"), lambda h: True),
                             (_("Day"), lambda h: 7 <= h <= 21),
                             (_("None"), lambda h: False)):
            btn = Gtk.Button(label=text)
            btn.connect("clicked", self.on_hours_preset, picker)
            quick.pack_start(btn, False, False, 0)
        grid.attach(quick, 0, 3, 2, 1)

        grid.attach(Gtk.Label(label=_("Minute"), xalign=0), 0, 4, 1, 1)
        self.cuckoo_minute = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.cuckoo_minute.set_value(int(cuckoo.get("minute", 0)))
        self.cuckoo_minute.connect("output", AlarmDialog._two_digits)
        self.cuckoo_minute.connect("value-changed", self.on_cuckoo_changed)
        self.cuckoo_minute.set_halign(Gtk.Align.END)
        grid.attach(self.cuckoo_minute, 1, 4, 1, 1)

        grid.attach(Gtk.Label(label=_("Sound"), xalign=0), 0, 5, 2, 1)
        self.cuckoo_sound = SoundPicker(self.cfg, cuckoo.get("sound"))
        self.cuckoo_sound.combo.connect("changed", self.on_cuckoo_changed)
        grid.attach(self.cuckoo_sound, 0, 6, 2, 1)

        self.count_hours = Gtk.CheckButton(
            label=_("Call as many times as the hour"))
        self.count_hours.set_active(bool(cuckoo.get("count_hours")))
        self.count_hours.connect("toggled", self.on_cuckoo_changed)
        grid.attach(self.count_hours, 0, 7, 2, 1)

        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.add(grid)
        return scroll

    def on_hours_preset(self, _btn, picker):
        for hour, button in enumerate(self.hour_buttons):
            button.set_active(picker(hour))

    def on_cuckoo_changed(self, *_args):
        cuckoo = self.cfg["cuckoo"]
        cuckoo["enabled"] = self.cuckoo_switch.get_active()
        cuckoo["hours"] = [h for h, b in enumerate(self.hour_buttons)
                           if b.get_active()]
        cuckoo["minute"] = self.cuckoo_minute.get_value_as_int()
        cuckoo["sound"] = self.cuckoo_sound.get()
        cuckoo["count_hours"] = self.count_hours.get_active()
        # Many toggles in a row → one single apply().
        if self._cuckoo_timeout:
            GLib.source_remove(self._cuckoo_timeout)
        self._cuckoo_timeout = GLib.timeout_add(700, self._apply_cuckoo)

    def _apply_cuckoo(self):
        self._cuckoo_timeout = None
        self.commit()
        return False

    def flush(self):
        """Apply pending cuckoo changes right now (before hiding/quitting)."""
        if self._cuckoo_timeout:
            GLib.source_remove(self._cuckoo_timeout)
            self._apply_cuckoo()

    def on_delete(self, *_args):
        self.flush()
        if self.app.tray:
            self.hide()
            return True
        return False


# ------------------------------------------------------------------ app

class ClockooApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.cfg = None
        self.window = None
        self.tray = None
        self.menu = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.cfg = core.load_config()
        set_lang(self.cfg.get("ui_lang"))
        core.apply(self.cfg)          # make systemd match the config
        self._make_tray()
        if self.tray:
            self.hold()               # keep running with no window
        GLib.timeout_add_seconds(30, self._tick)

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]
        if "--hidden" not in args or not self.tray:
            self.show_window()
        return 0

    def show_window(self, page=None):
        if not self.window:
            self.window = MainWindow(self)
            self.window.show_all()
        if page:
            self.window.stack.set_visible_child_name(page)
        self.window.present()

    def quick_countdown(self, minutes):
        """Tray shortcut: start a countdown with the last timer choices."""
        tcfg = self.cfg["timer"]
        _item, error = core.start_countdown(
            minutes * 60, "", tcfg.get("sound"), "", tcfg.get("voice"),
            tcfg.get("repeat", 3))
        if error:
            message(self.window, _("Could not start the timer"), detail=error)
        elif self.window:
            self.window.refresh_countdowns()

    def toggle_window(self):
        if self.window and self.window.is_visible():
            self.window.flush()
            self.window.hide()
        else:
            self.show_window()

    def rebuild(self):
        """Recreate the window after a language change."""
        set_lang(self.cfg.get("ui_lang"))
        if self.window:
            self.window.flush()
            self.window.destroy()
            self.window = None
        self._build_menu()
        self.show_window()

    # -- tray

    def _make_tray(self):
        if XApp is not None:
            self.tray = XApp.StatusIcon()
            self.tray.set_name(core.APP_ID)
            self.tray.set_icon_name(icon_name())
            self.tray.connect("activate", lambda *_a: self.toggle_window())
        else:
            try:
                self.tray = Gtk.StatusIcon.new_from_icon_name(icon_name())
                self.tray.connect("activate", lambda *_a: self.toggle_window())
            except (AttributeError, TypeError):
                self.tray = None
        self._build_menu()

    def _build_menu(self):
        if not self.tray:
            return
        menu = Gtk.Menu()
        self.next_item = Gtk.MenuItem(label="")
        self.next_item.set_sensitive(False)
        menu.append(self.next_item)
        menu.append(Gtk.SeparatorMenuItem())
        self.cuckoo_item = Gtk.CheckMenuItem(label="🐦 " + _("Hourly cuckoo"))
        self.cuckoo_item.set_active(bool(self.cfg["cuckoo"].get("enabled")))
        self.cuckoo_handler = self.cuckoo_item.connect("toggled",
                                                       self.on_tray_cuckoo)
        menu.append(self.cuckoo_item)
        menu.append(Gtk.SeparatorMenuItem())
        for minutes in (5, 10):
            item = Gtk.MenuItem(label="⏳ " + _("%d min") % minutes)
            item.connect("activate",
                         lambda _i, m=minutes: self.quick_countdown(m))
            menu.append(item)
        custom = Gtk.MenuItem(label="⏳ " + _("Custom…"))
        custom.connect("activate", lambda *_a: self.show_window("timer"))
        menu.append(custom)
        menu.append(Gtk.SeparatorMenuItem())
        open_item = Gtk.MenuItem(label=_("Open Clockoo"))
        open_item.connect("activate", lambda *_a: self.show_window())
        menu.append(open_item)
        menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label=_("Quit"))
        quit_item.connect("activate", lambda *_a: self.on_quit())
        menu.append(quit_item)
        menu.show_all()
        self.menu = menu
        if XApp is not None and isinstance(self.tray, XApp.StatusIcon):
            self.tray.set_secondary_menu(menu)
        else:
            self.tray.connect("popup-menu", lambda icon, button, time:
                              menu.popup(None, None, None, None, button, time))
        self.update_tray()

    def on_tray_cuckoo(self, item):
        self.cfg["cuckoo"]["enabled"] = item.get_active()
        core.apply(self.cfg)
        if self.window:
            self.window.cuckoo_switch.set_active(item.get_active())

    def update_tray(self):
        if not self.tray or not self.menu:
            return
        alarm, when = core.next_alarm(self.cfg)
        if when:
            text = _("Next alarm: %s") % when_text(when)
            if alarm.get("name"):
                text += " — " + alarm["name"]
        else:
            text = _("No alarm set")
        self.next_item.set_label(text)
        self.tray.set_tooltip_text("%s\n%s" % (core.APP_NAME, text))
        self.cuckoo_item.handler_block(self.cuckoo_handler)
        self.cuckoo_item.set_active(bool(self.cfg["cuckoo"].get("enabled")))
        self.cuckoo_item.handler_unblock(self.cuckoo_handler)

    def _tick(self):
        # A one-time alarm may have switched itself off: reread the config.
        fresh = core.load_config()
        if fresh != self.cfg:
            self.cfg.clear()
            self.cfg.update(fresh)
            if self.window:
                self.window.cfg = self.cfg
                self.window.refresh_alarms()
        self.update_tray()
        return True

    def on_quit(self):
        if self.window:
            self.window.flush()
        self.quit()


def main():
    app = ClockooApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
