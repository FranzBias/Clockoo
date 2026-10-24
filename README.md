<a id="top"></a>

# 🐦⏰ Clockoo

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
![Made with love](https://img.shields.io/badge/made%20with-%E2%9D%A4%EF%B8%8F%20by%20Francesco-blueviolet)
[![GitLab mirror](https://img.shields.io/badge/mirror-GitLab-FC6D26?logo=gitlab&logoColor=white)](https://gitlab.com/FranzBias/Clockoo)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![GTK](https://img.shields.io/badge/GUI-GTK%203-4A86CF)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)
![Version](https://img.shields.io/badge/version-0.2.0-blue)

[🇬🇧 English](#english) · [🇮🇹 Italiano](#italiano) · [🇩🇪 Deutsch](#deutsch) · [🇪🇸 Español](#espanol) · [🇫🇷 Français](#francais) · [🇳🇱 Nederlands](#nederlands) · [🇷🇺 Русский](#russkiy) · [🇸🇦 العربية](#arabic) · [🇨🇳 中文](#zhongwen) · [🇯🇵 日本語](#nihongo) · [🙏 Credits](#credits)

<p align="center">
  <img src="screenshots/alarms.jpg" alt="Clockoo — Alarms tab" width="48%">
  <img src="screenshots/edit-alarm.jpg" alt="Clockoo — editing an alarm with a text read aloud" width="40%">
</p>
<p align="center">
  <img src="screenshots/timer.jpg" alt="Clockoo — Timer tab with a running timer" width="45%">
  <img src="screenshots/cuckoo.jpg" alt="Clockoo — Cuckoo tab" width="45%">
</p>
<p align="center">
  <img src="screenshots/settings.jpg" alt="Clockoo — interface language and sounds folder" width="30%">
</p>

---

<a id="english"></a>

## 🇬🇧 English

**Clockoo** is an hourly cuckoo, a set of alarms that can read a text aloud, and a countdown timer for the Linux desktop — with a small window and a tray icon.

### ✨ Features

- **Hourly cuckoo** — pick the hours and the minute; optionally it calls **as many times as the hour**, like a real cuckoo clock.
- **Named alarms** — on chosen weekdays or just once, each with its own sound, repeat count and an optional **text read aloud**.
- **⏳ Timer** — 1, 3, 5, 10, 15, 30 minutes or any h:m:s, with a live countdown and *Cancel*; also from the tray menu.
- **Stop / Snooze** on every notification.
- **Rings with the window closed** — everything is a systemd *user* timer, so it keeps ringing even if the window, the tray or Cinnamon restarts.
- **13 CC0 sounds included**, or choose any folder of your own sounds.
- **Natural offline voices** with piper (optional), otherwise `spd-say`.
- Interface in English, Italian and German.

### 🚀 Install

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # for the current user, no sudo
```

Needs `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-notify-0.7`, `pw-play` or `paplay`; `gir1.2-xapp-1.0` for the tray icon. Clockoo is then in your menu and starts in the tray at login.

### 🗣️ Voices (optional)

```bash
./get-voices.sh       # asks first, ~500 MB, every file checked by SHA-256
```

Downloads piper and 8 voices with free licences (IT paola, riccardo · DE kerstin, thorsten · EN kristin, ljspeech, norman, john). Without it, texts are read by speech-dispatcher.

### ⚙️ How it works

The window only edits `~/.config/Clockoo/config.json`; `clockoo_core.py` turns it into systemd user timers (`clockoo-*`), and systemd starts `clockoo_ring.py` at the right moment. See them with `systemctl --user list-timers 'clockoo-*'`.

### 📜 License

MIT — see [LICENSE](LICENSE). Voices and sounds keep their own licences: see [Credits](#credits).

[⬆ top](#top)

---

<a id="italiano"></a>

## 🇮🇹 Italiano

**Clockoo** è un cucù orario, delle sveglie che sanno leggere un testo ad alta voce e un timer per il desktop Linux — con una piccola finestra e un'icona nel tray.

### ✨ Funzioni

- **Cucù orario** — scegli le ore e il minuto; se vuoi chiama **tante volte quante sono le ore**, come un vero orologio a cucù.
- **Sveglie con nome** — nei giorni scelti o una volta sola, ognuna col suo suono, le sue ripetizioni e un **testo letto ad alta voce** facoltativo.
- **⏳ Timer** — 1, 3, 5, 10, 15, 30 minuti o qualsiasi h:m:s, con il conto alla rovescia dal vivo e *Annulla*; anche dal menu del tray.
- **Stop / Posticipa** su ogni notifica.
- **Suona a finestra chiusa** — tutto è un timer *utente* di systemd: suona anche se la finestra, il tray o Cinnamon si riavviano.
- **13 suoni CC0 inclusi**, oppure una cartella qualsiasi di suoni tuoi.
- **Voci naturali offline** con piper (facoltativo), altrimenti `spd-say`.
- Interfaccia in inglese, italiano e tedesco.

### 🚀 Installazione

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # per l'utente corrente, senza sudo
```

Servono `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-notify-0.7`, `pw-play` o `paplay`; `gir1.2-xapp-1.0` per l'icona nel tray. Poi Clockoo è nel menu e parte nel tray all'accesso.

### 🗣️ Voci (facoltativo)

```bash
./get-voices.sh       # chiede prima, ~500 MB, ogni file controllato con SHA-256
```

Scarica piper e 8 voci con licenze libere (IT paola, riccardo · DE kerstin, thorsten · EN kristin, ljspeech, norman, john). Senza, i testi li legge speech-dispatcher.

### ⚙️ Come funziona

La finestra modifica solo `~/.config/Clockoo/config.json`; `clockoo_core.py` lo trasforma in timer utente di systemd (`clockoo-*`), e systemd avvia `clockoo_ring.py` al momento giusto. Li vedi con `systemctl --user list-timers 'clockoo-*'`.

### 📜 Licenza

MIT — vedi [LICENSE](LICENSE). Voci e suoni hanno le loro licenze: vedi [Credits](#credits).

[⬆ inizio](#top)

---

<a id="deutsch"></a>

## 🇩🇪 Deutsch

**Clockoo** ist ein stündlicher Kuckuck, Wecker, die einen Text vorlesen können, und ein Countdown-Timer für den Linux-Desktop — mit einem kleinen Fenster und einem Tray-Symbol.

### ✨ Funktionen

- **Stündlicher Kuckuck** — Stunden und Minute wählen; auf Wunsch ruft er **so oft, wie es Uhr ist**, wie eine echte Kuckucksuhr.
- **Wecker mit Namen** — an gewählten Wochentagen oder einmalig, jeder mit eigenem Klang, Wiederholungen und optionalem **vorgelesenem Text**.
- **⏳ Timer** — 1, 3, 5, 10, 15, 30 Minuten oder beliebige h:m:s, mit Live-Countdown und *Abbrechen*; auch über das Tray-Menü.
- **Stopp / Schlummern** in jeder Benachrichtigung.
- **Klingelt bei geschlossenem Fenster** — alles sind systemd-*Benutzer*-Timer: Er klingelt auch, wenn Fenster, Tray oder Cinnamon neu starten.
- **13 CC0-Klänge enthalten**, oder ein beliebiger eigener Klangordner.
- **Natürliche Offline-Stimmen** mit piper (optional), sonst `spd-say`.
- Oberfläche auf Englisch, Italienisch und Deutsch.

### 🚀 Installation

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # für den aktuellen Benutzer, ohne sudo
```

Benötigt `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-notify-0.7`, `pw-play` oder `paplay`; `gir1.2-xapp-1.0` für das Tray-Symbol. Danach steht Clockoo im Menü und startet beim Anmelden im Tray.

### 🗣️ Stimmen (optional)

```bash
./get-voices.sh       # fragt zuerst, ~500 MB, jede Datei per SHA-256 geprüft
```

Lädt piper und 8 Stimmen mit freien Lizenzen (IT paola, riccardo · DE kerstin, thorsten · EN kristin, ljspeech, norman, john). Ohne sie liest speech-dispatcher die Texte vor.

### ⚙️ So funktioniert es

Das Fenster bearbeitet nur `~/.config/Clockoo/config.json`; `clockoo_core.py` macht daraus systemd-Benutzer-Timer (`clockoo-*`), und systemd startet `clockoo_ring.py` zur richtigen Zeit. Anzeigen mit `systemctl --user list-timers 'clockoo-*'`.

### 📜 Lizenz

MIT — siehe [LICENSE](LICENSE). Stimmen und Klänge behalten ihre eigenen Lizenzen: siehe [Credits](#credits).

[⬆ nach oben](#top)

---

<a id="espanol"></a>

## 🇪🇸 Español

**Clockoo** es un cucú horario, alarmas que pueden leer un texto en voz alta y un temporizador para el escritorio Linux — con una pequeña ventana y un icono en la bandeja.

### ✨ Funciones

- **Cucú horario** — elige las horas y el minuto; si quieres, canta **tantas veces como la hora**, como un auténtico reloj de cucú.
- **Alarmas con nombre** — en los días elegidos o una sola vez, cada una con su sonido, sus repeticiones y un **texto leído en voz alta** opcional.
- **⏳ Temporizador** — 1, 3, 5, 10, 15, 30 minutos o cualquier h:m:s, con cuenta atrás en vivo y *Cancelar*; también desde el menú de la bandeja.
- **Detener / Posponer** en cada notificación.
- **Suena con la ventana cerrada** — todo es un temporizador de *usuario* de systemd: suena aunque se reinicien la ventana, la bandeja o Cinnamon.
- **13 sonidos CC0 incluidos**, o cualquier carpeta con tus propios sonidos.
- **Voces naturales sin conexión** con piper (opcional); si no, `spd-say`.
- Interfaz en inglés, italiano y alemán.

### 🚀 Instalación

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # para el usuario actual, sin sudo
```

Necesita `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-notify-0.7`, `pw-play` o `paplay`; `gir1.2-xapp-1.0` para el icono de la bandeja. Después Clockoo aparece en el menú y arranca en la bandeja al iniciar sesión.

### 🗣️ Voces (opcional)

```bash
./get-voices.sh       # pregunta antes, ~500 MB, cada archivo verificado con SHA-256
```

Descarga piper y 8 voces con licencias libres (IT paola, riccardo · DE kerstin, thorsten · EN kristin, ljspeech, norman, john). Sin ellas, speech-dispatcher lee los textos.

### ⚙️ Cómo funciona

La ventana solo modifica `~/.config/Clockoo/config.json`; `clockoo_core.py` lo convierte en temporizadores de usuario de systemd (`clockoo-*`), y systemd lanza `clockoo_ring.py` en el momento justo. Puedes verlos con `systemctl --user list-timers 'clockoo-*'`.

### 📜 Licencia

MIT — ver [LICENSE](LICENSE). Las voces y los sonidos conservan sus propias licencias: ver [Credits](#credits).

[⬆ arriba](#top)

---

<a id="francais"></a>

## 🇫🇷 Français

**Clockoo**, c'est un coucou horaire, des alarmes qui savent lire un texte à voix haute et un minuteur pour le bureau Linux — avec une petite fenêtre et une icône dans la zone de notification.

### ✨ Fonctions

- **Coucou horaire** — choisissez les heures et la minute ; s'il le faut, il chante **autant de fois que l'heure**, comme une vraie horloge à coucou.
- **Alarmes nommées** — les jours choisis ou une seule fois, chacune avec son son, ses répétitions et un **texte lu à voix haute** facultatif.
- **⏳ Minuteur** — 1, 3, 5, 10, 15, 30 minutes ou n'importe quelle durée h:m:s, avec compte à rebours en direct et *Annuler* ; aussi depuis le menu de l'icône.
- **Arrêter / Répéter plus tard** dans chaque notification.
- **Sonne fenêtre fermée** — tout passe par des minuteurs *utilisateur* systemd : ça sonne même si la fenêtre, l'icône ou Cinnamon redémarrent.
- **13 sons CC0 inclus**, ou n'importe quel dossier de vos propres sons.
- **Voix naturelles hors ligne** avec piper (facultatif), sinon `spd-say`.
- Interface en anglais, italien et allemand.

### 🚀 Installation

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # pour l'utilisateur courant, sans sudo
```

Nécessite `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-notify-0.7`, `pw-play` ou `paplay` ; `gir1.2-xapp-1.0` pour l'icône. Clockoo est ensuite dans le menu et démarre dans la zone de notification à la connexion.

### 🗣️ Voix (facultatif)

```bash
./get-voices.sh       # demande d'abord, ~500 Mo, chaque fichier vérifié par SHA-256
```

Télécharge piper et 8 voix sous licence libre (IT paola, riccardo · DE kerstin, thorsten · EN kristin, ljspeech, norman, john). Sans elles, speech-dispatcher lit les textes.

### ⚙️ Fonctionnement

La fenêtre ne modifie que `~/.config/Clockoo/config.json` ; `clockoo_core.py` le transforme en minuteurs utilisateur systemd (`clockoo-*`), et systemd lance `clockoo_ring.py` au bon moment. Pour les voir : `systemctl --user list-timers 'clockoo-*'`.

### 📜 Licence

MIT — voir [LICENSE](LICENSE). Les voix et les sons gardent leurs propres licences : voir [Credits](#credits).

[⬆ haut](#top)

---

<a id="nederlands"></a>

## 🇳🇱 Nederlands

**Clockoo** is een koekoek op het hele uur, wekkers die een tekst kunnen voorlezen en een timer voor het Linux-bureaublad — met een klein venster en een pictogram in het systeemvak.

### ✨ Functies

- **Koekoek op het hele uur** — kies de uren en de minuut; desgewenst roept hij **zo vaak als het uur slaat**, zoals een echte koekoeksklok.
- **Wekkers met een naam** — op gekozen weekdagen of één keer, elk met eigen geluid, herhalingen en een optionele **voorgelezen tekst**.
- **⏳ Timer** — 1, 3, 5, 10, 15, 30 minuten of elke u:m:s, met live aftellen en *Annuleren*; ook via het menu van het systeemvak.
- **Stoppen / Sluimeren** in elke melding.
- **Gaat af met het venster dicht** — alles is een systemd-*gebruikers*timer: hij gaat ook af als het venster, het systeemvak of Cinnamon herstart.
- **13 CC0-geluiden inbegrepen**, of elke map met je eigen geluiden.
- **Natuurlijke offline stemmen** met piper (optioneel), anders `spd-say`.
- Interface in het Engels, Italiaans en Duits.

### 🚀 Installatie

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # voor de huidige gebruiker, zonder sudo
```

Vereist `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-notify-0.7`, `pw-play` of `paplay`; `gir1.2-xapp-1.0` voor het pictogram. Daarna staat Clockoo in het menu en start het bij het aanmelden in het systeemvak.

### 🗣️ Stemmen (optioneel)

```bash
./get-voices.sh       # vraagt eerst, ~500 MB, elk bestand gecontroleerd met SHA-256
```

Downloadt piper en 8 stemmen met vrije licenties (IT paola, riccardo · DE kerstin, thorsten · EN kristin, ljspeech, norman, john). Zonder stemmen leest speech-dispatcher de teksten voor.

### ⚙️ Hoe het werkt

Het venster bewerkt alleen `~/.config/Clockoo/config.json`; `clockoo_core.py` maakt daar systemd-gebruikerstimers van (`clockoo-*`), en systemd start `clockoo_ring.py` op het juiste moment. Bekijk ze met `systemctl --user list-timers 'clockoo-*'`.

### 📜 Licentie

MIT — zie [LICENSE](LICENSE). Stemmen en geluiden houden hun eigen licenties: zie [Credits](#credits).

[⬆ boven](#top)

---

<a id="russkiy"></a>

## 🇷🇺 Русский

**Clockoo** — это кукушка каждый час, будильники, которые умеют читать текст вслух, и таймер для рабочего стола Linux — с небольшим окном и значком в трее.

### ✨ Возможности

- **Кукушка каждый час** — выберите часы и минуту; по желанию она кукует **столько раз, сколько сейчас часов**, как настоящие часы с кукушкой.
- **Будильники с названием** — в выбранные дни недели или один раз, у каждого свой звук, число повторов и необязательный **текст, читаемый вслух**.
- **⏳ Таймер** — 1, 3, 5, 10, 15, 30 минут или любое ч:м:с, с обратным отсчётом и кнопкой *Отмена*; также из меню в трее.
- **Стоп / Отложить** в каждом уведомлении.
- **Звонит при закрытом окне** — всё работает через *пользовательские* таймеры systemd: звонок прозвучит, даже если окно, трей или Cinnamon перезапустятся.
- **13 звуков CC0 в комплекте** или любая папка с вашими звуками.
- **Естественные офлайн-голоса** через piper (необязательно), иначе `spd-say`.
- Интерфейс на английском, итальянском и немецком.

### 🚀 Установка

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # для текущего пользователя, без sudo
```

Нужны `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-notify-0.7`, `pw-play` или `paplay`; `gir1.2-xapp-1.0` для значка в трее. После этого Clockoo появится в меню и будет запускаться в трее при входе.

### 🗣️ Голоса (необязательно)

```bash
./get-voices.sh       # сначала спрашивает, ~500 МБ, каждый файл проверяется по SHA-256
```

Скачивает piper и 8 голосов со свободными лицензиями (IT paola, riccardo · DE kerstin, thorsten · EN kristin, ljspeech, norman, john). Без них тексты читает speech-dispatcher.

### ⚙️ Как это работает

Окно лишь редактирует `~/.config/Clockoo/config.json`; `clockoo_core.py` превращает его в пользовательские таймеры systemd (`clockoo-*`), а systemd в нужный момент запускает `clockoo_ring.py`. Посмотреть: `systemctl --user list-timers 'clockoo-*'`.

### 📜 Лицензия

MIT — см. [LICENSE](LICENSE). У голосов и звуков свои лицензии: см. [Credits](#credits).

[⬆ наверх](#top)

---

<a id="arabic"></a>

## 🇸🇦 العربية

<div dir="rtl">

**Clockoo** هو وقواق يصيح كل ساعة، ومنبّهات تستطيع قراءة نص بصوت عالٍ، ومؤقّت تنازلي لسطح مكتب لينكس — مع نافذة صغيرة وأيقونة في شريط النظام.

### ✨ الميزات

- **وقواق كل ساعة** — اختر الساعات والدقيقة؛ ويمكنه أن يصيح **بعدد الساعة**، مثل ساعة الوقواق الحقيقية.
- **منبّهات بأسماء** — في أيام الأسبوع التي تختارها أو مرة واحدة، لكلّ منها صوتها وعدد تكراراتها و**نص يُقرأ بصوت عالٍ** اختياري.
- **⏳ مؤقّت** — 1 أو 3 أو 5 أو 10 أو 15 أو 30 دقيقة أو أي مدة س:د:ث، مع عدّ تنازلي مباشر وزر *إلغاء*؛ ومن قائمة شريط النظام أيضاً.
- **إيقاف / تأجيل** في كل إشعار.
- **يرنّ والنافذة مغلقة** — كل شيء مؤقّت *مستخدم* في systemd، فيرنّ حتى لو أُعيد تشغيل النافذة أو شريط النظام أو Cinnamon.
- **13 صوتاً بترخيص CC0 مضمّنة**، أو أي مجلد لأصواتك الخاصة.
- **أصوات طبيعية دون اتصال** عبر piper (اختياري)، وإلا `spd-say`.
- الواجهة بالإنجليزية والإيطالية والألمانية.

### 🚀 التثبيت

</div>

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # for the current user, no sudo
```

<div dir="rtl">

يتطلّب `python3-gi` و`gir1.2-gtk-3.0` و`gir1.2-notify-0.7` و`pw-play` أو `paplay`؛ و`gir1.2-xapp-1.0` لأيقونة شريط النظام. بعدها يظهر Clockoo في القائمة ويبدأ في شريط النظام عند تسجيل الدخول.

### 🗣️ الأصوات (اختياري)

</div>

```bash
./get-voices.sh       # asks first, ~500 MB, SHA-256 checked
```

<div dir="rtl">

ينزّل piper و8 أصوات بتراخيص حرّة (IT paola, riccardo · DE kerstin, thorsten · EN kristin, ljspeech, norman, john). من دونها يقرأ speech-dispatcher النصوص.

### ⚙️ كيف يعمل

النافذة تعدّل الملف `~/.config/Clockoo/config.json` فقط؛ ويحوّله `clockoo_core.py` إلى مؤقّتات مستخدم في systemd (`clockoo-*`)، ثم يشغّل systemd الملف `clockoo_ring.py` في اللحظة المناسبة. لعرضها: `systemctl --user list-timers 'clockoo-*'`.

### 📜 الترخيص

MIT — انظر [LICENSE](LICENSE). للأصوات والمؤثرات الصوتية تراخيصها الخاصة: انظر [Credits](#credits).

</div>

[⬆ الأعلى](#top)

---

<a id="zhongwen"></a>

## 🇨🇳 中文

**Clockoo** 是一款适用于 Linux 桌面的整点布谷鸟报时、能朗读文字的闹钟和倒计时器——带有一个小窗口和托盘图标。

### ✨ 功能

- **整点布谷鸟** —— 选择小时和分钟；还可以像真正的布谷鸟钟一样，**几点就叫几声**。
- **带名称的闹钟** —— 在选定的星期几或仅一次，每个闹钟都有自己的声音、重复次数和可选的**朗读文字**。
- **⏳ 计时器** —— 1、3、5、10、15、30 分钟或任意时:分:秒，实时倒计时并可*取消*；也可从托盘菜单启动。
- 每条通知都有**停止 / 稍后提醒**。
- **关闭窗口也会响** —— 一切都是 systemd *用户*定时器：即使窗口、托盘或 Cinnamon 重启，照样会响。
- **内置 13 个 CC0 声音**，也可以选择任意存放自己声音的文件夹。
- 使用 piper 的**自然离线语音**（可选），否则使用 `spd-say`。
- 界面提供英语、意大利语和德语。

### 🚀 安装

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # 仅当前用户，无需 sudo
```

需要 `python3-gi`、`gir1.2-gtk-3.0`、`gir1.2-notify-0.7`、`pw-play` 或 `paplay`；托盘图标需要 `gir1.2-xapp-1.0`。之后 Clockoo 会出现在菜单中，并在登录时启动到托盘。

### 🗣️ 语音（可选）

```bash
./get-voices.sh       # 先询问，约 500 MB，每个文件都经 SHA-256 校验
```

下载 piper 和 8 个自由许可的语音（IT paola、riccardo · DE kerstin、thorsten · EN kristin、ljspeech、norman、john）。没有它们时，由 speech-dispatcher 朗读文字。

### ⚙️ 工作原理

窗口只修改 `~/.config/Clockoo/config.json`；`clockoo_core.py` 把它转换成 systemd 用户定时器（`clockoo-*`），systemd 在正确的时刻启动 `clockoo_ring.py`。查看：`systemctl --user list-timers 'clockoo-*'`。

### 📜 许可证

MIT —— 见 [LICENSE](LICENSE)。语音和声音保留各自的许可证：见 [Credits](#credits)。

[⬆ 返回顶部](#top)

---

<a id="nihongo"></a>

## 🇯🇵 日本語

**Clockoo** は、Linux デスクトップ向けの時報カッコウ、テキストを読み上げるアラーム、カウントダウンタイマーです。小さなウィンドウとトレイアイコン付き。

### ✨ 機能

- **時報カッコウ** —— 時と分を選べます。本物のカッコウ時計のように**時刻の数だけ鳴く**こともできます。
- **名前付きアラーム** —— 選んだ曜日または一度だけ。それぞれに音、繰り返し回数、任意の**読み上げテキスト**を設定できます。
- **⏳ タイマー** —— 1・3・5・10・15・30 分、または任意の時:分:秒。ライブのカウントダウンと*キャンセル*付き。トレイのメニューからも使えます。
- すべての通知に**停止 / スヌーズ**。
- **ウィンドウを閉じても鳴る** —— すべて systemd の*ユーザー*タイマーなので、ウィンドウやトレイ、Cinnamon が再起動しても鳴ります。
- **CC0 のサウンド 13 種類を同梱**。自分のサウンドのフォルダーも選べます。
- piper による**自然なオフライン音声**（任意）。なければ `spd-say`。
- インターフェースは英語・イタリア語・ドイツ語。

### 🚀 インストール

```bash
git clone https://github.com/FranzBias/Clockoo.git
cd Clockoo
./install.sh          # 現在のユーザー用、sudo 不要
```

`python3-gi`、`gir1.2-gtk-3.0`、`gir1.2-notify-0.7`、`pw-play` または `paplay` が必要です。トレイアイコンには `gir1.2-xapp-1.0`。インストール後はメニューに表示され、ログイン時にトレイで起動します。

### 🗣️ 音声（任意）

```bash
./get-voices.sh       # 事前に確認、約 500 MB、全ファイルを SHA-256 で検証
```

piper と自由なライセンスの音声 8 種類（IT paola・riccardo / DE kerstin・thorsten / EN kristin・ljspeech・norman・john）をダウンロードします。なければ speech-dispatcher が読み上げます。

### ⚙️ 仕組み

ウィンドウは `~/.config/Clockoo/config.json` を編集するだけです。`clockoo_core.py` がそれを systemd のユーザータイマー（`clockoo-*`）に変換し、systemd が適切なタイミングで `clockoo_ring.py` を起動します。確認：`systemctl --user list-timers 'clockoo-*'`。

### 📜 ライセンス

MIT —— [LICENSE](LICENSE) を参照。音声とサウンドはそれぞれのライセンスに従います：[Credits](#credits) を参照。

[⬆ トップへ](#top)

---

<a id="credits"></a>

## 🙏 Credits

### Speech engine

| Project | Licence | Source |
|---|---|---|
| piper 2023.11.14-2 (Michael Hansen / Rhasspy) | MIT | <https://github.com/rhasspy/piper> |

### Voices (downloaded only by `get-voices.sh`, never bundled)

| Voice | Language | Licence of the dataset | Dataset |
|---|---|---|---|
| paola (medium) | it_IT | CC0 1.0 | <https://huggingface.co/datasets/paolapersico1/Voice-Dataset-Italian> |
| riccardo (x_low) | it_IT | M-AILABS licence (BSD-style, text below) | M-AILABS Speech Dataset |
| kerstin (low) | de_DE | CC0 1.0 | <https://github.com/rhasspy/dataset-voice-kerstin> |
| thorsten (medium) | de_DE | CC0 1.0 | <https://github.com/thorstenMueller/Thorsten-Voice> |
| kristin (medium) | en_US | public domain | <https://librivox.org> |
| ljspeech (medium) | en_US | public domain | <https://keithito.com/LJ-Speech-Dataset/> |
| norman (medium) | en_US | public domain | <https://librivox.org> |
| john (medium) | en_US | public domain | <https://librivox.org> |

Voice models: <https://huggingface.co/rhasspy/piper-voices> (each with its `MODEL_CARD`, installed next to the voice).

<details>
<summary>M-AILABS licence (voice <i>riccardo</i>)</summary>

```
Copyright (c) 2017-2019 by the original creators @ M-AILABS

Copyright (c) 2020 I. Celeste Aurora Solak (github.com/i-celeste-aurora)

Redistribution and use in any form, including any commercial use, with or without
modification are permitted provided that the following conditions are met:

- Redistributions of source data must retain the above copyright notice, this list
  of conditions and the following disclaimer.
- Neither the name of the copyright holder nor the names of its contributors may be
  used to endorse or promote products derived from this downloaded data, source-code
  or binary-code without specific prior written permission.

THIS DATA IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE and/or DATA, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

Source: <https://github.com/i-celeste-aurora/m-ailabs-dataset>
</details>

### Sounds (bundled in `sounds/`, all CC0 1.0)

All from [Freesound](https://freesound.org); full table with original titles in [sounds/CREDITS.md](sounds/CREDITS.md). Thanks to
DiArchangeli, finalCrystine, Monkay, Iamgiorgio, dsp9000, edschaefer, ZyryTSounds, tedthetrumpet, dland, jwheeler91, austin1234575, newagesoup and BenjaminNelan.

### Ideas

The timer presets were inspired by the Cinnamon applets *timer@Severga* and *cinnamon-timer@jake1164*; the countdown in the panel by *quick-alarm@andreas-glaser*. No code was taken from them.

[⬆ top](#top)
