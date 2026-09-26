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

# Python muss auf 3.10 festgenagelt werden. Das pygame-Rezept von
# python-for-android holt fest pygame 2.1.0, und dessen C-Code bindet
# <longintrepr.h> ein. Diese Datei liegt nur bis Python 3.10 im
# öffentlichen Include-Ordner; ab 3.11 ist sie nach cpython/
# gewandert. Ohne die Festlegung baut p4a gegen Python 3.14, und der
# Übersetzer bricht mit "longintrepr.h file not found" ab.
#
# hostpython3 muss dieselbe Fassung sein wie python3.
#
# numpy ist optional: das Spiel rechnet damit die Felsumrisse sauberer
# frei, kommt aber auch ohne aus. Wenn du es willst, hinten anhängen.
requirements = python3==3.10.12,hostpython3==3.10.12,pygame

# Das Spiel rechnet in 1024x1024. Hochkant bleibt unten Platz für die
# Bedienknöpfe; quer wäre das Bild größer, aber die Knöpfe lägen darauf.
orientation = portrait
fullscreen = 1

# Ladebildschirm, bis Python hochgefahren ist
android.presplash_color = #000000

# Sobald du ein Symbol hast (512x512 png), diese Zeile einkommentieren:
# icon.filename = %(source.dir)s/icon.png

# Die Lizenzen des Android-SDK ohne Rückfrage annehmen. Ohne das
# bleibt der Bau auf dem Server an einer Eingabeaufforderung stehen,
# die niemand beantworten kann.
android.accept_sdk_license = True

# Android 14 als Ziel, ab Android 7 lauffähig
android.api = 34
android.minapi = 24
android.ndk_api = 24

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
