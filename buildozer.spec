[app]

# Was im Startmenü des Handys steht
title = nomal

# Interner Name (keine Leerzeichen, keine Umlaute)
package.name = nomal

# Umgekehrte Domain. Zusammen mit package.name ergibt das die
# eindeutige App-ID: online.coldfrogames.nomal
package.domain = online.coldfrogames

# Alles in diesem Ordner wandert in die APK
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,otf,json
# Bilder und Schrift liegen in Unterordnern - die müssen einzeln
# benannt werden, sonst nimmt Buildozer nur die Dateien direkt daneben.
source.include_patterns = images/*,fonts/*

version = 0.1

# python3 und pygame reicht. numpy ist optional: das Spiel rechnet
# damit die Felsumrisse sauberer frei, kommt aber auch ohne aus.
# Wenn du es willst: requirements = python3,pygame,numpy
requirements = python3,pygame

# Das Spiel rechnet in 1024x1024. Hochkant bleibt unten Platz für die
# Bedienknöpfe; quer wäre das Bild größer, aber die Knöpfe lägen darauf.
orientation = portrait
fullscreen = 1

# Ladebildschirm, bis Python hochgefahren ist
android.presplash_color = #000000

# Sobald du ein Symbol hast (512x512 png), diese Zeile einkommentieren:
# icon.filename = %(source.dir)s/icon.png

# Android 14 als Ziel, ab Android 7 lauffähig
android.api = 33
android.minapi = 21

# Korrekte NDK-Version festlegen, um Pfadfehler zu vermeiden
android.ndk = 25b

# Erster Build nur 64 Bit - das halbiert die Bauzeit. Für den Play
# Store später: android.archs = arm64-v8a, armeabi-v7a
android.archs = arm64-v8a

# Keine Berechtigungen nötig: kein Netz, und gespeichert wird in der
# privaten Ablage der App.
android.permissions =

# SDL2 ist der Unterbau von pygame
p4a.bootstrap = sdl2

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
