# Changelog

All notable changes to Clockoo (the GTK app). The Cinnamon applet
`clockoo@FranzBias` follows the same version numbers.

## 0.7.0 — 2026-10-27

- **Pause / resume** for every running timer, a pomodoro phase included
  (the chain waits while its timer is paused).

## 0.6.0 — 2026-10-27

- **Pomodoro statistics**: completed work sessions today, this week and
  over the last 7 days (bars in the Timer tab, a line in the tray menu).
  Kept in `~/.config/Clockoo/pomodoro-log.json`, last 400 days.

## 0.5.1 — 2026-10-27

- The **stopwatch survives a restart** of the app or of the computer and
  keeps counting meanwhile (`~/.config/Clockoo/stopwatch.json`).

## 0.5.0 — 2026-10-26

- **🍅 Pomodoro**: work, break and long break in a chain, all adjustable;
  from the Timer tab or the tray menu; "Stop pomodoro" in the notification.
- **Snooze per alarm** (0 = the general setting).

## 0.4.0 — 2026-10-26

- **Suspend-safe**: alarms are `Persistent` (one missed while the computer
  was off rings at the next login); timers and snoozes end at a wall-clock
  time, so one that falls during suspend rings right at wake-up.
- **🌙 Quiet night** for the cuckoo.
- **⏱ Stopwatch** tab with laps.
- Alarms: **crescendo** (soft to full volume) and an optional **heads-up**
  some minutes before.
- Players get `LC_NUMERIC=C`, so `pw-play --volume` works in every locale.

## 0.3.0 — 2026-10-26

- New **mantel-clock icon**: wood on light themes, brass on dark ones
  (or fixed in the ☰ menu).
- Alarms: two choices under the time, **Days** or **No day = rings once**.
- **Saved timers**: save, start, move up/down, sort by duration or name;
  also in the tray menu.
- The window opens on the **monitor under the mouse** (no more half on
  each screen).
- Wording: "text to read" instead of "text to read aloud".

## 0.2.0 — 2026-10-24

- First public release: hourly cuckoo, named alarms with spoken text,
  countdown timer, 13 CC0 sounds, optional piper voices.
