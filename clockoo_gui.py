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
clockoo_gui.py — window and tray icon of Clockoo 🕰️

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
import time
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi  # noqa: E402
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gdk, Gio, GLib, Gtk, Pango  # noqa: E402

try:
    gi.require_version("XApp", "1.0")
    from gi.repository import XApp  # noqa: E402
except (ImportError, ValueError):
    XApp = None

import clockoo_core as core               # noqa: E402
from clockoo_i18n import _, set_lang, LANGS  # noqa: E402

APP_ID = "com.bybias.Clockoo"
ICON_NAME = "clockoo"              # wooden mantel clock, for light themes
ICON_NAME_DARK = "clockoo-dark"    # brass mantel clock, for dark themes
FALLBACK_ICON = "alarm-symbolic"
LANG_NAMES = {"en": "English", "it": "Italiano", "de": "Deutsch"}
ICON_STYLES = ("auto", "light", "dark")

# Once-mode day buttons stay clickable but look switched off.
CSS = b"""
.clockoo-dimmed { opacity: 0.45; }
"""


def theme_is_dark():
    """True when the GTK theme draws light text on a dark background."""
    settings = Gtk.Settings.get_default()
    if settings and settings.get_property("gtk-application-prefer-dark-theme"):
        return True
    name = (settings.get_property("gtk-theme-name") if settings else "") or ""
    if "dark" in name.lower():
        return True
    # Ask the theme itself: the luminance of a window's text colour.
    probe = Gtk.Window()
    color = probe.get_style_context().get_color(Gtk.StateFlags.NORMAL)
    probe.destroy()
    luminance = 0.2126 * color.red + 0.7152 * color.green + 0.0722 * color.blue
    return luminance > 0.6


def icon_name(cfg=None):
    """Pick the icon: the user's choice, or follow the theme ('auto')."""
    style = (cfg or {}).get("icon_style", "auto")
    dark = theme_is_dark() if style == "auto" else style == "dark"
    wanted = ICON_NAME_DARK if dark else ICON_NAME
    theme = Gtk.IconTheme.get_default()
    for name in (wanted, ICON_NAME):
        if theme and theme.has_icon(name):
            return name
    return FALLBACK_ICON


def center_on_pointer_monitor(window):
    """Place a window in the middle of the monitor under the mouse.

    Without this, on two monitors the window manager may centre the window
    on the whole desktop, i.e. half on each screen."""
    display = Gdk.Display.get_default()
    if not display:
        return
    seat = display.get_default_seat()
    pointer = seat.get_pointer() if seat else None
    if pointer:
        _screen, x, y = pointer.get_position()
        monitor = display.get_monitor_at_point(x, y)
    else:
        monitor = display.get_primary_monitor() or display.get_monitor(0)
    if not monitor:
        return
    area = monitor.get_workarea()
    width, height = window.get_size()
    width, height = min(width, area.width), min(height, area.height)
    window.move(area.x + (area.width - width) // 2,
                area.y + (area.height - height) // 2)


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


def minutes_text(minutes):
    """75 -> '1 h 15 min', 40 -> '40 min'."""
    hours, rest = divmod(int(minutes), 60)
    if not hours:
        return _("%d min") % rest
    return ("%d h %d min" % (hours, rest)) if rest else ("%d h" % hours)


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

        # Two choices under the time: repeat on some days, or ring once.
        # In "once" mode the day buttons look switched off but stay
        # clickable: clicking one moves the choice back to "Days".
        self._syncing = False
        saved_days = list(alarm.get("days", []))
        self._last_days = saved_days or [0, 1, 2, 3, 4]
        self.mode_days = Gtk.RadioButton.new_with_label(None, _("Days"))
        self.mode_once = Gtk.RadioButton.new_with_label_from_widget(
            self.mode_days, _("No day = rings once"))
        mbox = Gtk.Box(spacing=18)
        mbox.pack_start(self.mode_days, False, False, 0)
        mbox.pack_start(self.mode_once, False, False, 0)
        grid.attach(mbox, 1, row, 1, 1)
        row += 1

        self.dbox = Gtk.Box(spacing=2)
        self.dbox.get_style_context().add_class("linked")
        self.days = []
        for index, name in enumerate(day_names()):
            btn = Gtk.ToggleButton(label=name)
            btn.set_active(index in saved_days)
            btn.connect("toggled", self.on_day_toggled)
            self.dbox.pack_start(btn, True, True, 0)
            self.days.append(btn)
        grid.attach(self.dbox, 1, row, 1, 1)
        row += 1

        if saved_days:
            self.mode_days.set_active(True)
        else:
            self.mode_once.set_active(True)
        self._show_once(not saved_days)
        self.mode_once.connect("toggled", self.on_mode_toggled)

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

        self.crescendo = Gtk.CheckButton(
            label=_("Crescendo: the volume grows from soft to full"))
        self.crescendo.set_active(bool(alarm.get("crescendo")))
        grid.attach(self.crescendo, 1, row, 1, 1)
        row += 1

        # Heads-up: a box to switch it on, then how many minutes before.
        wbox = Gtk.Box(spacing=6)
        self.warn = Gtk.CheckButton(label=_("Warn me before"))
        self.warn.set_active(bool(alarm.get("warn")))
        self.warn_minutes = Gtk.SpinButton.new_with_range(1, 120, 1)
        self.warn_minutes.set_value(int(alarm.get("warn_minutes", 10)))
        self.warn_minutes.set_numeric(True)
        self.warn_minutes.set_sensitive(self.warn.get_active())
        self.warn.connect("toggled", lambda b: self.warn_minutes.set_sensitive(
            b.get_active()))
        wbox.pack_start(self.warn, False, False, 0)
        wbox.pack_start(self.warn_minutes, False, False, 0)
        wbox.pack_start(Gtk.Label(label=_("minutes")), False, False, 0)
        grid.attach(wbox, 1, row, 1, 1)
        row += 1

        sbox = Gtk.Box(spacing=6)
        self.snooze = Gtk.SpinButton.new_with_range(0, 60, 1)
        self.snooze.set_value(int(alarm.get("snooze_minutes") or 0))
        self.snooze.set_numeric(True)
        sbox.pack_start(self.snooze, False, False, 0)
        hint = Gtk.Label(label=_("min (0 = general setting: %d)")
                         % int(cfg.get("snooze_minutes", 5)))
        hint.get_style_context().add_class("dim-label")
        sbox.pack_start(hint, False, False, 0)
        grid.attach(label(_("Snooze")), 0, row, 1, 1)
        grid.attach(sbox, 1, row, 1, 1)
        row += 1

        text_label = Gtk.Label(label=_("Text to read (optional)"), xalign=0)
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

    def _show_once(self, once):
        ctx = self.dbox.get_style_context()
        if once:
            ctx.add_class("clockoo-dimmed")
        else:
            ctx.remove_class("clockoo-dimmed")

    def _set_days(self, days):
        self._syncing = True
        for index, btn in enumerate(self.days):
            btn.set_active(index in days)
        self._syncing = False

    def on_mode_toggled(self, radio):
        if self._syncing:
            return
        once = radio.get_active()
        if once:
            current = [i for i, b in enumerate(self.days) if b.get_active()]
            if current:
                self._last_days = current
            self._set_days([])
        elif not any(b.get_active() for b in self.days):
            self._set_days(self._last_days)
        self._show_once(once)

    def on_day_toggled(self, btn):
        if self._syncing:
            return
        if btn.get_active() and self.mode_once.get_active():
            self._syncing = True
            self.mode_days.set_active(True)
            self._syncing = False
            self._show_once(False)

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
        alarm["days"] = [] if self.mode_once.get_active() else \
            [i for i, b in enumerate(self.days) if b.get_active()]
        alarm["date"] = None if alarm["days"] else \
            core.next_once_date(alarm["time"])
        alarm["sound"] = self.sound.get()
        alarm["repeat"] = self.repeat.get_value_as_int()
        alarm["text"] = self.get_text()
        alarm["voice"] = self.voice.get_active_id() or ""
        alarm["crescendo"] = self.crescendo.get_active()
        alarm["warn"] = self.warn.get_active()
        alarm["warn_minutes"] = self.warn_minutes.get_value_as_int()
        alarm["snooze_minutes"] = self.snooze.get_value_as_int()
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
        if alarm.get("crescendo"):
            detail += "  ·  📈"
        if alarm.get("warn"):
            detail += "  ·  🔔 −%d′" % int(alarm.get("warn_minutes", 10))
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
        if item.get("paused"):
            end_text = "⏸ " + _("paused")
        else:
            end_text = _("ends at %s") % end
        detail = core.format_duration(item.get("seconds", 0)) + "  ·  " + end_text
        if item.get("text"):
            detail += "  ·  🗣"
        sub = Gtk.Label(label=detail, xalign=0)
        sub.get_style_context().add_class("dim-label")
        info.pack_start(name, False, False, 0)
        info.pack_start(sub, False, False, 0)
        box.pack_start(info, True, True, 0)

        paused = bool(item.get("paused"))
        toggle = Gtk.Button.new_from_icon_name(
            "media-playback-start-symbolic" if paused else
            "media-playback-pause-symbolic", Gtk.IconSize.BUTTON)
        toggle.set_tooltip_text(_("Resume") if paused else _("Pause"))
        toggle.set_valign(Gtk.Align.CENTER)
        toggle.connect("clicked", lambda *_a: window.toggle_countdown(item))
        box.pack_start(toggle, False, False, 0)

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


class SavedTimerRow(Gtk.ListBoxRow):
    """One saved timer: duration, name, ▶ start, ↑ ↓ move, delete."""

    def __init__(self, window, item, index, count):
        super().__init__()
        self.item = item
        box = Gtk.Box(spacing=8, margin=6, margin_start=10)
        self.add(box)

        clock = Gtk.Label(xalign=0)
        clock.set_markup("<span size='large' weight='bold' "
                         "font_features='tnum'>%s</span>"
                         % core.format_duration(item.get("seconds", 0)))
        box.pack_start(clock, False, False, 0)

        text = item.get("name") or _("Timer")
        if item.get("text"):
            text += "  ·  🗣"
        name = Gtk.Label(label=text, xalign=0)
        name.set_ellipsize(Pango.EllipsizeMode.END)
        box.pack_start(name, True, True, 0)

        def icon_button(icon, tip, callback, sensitive=True):
            btn = Gtk.Button.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
            btn.set_tooltip_text(tip)
            btn.set_valign(Gtk.Align.CENTER)
            btn.set_sensitive(sensitive)
            btn.connect("clicked", lambda *_a: callback())
            box.pack_start(btn, False, False, 0)
            return btn

        # No "suggested-action" here: some themes paint the symbolic icon
        # white on a white button, and the ▶ disappears.
        icon_button("media-playback-start-symbolic", _("Start"),
                    lambda: window.start_saved_timer(item))
        icon_button("go-up-symbolic", _("Move up"),
                    lambda: window.move_saved_timer(index, -1), index > 0)
        icon_button("go-down-symbolic", _("Move down"),
                    lambda: window.move_saved_timer(index, 1),
                    index < count - 1)
        icon_button("user-trash-symbolic", _("Delete"),
                    lambda: window.delete_saved_timer(item))


# ------------------------------------------------------------------ window

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=core.APP_NAME)
        self.app = app
        self.cfg = app.cfg
        self.set_default_size(560, 640)
        self.set_position(Gtk.WindowPosition.NONE)   # we place it ourselves
        self.set_icon_name(icon_name(self.cfg))
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
        self.stack.add_titled(self._stopwatch_page(), "stopwatch",
                              "⏱ " + _("Stopwatch"))
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
        if self.sw_timeout:
            GLib.source_remove(self.sw_timeout)
            self.sw_timeout = None

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

        box.pack_start(Gtk.Label(label=_("Icon"), xalign=0, margin_top=6),
                       False, False, 0)
        icon_combo = Gtk.ComboBoxText()
        icon_combo.append("auto", _("Follow the theme"))
        icon_combo.append("light", _("Wood (light themes)"))
        icon_combo.append("dark", _("Brass (dark themes)"))
        icon_combo.set_active_id(self.cfg.get("icon_style", "auto"))
        icon_combo.connect("changed", self.on_icon_style)
        box.pack_start(icon_combo, False, False, 0)

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

    def on_icon_style(self, combo):
        self.cfg["icon_style"] = combo.get_active_id() or "auto"
        core.save_config(self.cfg)
        self.app.update_icons()

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
            hexpand=True, placeholder_text=_("Text to read (optional)"))
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
        save = Gtk.Button(label="💾 " + _("Save"))
        save.set_tooltip_text(_("Save this timer for later"))
        save.connect("clicked", lambda *_a: self.on_save_timer())
        custom.pack_end(save, False, False, 0)
        grid.attach(custom, 0, row, 2, 1)
        row += 1

        # Saved timers: start with one click, move up/down, sort, delete.
        saved_head = Gtk.Box(spacing=6)
        saved_head.pack_start(heading(_("Saved timers")), True, True, 0)
        for text, key in ((_("By duration"), "seconds"),
                          (_("By name"), "name")):
            btn = Gtk.Button(label="⇅ " + text)
            btn.set_tooltip_text(_("Sort the saved timers"))
            btn.connect("clicked", lambda _b, k=key: self.sort_saved_timers(k))
            saved_head.pack_end(btn, False, False, 0)
        grid.attach(saved_head, 0, row, 2, 1)
        row += 1
        self.saved_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.saved_list.get_style_context().add_class("frame")
        placeholder = Gtk.Label(
            label=_("No saved timers. Set one above and press 💾."), margin=18)
        placeholder.get_style_context().add_class("dim-label")
        placeholder.show()
        self.saved_list.set_placeholder(placeholder)
        grid.attach(self.saved_list, 0, row, 2, 1)
        row += 1

        # Pomodoro: work and breaks in a chain, one click to start.
        grid.attach(heading("🍅 " + _("Pomodoro")), 0, row, 2, 1)
        row += 1
        pcfg = self.cfg.get("pomodoro") or core.DEFAULT_CONFIG["pomodoro"]
        pgrid = Gtk.Grid(column_spacing=8, row_spacing=6)
        self.pomo_spins = {}
        fields = (("work", _("Work"), 1, 180, _("min")),
                  ("short", _("Break"), 1, 60, _("min")),
                  ("long", _("Long break"), 1, 120, _("min")),
                  ("every", _("Long break every"), 1, 12, _("works")),
                  ("rounds", _("Works in all"), 0, 99, _("(0 = no end)")))
        for index, (key, text, low, high, unit) in enumerate(fields):
            spin = Gtk.SpinButton.new_with_range(low, high, 1)
            spin.set_value(int(pcfg.get(key, core.DEFAULT_CONFIG["pomodoro"][key])))
            spin.set_numeric(True)
            self.pomo_spins[key] = spin
            pgrid.attach(label(text), 0, index, 1, 1)
            pgrid.attach(spin, 1, index, 1, 1)
            unit_label = Gtk.Label(label=unit, xalign=0)
            unit_label.get_style_context().add_class("dim-label")
            pgrid.attach(unit_label, 2, index, 1, 1)
        pomo_start = Gtk.Button(label="🍅 " + _("Start pomodoro"),
                                valign=Gtk.Align.END, hexpand=True,
                                halign=Gtk.Align.END)
        pomo_start.get_style_context().add_class("suggested-action")
        pomo_start.connect("clicked", lambda *_a: self.on_pomodoro_start())
        pgrid.attach(pomo_start, 3, 0, 1, len(fields))
        grid.attach(pgrid, 0, row, 2, 1)
        row += 1

        # Statistics: completed work sessions, today / week / last 7 days.
        self.pomo_summary = Gtk.Label(xalign=0, wrap=True)
        grid.attach(self.pomo_summary, 0, row, 2, 1)
        row += 1
        bars = Gtk.Grid(column_spacing=10, row_spacing=2,
                        column_homogeneous=True)
        self.pomo_bars = []
        for column in range(7):
            count = Gtk.Label()
            count.get_style_context().add_class("dim-label")
            bar = Gtk.LevelBar(orientation=Gtk.Orientation.VERTICAL,
                               inverted=True, height_request=48)
            bar.set_mode(Gtk.LevelBarMode.CONTINUOUS)
            day = Gtk.Label()
            bars.attach(count, column, 0, 1, 1)
            bars.attach(bar, column, 1, 1, 1)
            bars.attach(day, column, 2, 1, 1)
            self.pomo_bars.append((count, bar, day))
        grid.attach(bars, 0, row, 2, 1)
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
        self.refresh_saved_timers()
        self.refresh_pomodoro_stats()
        return scroll

    def refresh_pomodoro_stats(self):
        stats = core.pomodoro_stats()
        self.pomo_summary.set_markup(
            "<b>%s</b>  %d 🍅 (%s)   ·   <b>%s</b>  %d 🍅 (%s)" % (
                GLib.markup_escape_text(_("Today")), stats["today"],
                minutes_text(stats["today_minutes"]),
                GLib.markup_escape_text(_("This week")), stats["week"],
                minutes_text(stats["week_minutes"])))
        top = max([1] + [count for _d, _w, count in stats["days"]])
        names = day_names()
        for (count_label, bar, day_label), (_date, weekday, count) in zip(
                self.pomo_bars, stats["days"]):
            count_label.set_text(str(count) if count else "")
            bar.set_max_value(top)
            bar.set_value(count)
            day_label.set_text(names[weekday])

    def on_pomodoro_start(self):
        self.cfg["pomodoro"] = {key: spin.get_value_as_int()
                                for key, spin in self.pomo_spins.items()}
        tcfg = self.cfg["timer"]
        tcfg["sound"] = self.timer_sound.get()
        tcfg["voice"] = self.timer_voice.get_active_id() or ""
        core.save_config(self.cfg)
        _item, error = core.start_pomodoro(self.cfg)
        self.refresh_countdowns()
        if error:
            message(self, _("Could not start the timer"), detail=error)

    # -- saved timers

    def _custom_seconds(self):
        hours, minutes, seconds = (s.get_value_as_int()
                                   for s in self.timer_spins)
        return hours * 3600 + minutes * 60 + seconds

    def on_save_timer(self):
        total = self._custom_seconds()
        if total <= 0:
            return
        saved = self.cfg["timer"].setdefault("saved", [])
        saved.append({
            "id": uuid.uuid4().hex[:8],
            "name": self.timer_name.get_text().strip(),
            "seconds": total,
            "sound": self.timer_sound.get(),
            "text": self.timer_text.get_text().strip(),
            "voice": self.timer_voice.get_active_id() or "",
        })
        core.save_config(self.cfg)
        self.refresh_saved_timers()
        self.app.build_menu()

    def refresh_saved_timers(self):
        for child in self.saved_list.get_children():
            self.saved_list.remove(child)
        saved = self.cfg["timer"].get("saved", [])
        for index, item in enumerate(saved):
            self.saved_list.add(SavedTimerRow(self, item, index, len(saved)))
        self.saved_list.show_all()

    def start_saved_timer(self, item):
        _item, error = core.start_countdown(
            int(item.get("seconds", 0)), item.get("name", ""),
            item.get("sound") or self.cfg["timer"].get("sound"),
            item.get("text", ""), item.get("voice", ""),
            self.cfg["timer"].get("repeat", 3))
        self.refresh_countdowns()
        if error:
            message(self, _("Could not start the timer"), detail=error)

    def move_saved_timer(self, index, step):
        saved = self.cfg["timer"].get("saved", [])
        other = index + step
        if 0 <= other < len(saved):
            saved[index], saved[other] = saved[other], saved[index]
            core.save_config(self.cfg)
            self.refresh_saved_timers()
            self.app.build_menu()

    def sort_saved_timers(self, key):
        saved = self.cfg["timer"].get("saved", [])
        if key == "name":
            saved.sort(key=lambda t: (t.get("name") or "").casefold())
        else:
            saved.sort(key=lambda t: int(t.get("seconds", 0)))
        core.save_config(self.cfg)
        self.refresh_saved_timers()
        self.app.build_menu()

    def delete_saved_timer(self, item):
        title = item.get("name") or core.format_duration(item.get("seconds", 0))
        dlg = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text=_("Delete saved timer «%s»?") % title)
        dlg.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        dlg.add_button(_("Delete"), Gtk.ResponseType.OK) \
            .get_style_context().add_class("destructive-action")
        if dlg.run() == Gtk.ResponseType.OK:
            self.cfg["timer"]["saved"] = [
                t for t in self.cfg["timer"].get("saved", [])
                if t.get("id") != item.get("id")]
            core.save_config(self.cfg)
            self.refresh_saved_timers()
            self.app.build_menu()
        dlg.destroy()

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

    def toggle_countdown(self, item):
        """Pause a running countdown, or resume a paused one (a pomodoro
        phase too: the chain simply waits)."""
        if item.get("paused"):
            error = core.resume_countdown(item["id"])
            if error:
                message(self, _("Could not start the timer"), detail=error)
        else:
            core.pause_countdown(item["id"])
        self.refresh_countdowns()

    def cancel_countdown(self, countdown_id):
        core.cancel_countdown(countdown_id)
        self.refresh_countdowns()

    @staticmethod
    def _countdown_keys(items):
        """What a redraw depends on: ids and paused state (the tray or
        the applet may pause a timer behind our back)."""
        return [(c["id"], bool(c.get("paused"))) for c in items]

    def refresh_countdowns(self, prune=False):
        items = core.prune_countdowns() if prune else core.list_countdowns()
        items = sorted(items, key=lambda c: c.get("end", ""))
        self._countdown_ids = self._countdown_keys(items)
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
            self.refresh_pomodoro_stats()   # a work session may have ended
        elif self._countdown_keys(core.list_countdowns()) != self._countdown_ids:
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

        # Quiet night: silences a range of hours without touching the grid
        # above, so switching it off brings every chosen hour back.
        qbox = Gtk.Box(spacing=6)
        self.quiet = Gtk.CheckButton(label="🌙 " + _("Quiet night from"))
        self.quiet.set_active(bool(cuckoo.get("quiet")))
        self.quiet_from = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.quiet_from.set_value(int(cuckoo.get("quiet_from", 22)))
        self.quiet_to = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.quiet_to.set_value(int(cuckoo.get("quiet_to", 7)))
        for spin in (self.quiet_from, self.quiet_to):
            spin.set_wrap(True)
            spin.connect("output", AlarmDialog._two_digits)
            spin.connect("value-changed", self.on_cuckoo_changed)
        self.quiet.connect("toggled", self.on_cuckoo_changed)
        qbox.pack_start(self.quiet, False, False, 0)
        qbox.pack_start(self.quiet_from, False, False, 0)
        qbox.pack_start(Gtk.Label(label=_("to")), False, False, 0)
        qbox.pack_start(self.quiet_to, False, False, 0)
        grid.attach(qbox, 0, 8, 2, 1)
        self._show_quiet_hours()

        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.add(grid)
        return scroll

    def _show_quiet_hours(self):
        """Dim the hour buttons silenced by the quiet night."""
        quiet = core.quiet_hours(self.cfg["cuckoo"])
        for spin in (self.quiet_from, self.quiet_to):
            spin.set_sensitive(self.quiet.get_active())
        for hour, button in enumerate(self.hour_buttons):
            ctx = button.get_style_context()
            if hour in quiet:
                ctx.add_class("clockoo-dimmed")
            else:
                ctx.remove_class("clockoo-dimmed")

    # -- stopwatch page

    def _stopwatch_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin=18)
        self.sw_label = Gtk.Label()
        box.pack_start(self.sw_label, False, False, 12)

        buttons = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
        self.sw_start = Gtk.Button()
        self.sw_start.get_style_context().add_class("suggested-action")
        self.sw_start.connect("clicked", lambda *_a: self.on_sw_start())
        self.sw_lap = Gtk.Button(label="🏁 " + _("Lap"))
        self.sw_lap.connect("clicked", lambda *_a: self.on_sw_lap())
        self.sw_reset = Gtk.Button(label="↺ " + _("Reset"))
        self.sw_reset.connect("clicked", lambda *_a: self.on_sw_reset())
        for btn in (self.sw_start, self.sw_lap, self.sw_reset):
            buttons.pack_start(btn, False, False, 0)
        box.pack_start(buttons, False, False, 0)

        scroll = Gtk.ScrolledWindow(vexpand=True,
                                    hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.sw_laps = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.sw_laps.get_style_context().add_class("frame")
        placeholder = Gtk.Label(label=_("No laps yet."), margin=18)
        placeholder.get_style_context().add_class("dim-label")
        placeholder.show()
        self.sw_laps.set_placeholder(placeholder)
        scroll.add(self.sw_laps)
        box.pack_start(scroll, True, True, 0)

        # State in ~/.config/Clockoo/stopwatch.json (wall-clock times), so
        # the stopwatch survives a restart and keeps counting meanwhile.
        self.sw = core.load_stopwatch()
        for index, (lap, total) in enumerate(self.sw["laps"]):
            self._sw_lap_row(index + 1, lap, total)
        self.sw_timeout = None
        if self.sw["running"]:
            self.sw_timeout = GLib.timeout_add(47, self._sw_refresh)
        self._sw_refresh()
        return box

    @staticmethod
    def _sw_text(seconds):
        minutes, secs = divmod(max(0.0, seconds), 60)
        hours, minutes = divmod(int(minutes), 60)
        hundredths = int((secs - int(secs)) * 100)
        if hours:
            return "%d:%02d:%02d.%02d" % (hours, minutes, int(secs), hundredths)
        return "%02d:%02d.%02d" % (minutes, int(secs), hundredths)

    def _sw_elapsed(self):
        if self.sw["running"]:
            return self.sw["base"] + time.time() - self.sw["since"]
        return self.sw["base"]

    def _sw_refresh(self):
        self.sw_label.set_markup(
            "<span size='300%%' weight='bold' font_features='tnum'>%s</span>"
            % self._sw_text(self._sw_elapsed()))
        self.sw_start.set_label(("⏸ " + _("Pause")) if self.sw["running"] else
                                ("▶ " + _("Start")))
        self.sw_lap.set_sensitive(self.sw["running"])
        self.sw_reset.set_sensitive(not self.sw["running"] and
                                    self.sw["base"] > 0)
        return True

    def on_sw_start(self):
        now = time.time()
        if self.sw["running"]:
            self.sw["base"] += now - self.sw["since"]
            self.sw["running"] = False
            if self.sw_timeout:
                GLib.source_remove(self.sw_timeout)
                self.sw_timeout = None
        else:
            self.sw["since"] = now
            self.sw["running"] = True
            self.sw_timeout = GLib.timeout_add(47, self._sw_refresh)
        core.save_stopwatch(self.sw)
        self._sw_refresh()

    def _sw_lap_row(self, number, lap, total):
        row = Gtk.Box(spacing=12, margin=6, margin_start=12, margin_end=12)
        label_n = Gtk.Label(label="#%d" % number, xalign=0)
        label_n.get_style_context().add_class("dim-label")
        label_lap = Gtk.Label(xalign=0, hexpand=True)
        label_lap.set_markup("<b>%s</b>" % self._sw_text(lap))
        label_total = Gtk.Label(label=self._sw_text(total), xalign=1)
        label_total.get_style_context().add_class("dim-label")
        for widget in (label_n, label_lap, label_total):
            row.pack_start(widget, widget is label_lap, widget is label_lap, 0)
        self.sw_laps.insert(row, 0)          # newest lap on top
        self.sw_laps.show_all()

    def on_sw_lap(self):
        total = self._sw_elapsed()
        previous = self.sw["laps"][-1][1] if self.sw["laps"] else 0.0
        self.sw["laps"].append([total - previous, total])
        core.save_stopwatch(self.sw)
        self._sw_lap_row(len(self.sw["laps"]), total - previous, total)

    def on_sw_reset(self):
        self.sw.update(running=False, base=0.0, since=0.0, laps=[])
        core.save_stopwatch(self.sw)
        for child in self.sw_laps.get_children():
            self.sw_laps.remove(child)
        self._sw_refresh()

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
        cuckoo["quiet"] = self.quiet.get_active()
        cuckoo["quiet_from"] = self.quiet_from.get_value_as_int()
        cuckoo["quiet_to"] = self.quiet_to.get_value_as_int()
        self._show_quiet_hours()
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
        css = Gtk.CssProvider()
        css.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # Light ↔ dark theme switch: swap wood and brass icons live.
        settings = Gtk.Settings.get_default()
        if settings:
            for prop in ("gtk-theme-name", "gtk-application-prefer-dark-theme"):
                settings.connect("notify::" + prop,
                                 lambda *_a: GLib.idle_add(self.update_icons))
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
        if not self.window.is_visible():
            # Open on the monitor under the mouse, never across two screens.
            center_on_pointer_monitor(self.window)
            self.window.show_all()
        if page:
            self.window.stack.set_visible_child_name(page)
        self.window.present()

    def update_icons(self):
        """Apply the icon style (or the new theme) to window and tray."""
        name = icon_name(self.cfg)
        if self.window:
            self.window.set_icon_name(name)
        if self.tray is not None:
            if XApp is not None and isinstance(self.tray, XApp.StatusIcon):
                self.tray.set_icon_name(name)
            else:
                self.tray.set_from_icon_name(name)
        return False

    def start_saved(self, item):
        """Tray shortcut for a saved timer."""
        tcfg = self.cfg["timer"]
        _item, error = core.start_countdown(
            int(item.get("seconds", 0)), item.get("name", ""),
            item.get("sound") or tcfg.get("sound"), item.get("text", ""),
            item.get("voice", ""), tcfg.get("repeat", 3))
        if error:
            message(self.window, _("Could not start the timer"), detail=error)
        elif self.window:
            self.window.refresh_countdowns()

    def start_pomodoro(self):
        """Tray shortcut: a pomodoro with the saved settings."""
        _item, error = core.start_pomodoro(self.cfg)
        if error:
            message(self.window, _("Could not start the timer"), detail=error)
        elif self.window:
            self.window.refresh_countdowns()

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
            self.tray.set_icon_name(icon_name(self.cfg))
            self.tray.connect("activate", lambda *_a: self.toggle_window())
        else:
            try:
                self.tray = Gtk.StatusIcon.new_from_icon_name(
                    icon_name(self.cfg))
                self.tray.connect("activate", lambda *_a: self.toggle_window())
            except (AttributeError, TypeError):
                self.tray = None
        self._build_menu()

    def build_menu(self):
        """Public: rebuild the tray menu (e.g. after saving a timer)."""
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
        for item in self.cfg["timer"].get("saved", []):
            label = core.format_duration(item.get("seconds", 0))
            if item.get("name"):
                label += " — " + item["name"]
            entry = Gtk.MenuItem(label="💾 " + label)
            entry.connect("activate", lambda _i, t=item: self.start_saved(t))
            menu.append(entry)
        pomodoro = Gtk.MenuItem(label="🍅 " + _("Start pomodoro"))
        pomodoro.connect("activate", lambda *_a: self.start_pomodoro())
        menu.append(pomodoro)
        self.pomo_stats_item = Gtk.MenuItem(label="")
        self.pomo_stats_item.set_sensitive(False)
        menu.append(self.pomo_stats_item)
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
        stats = core.pomodoro_stats()
        self.pomo_stats_item.set_label("    %s %d 🍅 · %s %d 🍅" % (
            _("Today"), stats["today"], _("This week"), stats["week"]))
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
