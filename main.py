"""nomal - Einzeldatei-Fassung fuer den Android-Build.

Aus den Einzelmodulen zusammengefuegt: konfig, texte, verse, labyrinth,
raum1, raum1_moebel, figuren, landschaft, Dialogfenster, Spielmenu und
der Spielkern aus main.py. Die Musik ist vollstaendig entfernt.

Reihenfolge der Abschnitte = Reihenfolge der frueheren Importe. Wer
etwas sucht, findet es unter der Ueberschrift mit dem alten Dateinamen.
"""
import json
import math
import os
import random
import sys
from collections import namedtuple
from datetime import datetime

import pygame

# ------------------------------------------------------------------
# Ablageorte
# ------------------------------------------------------------------
# BASIS: der Ordner, in dem diese Datei liegt. Alle Bilder und Schriften
# werden von hier gelesen - damit ist es egal, aus welchem Verzeichnis
# das Spiel gestartet wird (auf Android ist das nie der eigene Ordner).
BASIS = os.path.dirname(os.path.abspath(__file__))

# ANDROID: python-for-android setzt diese Umgebungsvariable. Nur daran
# wird das Handy erkannt - nichts anderes im Spiel fragt danach.
ANDROID = "ANDROID_ARGUMENT" in os.environ

# True, solange die Bildschirmtastatur offen ist. Dann verschwindet die
# Bildschirmbedienung - sie laege sonst unter den Tasten.
TASTATUR_OFFEN = False


def daten_pfad(name):
    """Ort fuer Dateien, die das Spiel SCHREIBT (Spielstaende,
    Einstellungen, Bestenliste).

    Auf Android ist der App-Ordner schreibgeschuetzt; beschreibbar ist
    nur die private Ablage, deren Pfad p4a in ANDROID_PRIVATE stellt.
    Am Rechner bleibt alles wie bisher neben dem Spiel liegen."""
    ordner = os.environ.get("ANDROID_PRIVATE") if ANDROID else BASIS
    return os.path.join(ordner or BASIS, os.path.basename(name))



# ######################################################################
# konfig.py
# ######################################################################
"""Zentrale Spielkonstanten.

Alles, was sich am Spiel einstellen laesst - Groessen, Zeiten, Tempi,
Positionen - steht hier an einem Ort. Die Spiellogik liegt in main.py,
die Texte in texte.py.
"""

# ---------------------------------------------------------------
# Fenster & Grundfarben
# ---------------------------------------------------------------
WIDTH = 1024
HEIGHT = 1024
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Verzeichnisse fuer Musik und Bilder
image_dir = os.path.join(BASIS, "images")

# Untersuchen-System: Rastergroesse fuer deterministische Texte
INSPECT_GRID = 128

# ---------------------------------------------------------------
# Stationspunkte & Konstruktionswelten
# (Namen und Texte sind PLATZHALTER - werden nach deiner
#  Beschreibung der 9 Stationspunkte ersetzt)
# ---------------------------------------------------------------
K_KEYS = ("k1", "k2", "k3", "k4", "k5", "k6")
OPEN_WORLDS = ("world2", "world3") + K_KEYS

# ---------------------------------------------------------------
# Welt 2: Papierverteilung
# ---------------------------------------------------------------
PAPER_COUNT = 10
PAPER_SPREAD = 2400
PAPER_MIN_DIST = 500

# Das Waldreich laeuft jetzt auch gegen die Uhr - das Spiel soll ein
# Speedrun werden. Die Rechnung dahinter: zehn Blaetter in einem Feld
# von 4800 x 4800 px ergeben als Rundreise rund 10.600 px, im dichten
# Wald mit Umwegen etwa 14.000. Gehen sind 240 px/s, sprinten 480, im
# Schnitt mit Ausdauer rund 326 px/s - macht 45 s reines Laufen. Dazu
# Suchen und zehn Gedichte. 300 s sind fuer einen geuebten Lauf bequem
# und fuer den ersten Durchgang knapp.
W2_ZEIT = 300.0

# Baeume und Staemme stehen als Ring um jedes Blatt. Eine Luecke bleibt
# immer offen, und danach wird nachgerechnet, ob das Blatt wirklich
# erreichbar ist - sonst werden Ringstuecke wieder entfernt.
W2_NEST_RADIUS = 215       # Abstand der Hindernisse vom Blatt
W2_NEST_STUECKE = 11       # so viele Plaetze hat der Ring
W2_NEST_LUECKE = 0.62      # halbe Breite der Luecke im Bogenmass
W2_NEST_FREI = 130         # um das Blatt selbst bleibt alles frei

# Die Tuer nach Welt 3 erscheint nicht irgendwo, sondern immer im Bild.
# Drumherum wird eine Lichtung geschlagen - notfalls faellt dafuer ein
# grosser Baum. Der Abstand bleibt unter der halben Bildhoehe, damit sie
# ganz zu sehen ist.
W2_TUER_ABSTAND = 290      # so weit vor dem Spieler erscheint sie
W2_TUER_LICHTUNG = 210     # Radius des freigeraeumten Kreises

# ---------------------------------------------------------------
# Schwierigkeit: unterscheidet sich nur in der Zeit
# ---------------------------------------------------------------
# Der Faktor multipliziert jede Uhr im Spiel - Waldreich, Erdreich,
# Labyrinth, die Sprintfenster und die Ewigkeit. Anfaenger bekommt gut
# die Haelfte mehr, Experte ein knappes Drittel weniger.
SCHWIERIGKEITEN = [
    ("Anfänger", 1.60, "Viel Luft. Zum Kennenlernen."),
    ("Medium",   1.00, "So ist das Spiel gedacht."),
    ("Experte",  0.70, "Für den Speedrun. Kein Umweg ist gratis."),
]
SCHWIERIGKEIT_STANDARD = 1

# Die Frau: Signal-Rhythmus der Wegweiserin
NPC_SIGNAL_INTERVALL = 8.0    # alle ~8 Sekunden zeigt sie die Richtung
# Dauer >= Intervall heisst: der Pfeil geht nie aus. Wer auf Zeit
# spielt, soll die Richtung jederzeit sehen koennen.
NPC_PFEIL_DAUER = 9.0         # so lange bleibt der Pfeil sichtbar

# ---------------------------------------------------------------
# Die 6 Welten der Storyline
# ---------------------------------------------------------------
WORLD_NAMES = {
    "room1": "Zimmer",
    "world2": "Waldreich",
    "world3": "Erdreich",
    "world4": "Tunnel",
    "world5": "Lava",
    "world6": "Entscheidungen",
}
WORLD_NR = {"room1": 1, "world2": 2, "world3": 3,
            "world4": 4, "world5": 5, "world6": 6}

# Belohnungsobjekt jeder Welt. Diese Namen tippt man im Finale am
# Computer aus dem Gedaechtnis ein - Reihenfolge und Schreibweise
# stehen nur hier.
WORLD_OBJECTS = {1: "Träne", 2: "Schuhe", 3: "Lampe",
                 4: "Glas", 5: "Batterien", 6: "Herz"}

# Wie nah man an ein Objekt heran muss, um es mit Leertaste aufzuheben.
# Gemessen wird vom FUSSPUNKT des Spielers zur MITTE des Objekts -
# nicht von der linken oberen Ecke des Sprites. Das war der Grund,
# warum das Objekt in Raum 1 unerreichbar in der Ecke lag.
BELOHNUNG_REICHWEITE = 150

# Ablageplaetze der beiden Objekte in Raum 1 (Mittelpunkt, nicht Ecke).
# Beide liegen frei auf den Kacheln, weit weg von Tuer, Tisch und Stuhl.
R1_OBJEKT_1 = (300, 700)        # Träne
R1_OBJEKT_2 = (460, 762)        # Schuhe

# Bildblatt der sechs Objekte: 3 Spalten, 2 Zeilen, in der Reihenfolge
# von WORLD_OBJECTS. Oben Träne, Schuhe, Lampe - unten Glas, Batterien,
# Herz. Die Aufhebe-Hitbox wird aus den Bildpunkten gerechnet, nicht
# aus der Zellgroesse: es zaehlt der Gegenstand, nicht die leere Ecke.
# Wo die Frau im Zimmer liegt, wenn man sich in Welt 6 fuer "Jaein"
# oder "Nein" entschieden hat. Mittelpunkt auf dem Boden.
R1_FRAU_POS = (330, 770)
R1_FRAU_BREITE = 128            # Breite des liegenden Sprites im Spiel
R1_FRAU_REICHWEITE = 150        # so nah muss man heran, um sie anzusprechen

OBJEKT_BLATT = "gegenstaende.png"
OBJEKT_SPALTEN = 3
OBJEKT_ZEILEN = 2
OBJEKT_GROESSE = 64             # Kantenlaenge im Spiel

# ---------------------------------------------------------------
# Welt 3: Erdreich – Kampf gegen die Uhr
# ---------------------------------------------------------------
# Der Ablauf besteht aus Phasen. Jede Phase hat zwei Teile:
#
#   1. Sammeln: W3_PHASEN[i][1] schwarze Punkte, die IMMER im Blickfeld
#      erscheinen - der erste am Bildrand, dann Schritt fuer Schritt naeher.
#   2. Hetze:   die Meldung "Nach oben!" (bzw. unten/rechts/links). Der
#      naechste Punkt liegt W3_SPRINT_DISTANZ weit in dieser Richtung im
#      Dunkeln. Wer ihn nicht in W3_SPRINT_ZEIT Sekunden erreicht, ist raus.
#
#   3. Gegenpunkt: direkt nach der Hetze liegt der naechste Punkt NICHT im
#      Blickfeld, sondern in der genau entgegengesetzten Richtung. Wer eben
#      nach oben gehetzt ist, muss sofort wieder nach unten. Danach geht es
#      normal weiter. Der Gegenpunkt hat keine eigene Uhr - er kostet nur
#      Zeit auf der Gesamtuhr.
#
# Vier Phasen zu je 7 Sammelpunkten + Hetzpunkt + Gegenpunkt = 36 Punkte.
W3_PHASEN = [
    ("oben",   7),
    ("unten",  7),
    ("rechts", 7),
    ("links",  7),
]

W3_ABSTAND_MAX = 440       # erster Sammelpunkt: am Rand, gerade noch im Bild
W3_ABSTAND_MIN = 110       # letzter Sammelpunkt: direkt vor der Nase
W3_TREFFER_RADIUS = 52     # so nah muss man an einen Punkt heran

# Auch im Erdreich stehen Felsen um die Punkte. Der Ring ist weiter und
# offener als im Wald - hier laeuft die Uhr, und ein zugestellter Punkt
# waere kein Hindernis, sondern ein Todesurteil. Um Hetz- und
# Gegenpunkte wird gar kein Ring gebaut.
W3_NEST_RADIUS = 250
W3_NEST_STUECKE = 9
W3_NEST_LUECKE = 1.00      # halbe Breite der Luecke im Bogenmass
W3_PUNKT_FREI = 170        # dieser Kreis um den Punkt wird leergeraeumt
W3_VERS_DAUER = 7.0        # so lange steht der Rilke-Wegweiser im Bild

# Nach jedem durchquerten Punkt wird rund um den Spieler ein Kreis
# leergeraeumt - doppelte Spielerbreite. Sonst kann ein Fels genau dort
# erscheinen, wo man gerade steht, und man sitzt fest.
W3_FREIRAUM = 128          # = 2 x R1_HITBOX-Breite (64), siehe weiter unten

W3_SPRINT_ZEIT = 4.0       # Sekunden fuer die Hetze
W3_SPRINT_DISTANZ = 1150   # so weit weg liegt der Hetzpunkt
# Die Rechnung dahinter (gehen 240 px/s, sprinten 480 px/s):
#   sprinten  1150 / 480 = 2,4 s  -> bleiben 1,6 s zum Reagieren
#   gehen     1150 / 240 = 4,8 s  -> reicht nicht, man MUSS sprinten
# Vier Sekunden sind knapp bemessen. Ist es beim Spielen zu hart, senke
# W3_SPRINT_DISTANZ (jede 100 px sind 0,2 s mehr Luft) oder erhoehe
# W3_SPRINT_ZEIT. Wichtig bleibt nur: Gehen darf nie reichen, also
# W3_SPRINT_DISTANZ immer ueber 240 * W3_SPRINT_ZEIT halten.
# Beim Startruf wird die Ausdauer aufgefuellt, damit die Hetze an der
# Reaktion haengt und nicht daran, ob man kurz vorher gesprintet ist.

W3_ZEIT = 180.0            # Gesamtuhr am Handgelenk (3 Minuten)

W3_RICHTUNGEN = {
    "oben":   ((0, -1), "Nach oben!"),
    "unten":  ((0, 1),  "Nach unten!"),
    "rechts": ((1, 0),  "Nach rechts!"),
    "links":  ((-1, 0), "Nach links!"),
}

W3_GEGEN_DISTANZ = 800     # Gegenpunkt: weiter als die halbe Bildbreite (512),
                           # damit er garantiert ausserhalb des Blickfelds liegt

# Sammelpunkte + je ein Hetz- und ein Gegenpunkt pro Phase
W3_PUNKTE_GESAMT = sum(n for _, n in W3_PHASEN) + 2 * len(W3_PHASEN)

# Welt 4: Labyrinth – Wettlauf gegen die Frau
# Am 09.09. verlaengert: das Labyrinth war in gut fuenf Minuten durch.
# Groesser UND dunkler - mit der Lampe sieht man nur einen Ausschnitt,
# also braucht das Suchen laenger. Zeit im gleichen Verhaeltnis erhoeht
# wie die Breite (23 -> 31 Zellen), plus Zuschlag fuer die Dunkelheit.
W4_ZEIT = 480.0
W4_ZETTEL_MIN = 5
W4_WOERTER = ["Ich", "Du", "Er", "Sie", "Es", "Wir", "Ihr", "Sie"]

W4_ZELLE = 200            # Kantenlaenge einer Labyrinth-Zelle
W4_WAND = 40              # Wandstaerke -> Gassenbreite = W4_ZELLE - W4_WAND = 160
W4_SPALTEN = 31           # Zellen in x-Richtung
W4_ZEILEN = 17            # Zellen in y-Richtung
W4_SCHLEIFEN = 30         # zusaetzliche Durchbrueche -> Alternativrouten
W4_START_ZEILE = W4_ZEILEN // 2

# Ursprung so, dass die Mitte der Startzelle bei (32, 32) liegt
W4_OX = 32 - W4_ZELLE // 2
W4_OY = 32 - W4_ZELLE // 2 - W4_START_ZEILE * W4_ZELLE

W4_FRAU_TEMPO = 240.0     # Pixel pro Sekunde (Spieler geht ca. 480, Sprint 960)
W4_FRAU_VORSPRUNG = 3     # Zellen Vorsprung beim Start

# Sie passt sich an: sprintet der Spieler, zieht sie mit. Der Faktor gilt
# nur solange gesprintet wird, und sie gleicht ihr Tempo weich an, damit es
# nicht nach einem Schalter aussieht.
#
# Warum 1,4 und nicht mehr: die Ausdauer laesst nur etwa 36 % Sprintanteil zu
# (3,8 s sprinten, dann 6,7 s auffuellen). Im Schnitt laeuft der Spieler damit
# rund 326 px/s, die Frau bei Faktor 1,4 rund 275 px/s. Das sind knapp 19 %
# Vorsprung - und den braucht er fuer die Umwege zu den Zetteln. Bei 1,7 waeren
# es nur noch 8 %, dann ist das Rennen kaum zu gewinnen.
W4_FRAU_SPRINT_FAKTOR = 1.4   # so viel schneller, wenn der Spieler sprintet
W4_FRAU_ANPASSUNG = 2.5       # wie schnell sie umschaltet (hoeher = haerter)
W4_FRAU_VERZOEGERUNG = 5.0  # Sekunden, bis sie losgeht
W4_ZIEL_RADIUS = 90       # so nah muss man an die Tuer

# Rund um die Tuer werden die Waende weggeraeumt, damit sie immer
# erreichbar ist - egal wie das Labyrinth gewuerfelt wurde.
# Wert in Pixeln, gemessen von der Zellmitte nach allen Seiten.
W4_TUER_FREIRAUM = 260

# ---------------------------------------------------------------
# Welt 4: Dunkelheit und Taschenlampe
# ---------------------------------------------------------------
# Im Tunnel ist es finster. Ohne Lampe sieht man nur den Boden vor den
# eigenen Fuessen, mit Lampe einen Kegel. Umschalten mit T - und nur
# hier, in keiner anderen Welt.
W4_DUNKEL = True
W4_LICHT_AUS = 150         # Sichtradius ohne Lampe
W4_LICHT_AN = 400          # Sichtradius mit Lampe
W4_LICHT_WEICH = 0.42      # bis hierhin voll hell, danach weicher Rand
W4_LICHT_FLACKERN = 16     # Staerke des Flackerns (0 = ruhiges Licht)
W4_LICHT_FARBE = (54, 40, 16)   # warmer Schimmer im Kegel
W4_LAMPE_START_AN = False  # brennt die Lampe beim Betreten schon?

# ---------------------------------------------------------------
# Welt 5: Lava – 5 Türen nach Koordinaten des Zukunfts-Ichs
# ---------------------------------------------------------------
W5_TUEREN_ZIEL = 5

# Alle paar Sekunden zieht ein Geist quer durchs Bild. Wer sich
# erwischen laesst, hat die Welt verloren. Sie kommen immer von
# ausserhalb des Blickfelds und fliegen geradlinig hindurch, damit man
# sie kommen sieht und ausweichen kann.
W5_GEIST_INTERVALL = (2.6, 4.4)   # Sekunden zwischen zwei Geistern
W5_GEIST_TEMPO = (210.0, 340.0)   # Pixel pro Sekunde
W5_GEIST_GROESSE = (150, 240)     # Durchmesser des Schemens
W5_GEIST_TREFFER = 46             # so nah darf er an den Spieler
W5_GEIST_MAX = 5                  # mehr als so viele nie gleichzeitig
W5_GEIST_FARBE = (176, 214, 238)  # blasses Blau

# Welt 6: Ewigkeit – nach 10 Minuten Rilke-Regen ist Schluss
W6_EWIGKEIT = 600.0

DEAD_END_DAUER = 10.0  # 10 Sekunden nach dem Dead End erscheint der Highscore

# Aufblende beim Spielstart: schwarz -> hell
INTRO_FADE_DAUER = 5.0

# Raum 1: Abstand des Spielers zur Tuer beim Erscheinen
R1_SCHRITT_PX = 64     # was ein "Schritt" optisch bedeutet
R1_ABSTAND_SCHRITTE = 3

# ---------------------------------------------------------------
# Raum 1: begehbare Bodenflaeche
# ---------------------------------------------------------------
# Der Raum ist perspektivisch gezeichnet: der Kachelboden ist ein Trapez,
# hinten an der Rueckwand schmal, vorne zum Betrachter hin breit.
# Diese sechs Werte beschreiben ihn. Im Spiel mit F1 einblenden und
# nachjustieren, bis die Linie genau auf der Kachelkante liegt.
# Am 09.09. am neuen images/background.png nachgemessen. Der Raum ist
# tiefer geworden: der Kachelboden laeuft jetzt bis fast an den unteren
# Bildrand und wird dabei fast bildbreit. Die Kanten sind an den hellen
# Randlinien abgelesen (y=580: 294..736, y=800: 84..948) und daraus
# linear auf Vorder- und Hinterkante gerechnet.
R1_BODEN_HINTEN_Y = 548        # Hoehe der hinteren Bodenkante (Fuss der Rueckwand)
R1_BODEN_HINTEN_LINKS = 324
R1_BODEN_HINTEN_RECHTS = 705

# Die Fluchtlinien laufen unten aus dem Bild heraus. Deshalb ist die
# vordere Kante bis fast an den Bildrand gezogen und die rechnerischen
# Randwerte liegen ausserhalb - begrenzt wird zusaetzlich durch
# R1_BODEN_RAND, damit der Spieler nicht halb aus dem Bild laeuft.
R1_BODEN_VORNE_Y = 1004        # Hoehe der vorderen Bodenkante
R1_BODEN_VORNE_LINKS = -111
R1_BODEN_VORNE_RECHTS = 1145
R1_BODEN_RAND = 24             # Sicherheitsabstand zum Bildrand

# ---------------------------------------------------------------
# Raum 1: die erste Tuer
# ---------------------------------------------------------------
# Die Tuer steht an der Rueckwand. Ihre Unterkante liegt genau auf der
# Fluchtlinie des Raums - alles, was tiefer laege, wird beim Zeichnen
# abgeschnitten. Damit sitzt sie im Raum statt darueber zu schweben.
R1_TUER_UNTEN = R1_BODEN_HINTEN_Y   # Unterkante = hintere Bodenkante
R1_TUER_VERSATZ_X = 0               # + verschiebt nach rechts
# 256 = volle Zellhoehe des Sprites. Der Wert war auf 250 gesetzt, solange
# Tür.png fehlerhaft war; mit dem neu geschnittenen Sprite sitzt die Tuer
# unten buendig in der Zelle und darf voll gezeichnet werden.
R1_TUER_MAX_HOEHE = 256             # so hoch darf die Tuer hoechstens sein

# Tuerblatt images/Tür.png: 4 Spalten, 2 Zeilen. Zelle (0,0) ist die
# geschlossene, (1,0) die offene Tuer. Die Zellgroesse liest main.py aus
# dem Bild; durchsichtige Raender werden automatisch abgeschnitten, damit
# die Unterkante des Sprites auch die Unterkante der Tuer ist.
TUER_SKALIERUNG = 1.0               # 1.0 = Originalgroesse

# Kollisionsbox des Spielers innerhalb des 128x128-Sprites: (dx, dy, breite, hoehe)
# Nur der Fussbereich zaehlt - in der Perspektive stehen die Fuesse auf dem Boden,
# der Kopf darf optisch vor der Wand liegen.
R1_HITBOX = (32, 76, 64, 44)

# ---------------------------------------------------------------
# Raum 1: Computertisch, Sitzplatz und Stuhl
# ---------------------------------------------------------------
# Von hinten nach vorne stehen die drei Bereiche untereinander:
#
#     R1_STUHL      Fussabdruck des Buerostuhls
#     R1_SITZ       genau eine Spielerhitbox hoch - hier steht man
#     R1_COMPUTER   Fussabdruck des Computertisches
#
# Stuhl und Tisch sind Hindernisse, dazwischen bleibt eine Luecke. Man
# kommt also nur von links oder rechts hinein. Steht der Spieler darin,
# wird der Tisch NACH ihm gezeichnet und verdeckt seine untere Haelfte.
#
# Alles haengt an vier Zahlen. Im Spiel mit F1 pruefen und nachziehen.
# Am 09.09. nach links gerueckt und nach vorne gesetzt: rechts neben
# Tisch und Stuhl bleibt jetzt ein begehbarer Gang zur Wand (rund 140
# bzw. 180 px, der Spieler braucht 64), und hinter dem Stuhl ebenfalls.
R1_MOEBEL_MITTE_X = 620         # gemeinsame Mittelachse der drei Bereiche
R1_TISCH_BREITE = 210           # Breite, auf die das Tischbild skaliert wird
R1_TISCH_FUSS_Y = 850           # Vorderkante des Tisches auf dem Boden
R1_TISCH_TIEFE = 90             # Tiefe des Fussabdrucks

R1_COMPUTER = (R1_MOEBEL_MITTE_X - R1_TISCH_BREITE // 2,
               R1_TISCH_FUSS_Y - R1_TISCH_TIEFE,
               R1_TISCH_BREITE, R1_TISCH_TIEFE)

# Der Sitzplatz ist genau eine Spielerhitbox tief. R1_SITZ_LUFT gibt ein
# paar Pixel Spielraum dazu - sonst muesste man pixelgenau treffen, und
# bei 8 px pro Schritt trifft man nie. Auf 0 setzen, wenn es exakt eine
# Hitbox sein soll.
R1_SITZ_LUFT = 20
R1_SITZ_TIEFE = R1_HITBOX[3] + R1_SITZ_LUFT
R1_SITZ_BREITE = R1_HITBOX[2] + 48
R1_SITZ = (R1_MOEBEL_MITTE_X - R1_SITZ_BREITE // 2,
           R1_COMPUTER[1] - R1_SITZ_TIEFE,
           R1_SITZ_BREITE, R1_SITZ_TIEFE)

R1_STUHL_BREITE = 90            # Breite, auf die das Stuhlbild skaliert wird
R1_STUHL_TIEFE = 44             # Tiefe des Fussabdrucks (Rollenkreuz)
R1_STUHL = (R1_MOEBEL_MITTE_X - R1_STUHL_BREITE // 2,
            R1_SITZ[1] - R1_STUHL_TIEFE,
            R1_STUHL_BREITE, R1_STUHL_TIEFE)

# Wie nah man dran sein muss, damit sich das Menue oeffnet
R1_COMPUTER_REICHWEITE = 45

# Hindernisse auf dem Boden als (x, y, breite, hoehe)
R1_HINDERNISSE = [
    R1_COMPUTER,
    R1_STUHL,
]

# ---------------------------------------------------------------
# Ausdauer: Sprinten kostet Kraft
# ---------------------------------------------------------------
AUSDAUER_MAX = 100.0
AUSDAUER_VERBRAUCH = 26.0   # Verbrauch pro Sekunde Sprint
AUSDAUER_REGEN = 15.0       # Erholung pro Sekunde (gehen oder stehen)
AUSDAUER_SPERRE = 20.0      # leer gesprintet? Erst ab diesem Wert wieder Sprint

# Welt 4: jedes aufgesammelte Wort laesst die Frau kurz innehalten
W4_ZETTEL_STOPP = 2.5       # Sekunden Stillstand pro Zettel

# ---------------------------------------------------------------
# Finale am Computer: Objekte aus dem Gedaechtnis eintippen
# ---------------------------------------------------------------
FINALE_VERSUCHE = 3        # so viele Fehlversuche sind insgesamt erlaubt


# ######################################################################
# texte.py
# ######################################################################
"""Alle Spieltexte: Untersuchen-Texte und die Rilke-Gedichte.

Inhalt aendern ist hier gefahrlos - die Logik in main.py greift nur
auf die Listen zu.
"""

# ---------------------------------------------------------------
# Untersuchen-System: Texte
# ---------------------------------------------------------------
FLAVOR_TEXTS = [
    "Ein Stück Boden. Es schweigt beharrlich.",
    "Hier liegt Staub. Sehr alter Staub.",
    "Du entdeckst einen Kratzer im Boden. Wer war das?",
    "Nichts Besonderes. Oder doch? ... Nein, nichts Besonderes.",
    "Eine kalte Stelle. Du fröstelst kurz.",
    "Der Boden knarzt hier verdächtig.",
    "Du findest eine verlorene Schraube. Wozu gehörte sie wohl?",
    "Ein Fleck. Du willst lieber nicht wissen, wovon.",
    "Hier hat jemand etwas in den Boden geritzt: 'WARUM?'",
    "Feiner Sand. Woher kommt hier Sand?",
    "Du hörst ein leises Summen unter dem Boden.",
    "Eine Stelle, die wärmer ist als der Rest. Seltsam.",
    "Spinnweben. Die Spinne ist ausgezogen.",
    "Du siehst deinen eigenen Schatten an. Er sieht zurück.",
    "Ein winziges Loch im Boden. Zu klein für Antworten.",
    "Hier riecht es nach altem Papier.",
]

STONE_FLAVOR_TEXTS = [
    "Ein Stein. Er war schon vor dir hier und wird nach dir hier sein.",
    "Kalter Fels. Er antwortet nicht.",
    "Ein Riss im Stein. Wie eine Frage.",
    "Moos. Das einzige, was hier lebt. Vielleicht.",
    "Der Stein ist glatt. Jemand hat oft darüber gestrichen.",
    "Du klopfst auf den Fels. Er klingt hohl. Oder du bildest es dir ein.",
    "Kieselsteine. Sie ordnen sich zu keinem Muster.",
    "Ein Stein, der aussieht wie ein Gesicht. Er schaut weg.",
]

# Texte für die drei "Hängengeblieben"-Zustände:
# Wer die Regeln verlässt, bekommt keine Erklärung. Nur das hier.
ROOM1_DEAD_TEXTS = [
    "Stille.",
    "Der Boden ist noch da. Sonst nichts.",
    "Du hast aufgehört. Warum bist du noch hier?",
    "Niemand ruft mehr.",
    "Die Ritzung im Boden ist verschwunden.",
    "Es gibt nichts zu untersuchen. Es gab nie etwas.",
    "Dein Schatten bewegt sich eine Spur zu spät.",
    "Du erinnerst dich an eine Stimme. Oder?",
]

LIMBO_TEXTS = [
    "Nichts.",
    "Hier lag einmal etwas. Jetzt nicht mehr.",
    "Der Boden erinnert sich nicht an dich.",
    "Du hörst deinen eigenen Schritt. Sonst nichts.",
    "Es gibt keine Aufgabe mehr.",
    "Warum bist du noch hier?",
    "Gras, das sich nicht im Wind bewegt. Es gibt keinen Wind.",
    "Weit und breit dieselbe Antwort: keine.",
]

FROZEN_TEXTS = [
    "Der Stein ist noch kälter geworden.",
    "Kein Ticken. Nirgends.",
    "Staub, der einmal Papier war.",
    "Die Zeit ist nicht um. Sie ist weg.",
    "Du wirfst einen Kiesel. Er fällt. Sonst passiert nichts. Nie wieder.",
    "Irgendwo hier lagen Wörter. Du weißt nicht mehr, welche.",
    "Dein Handgelenk fühlt sich leicht an. Zu leicht.",
]

# ---------------------------------------------------------------
# Welt 2: Rilke-Gedichte (Überschrift - Leerzeile - Versform)
# ---------------------------------------------------------------
RILKE_GEDICHTE = [
    "Herbsttag\n\n"
    "Herr: es ist Zeit. Der Sommer war sehr groß.\n"
    "Leg deinen Schatten auf die Sonnenuhren,\n"
    "und auf den Fluren lass die Winde los.",

    "Der Panther\n\n"
    "Sein Blick ist vom Vorübergehn der Stäbe\n"
    "so müd geworden, dass er nichts mehr hält.\n"
    "Ihm ist, als ob es tausend Stäbe gäbe\n"
    "und hinter tausend Stäben keine Welt.",

    "Herbst\n\n"
    "Die Blätter fallen, fallen wie von weit,\n"
    "als welkten in den Himmeln ferne Gärten;\n"
    "sie fallen mit verneinender Gebärde.",

    "Herbst\n\n"
    "Und doch ist Einer, welcher dieses Fallen\n"
    "unendlich sanft in seinen Händen hält.",

    "Das Stunden-Buch\n\n"
    "Ich lebe mein Leben in wachsenden Ringen,\n"
    "die sich über die Dinge ziehn.\n"
    "Ich werde den letzten vielleicht nicht vollbringen,\n"
    "aber versuchen will ich ihn.",

    "Du musst das Leben nicht verstehen\n\n"
    "Du musst das Leben nicht verstehen,\n"
    "dann wird es werden wie ein Fest.",

    "Herbsttag\n\n"
    "Wer jetzt kein Haus hat, baut sich keines mehr.\n"
    "Wer jetzt allein ist, wird es lange bleiben.",

    "Abend\n\n"
    "Der Abend wechselt langsam die Gewänder,\n"
    "die ihm ein Rand von alten Bäumen hält.",

    "Das Stunden-Buch\n\n"
    "Lösch mir die Augen aus: ich kann dich sehn,\n"
    "wirf mir die Ohren zu: ich kann dich hören.",

    "Der Schwan\n\n"
    "Diese Mühsal, durch noch Ungetanes\n"
    "schwer und wie gebunden hinzugehn,\n"
    "gleicht dem ungeschaffnen Gang des Schwanes.",
]


# ######################################################################
# verse.py
# ######################################################################
"""Verse fuer das Erdreich.

Im Erdreich liegt der naechste Punkt nach einer Hetze ausserhalb des
Bildes. Damit man weiss, wohin man laufen muss, sagt die Welt es nicht
als Befehl, sondern als Vers - im Ton von Rilke, aber selbst geschrieben.

Jeder Vers nennt die Richtung deutlich genug, dass man ihn als Wegweiser
lesen kann, ohne dass es klingt wie ein Schild.

Benutzt wird das so:

    from verse import w3_vers, GEGENRICHTUNG
    text = w3_vers("oben")                  # Vers nach oben
    text = w3_vers(GEGENRICHTUNG["oben"])   # Vers fuer den Gegenpunkt
"""

# Der Gegenpunkt liegt immer genau andersherum als die Hetze davor.
GEGENRICHTUNG = {"oben": "unten", "unten": "oben",
                 "rechts": "links", "links": "rechts"}

W3_VERSE = {
    "oben": [
        "Geh, wo der Himmel sich\nüber dem Staub schließt.\nWas oben liegt,\nhat immer auf dich gewartet.",
        "Über dir, wo nichts mehr wächst,\nsteht das Dunkle still.\nSteig hinauf. Es hält.",
        "Was dich ruft, liegt höher,\nals dein Atem reicht.\nNach oben, sagt der Stein.",
        "Der Weg nach oben ist der kürzeste,\nden keiner gerne nimmt.",
    ],
    "unten": [
        "Unter dir liegt, was du vergisst.\nGeh hinab. Es zählt mit.",
        "Nach unten. Dorthin,\nwo das Gewicht sich sammelt\nund nicht fragt.",
        "Was du suchst, sinkt.\nFolge ihm nach unten,\nbevor der Grund sich schließt.",
        "Der Grund ist tiefer als der Weg.\nNach unten, sagt die Zeit.",
    ],
    "rechts": [
        "Zur Rechten wartet, was dir fremd ist.\nGeh, eh es sich abwendet.",
        "Nach rechts: dort öffnet sich\ndie Hand, die du nicht kennst.",
        "Rechts von dir bricht das Licht\nan einer Kante auf.\nLauf dorthin.",
        "Was rechts liegt, hat keinen Namen.\nGib ihm einen, indem du kommst.",
    ],
    "links": [
        "Zur Linken liegt die Stelle,\nan der du nie gestanden hast.",
        "Nach links, sagt der Wind,\nund schweigt dann wieder.",
        "Links ist die Seite, die dich sieht.\nWende dich.",
        "Was links auf dich wartet,\nwartet nicht lange.",
    ],
}


def w3_vers(richtung, nummer=None):
    """Vers fuer eine Richtung. Ohne nummer wird einer gewuerfelt."""
    verse = W3_VERSE.get(richtung)
    if not verse:
        return ""
    if nummer is None:
        return random.choice(verse)
    return verse[nummer % len(verse)]


# ######################################################################
# labyrinth.py
# ######################################################################
"""Welt 4: Labyrinth-Erzeugung (Recursive Backtracker) und Wegsuche."""



# ---------------------------------------------------------------
# Welt 4: Labyrinth erzeugen (Recursive Backtracker) + Weg suchen
# ---------------------------------------------------------------
def w4_zell_mitte(cx, cy):
    """Weltkoordinate der Zellenmitte."""
    return [W4_OX + cx * W4_ZELLE + W4_ZELLE // 2,
            W4_OY + cy * W4_ZELLE + W4_ZELLE // 2]


def w4_erzeuge_labyrinth():
    """Recursive Backtracker. Gibt (verbunden, sackgassen) zurueck.
    verbunden = Menge von frozenset({zelle_a, zelle_b}) fuer offene Durchgaenge."""
    start = (0, W4_START_ZEILE)
    verbunden = set()
    besucht = {start}
    stack = [start]
    while stack:
        cx, cy = stack[-1]
        frei = [(cx + dx, cy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= cx + dx < W4_SPALTEN and 0 <= cy + dy < W4_ZEILEN
                and (cx + dx, cy + dy) not in besucht]
        if not frei:
            stack.pop()
            continue
        nxt = random.choice(frei)
        verbunden.add(frozenset(((cx, cy), nxt)))
        besucht.add(nxt)
        stack.append(nxt)

    # Ein paar zusaetzliche Durchbrueche: erzeugt Schleifen und Alternativwege
    versuche = 0
    gesetzt = 0
    while gesetzt < W4_SCHLEIFEN and versuche < 400:
        versuche += 1
        cx = random.randrange(W4_SPALTEN)
        cy = random.randrange(W4_ZEILEN)
        dx, dy = random.choice(((1, 0), (0, 1)))
        nx, ny = cx + dx, cy + dy
        if not (0 <= nx < W4_SPALTEN and 0 <= ny < W4_ZEILEN):
            continue
        paar = frozenset(((cx, cy), (nx, ny)))
        if paar in verbunden:
            continue
        verbunden.add(paar)
        gesetzt += 1

    # Sackgassen einsammeln (genau ein offener Nachbar) - dort liegen die Zettel
    sackgassen = []
    for cx in range(W4_SPALTEN):
        for cy in range(W4_ZEILEN):
            offen = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if frozenset(((cx, cy), (cx + dx, cy + dy))) in verbunden)
            if offen == 1:
                sackgassen.append((cx, cy))
    return verbunden, sackgassen


def w4_wand_rects(verbunden):
    """Baut aus den offenen Verbindungen die Wand-Rechtecke."""
    waende = []
    halb = W4_WAND // 2
    breite_gesamt = W4_SPALTEN * W4_ZELLE
    hoehe_gesamt = W4_ZEILEN * W4_ZELLE

    # Aussenwaende
    waende.append(pygame.Rect(W4_OX - halb, W4_OY - halb,
                              breite_gesamt + W4_WAND, W4_WAND))
    waende.append(pygame.Rect(W4_OX - halb, W4_OY + hoehe_gesamt - halb,
                              breite_gesamt + W4_WAND, W4_WAND))
    waende.append(pygame.Rect(W4_OX - halb, W4_OY - halb,
                              W4_WAND, hoehe_gesamt + W4_WAND))
    waende.append(pygame.Rect(W4_OX + breite_gesamt - halb, W4_OY - halb,
                              W4_WAND, hoehe_gesamt + W4_WAND))

    # Innenwaende: ueberall dort, wo keine Verbindung besteht
    for cx in range(W4_SPALTEN):
        for cy in range(W4_ZEILEN):
            if cx + 1 < W4_SPALTEN and frozenset(((cx, cy), (cx + 1, cy))) not in verbunden:
                waende.append(pygame.Rect(W4_OX + (cx + 1) * W4_ZELLE - halb,
                                          W4_OY + cy * W4_ZELLE - halb,
                                          W4_WAND, W4_ZELLE + W4_WAND))
            if cy + 1 < W4_ZEILEN and frozenset(((cx, cy), (cx, cy + 1))) not in verbunden:
                waende.append(pygame.Rect(W4_OX + cx * W4_ZELLE - halb,
                                          W4_OY + (cy + 1) * W4_ZELLE - halb,
                                          W4_ZELLE + W4_WAND, W4_WAND))
    return waende


def w4_kuerzester_weg(verbunden, start, ziel):
    """Breitensuche durchs Labyrinth. Gibt die Zellfolge zurueck."""
    vorgaenger = {start: None}
    queue = [start]
    kopf = 0
    while kopf < len(queue):
        akt = queue[kopf]
        kopf += 1
        if akt == ziel:
            break
        cx, cy = akt
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (cx + dx, cy + dy)
            if nb in vorgaenger:
                continue
            if frozenset((akt, nb)) not in verbunden:
                continue
            vorgaenger[nb] = akt
            queue.append(nb)
    if ziel not in vorgaenger:
        return [start]
    weg = []
    akt = ziel
    while akt is not None:
        weg.append(akt)
        akt = vorgaenger[akt]
    weg.reverse()
    return weg


# ######################################################################
# raum1.py
# ######################################################################
"""Raum 1: die perspektivische Bodenflaeche und ihre Kollision.

Der Kachelboden ist ein Trapez (hinten schmal, vorne breit); die
Eckwerte stehen in konfig.py und lassen sich im Spiel mit F1 pruefen.
"""


def r1_boden_grenzen(y):
    """Linke und rechte Bodenkante auf Hoehe y (lineare Perspektive)."""
    spanne = R1_BODEN_VORNE_Y - R1_BODEN_HINTEN_Y
    t = 0.0 if spanne <= 0 else (y - R1_BODEN_HINTEN_Y) / spanne
    t = max(0.0, min(1.0, t))
    links = R1_BODEN_HINTEN_LINKS + t * (R1_BODEN_VORNE_LINKS - R1_BODEN_HINTEN_LINKS)
    rechts = R1_BODEN_HINTEN_RECHTS + t * (R1_BODEN_VORNE_RECHTS - R1_BODEN_HINTEN_RECHTS)
    # Weiter unten laufen die Fluchtlinien aus dem Bild. Dort begrenzt
    # der Bildrand, nicht mehr die Perspektive.
    return max(R1_BODEN_RAND, links), min(WIDTH - R1_BODEN_RAND, rechts)


def r1_hitbox(pos):
    """Kollisionsbox des Spielers an Position pos (Fussbereich)."""
    return pygame.Rect(pos[0] + R1_HITBOX[0], pos[1] + R1_HITBOX[1],
                       R1_HITBOX[2], R1_HITBOX[3])


def r1_blockiert(pos):
    """True, wenn der Spieler dort nicht stehen kann."""
    hb = r1_hitbox(pos)
    fuss_y = hb.bottom          # die Fuesse bestimmen die Tiefe im Raum

    if fuss_y < R1_BODEN_HINTEN_Y or fuss_y > R1_BODEN_VORNE_Y:
        return True

    links, rechts = r1_boden_grenzen(fuss_y)
    if hb.left < links or hb.right > rechts:
        return True

    for h in R1_HINDERNISSE:
        if hb.colliderect(pygame.Rect(*h)):
            return True
    return False


def r1_boden_polygon(schritte=16):
    """Umriss der Bodenflaeche - fuer die F1-Anzeige und den Lichtschein.

    Wird abgetastet statt aus vier Ecken gebaut, weil die Flaeche unten
    am Bildrand abgeschnitten wird und dadurch mehr als vier Ecken hat."""
    spanne = R1_BODEN_VORNE_Y - R1_BODEN_HINTEN_Y
    hoehen = [R1_BODEN_HINTEN_Y + spanne * i / schritte
              for i in range(schritte + 1)]
    rechte = [(r1_boden_grenzen(y)[1], y) for y in hoehen]
    linke = [(r1_boden_grenzen(y)[0], y) for y in reversed(hoehen)]
    return rechte + linke


# ######################################################################
# raum1_moebel.py
# ######################################################################
"""Raum 1: Computertisch und Stuhl.

Von hinten nach vorne stehen im Zimmer untereinander:

    Stuhl          R1_STUHL      (Hitbox)
    Sitzplatz      R1_SITZ       genau eine Spielerhitbox hoch
    Computertisch  R1_COMPUTER   (Hitbox)

Der Spieler kommt nur von links oder rechts in den Sitzplatz hinein.
Steht er darin, wird der Tisch NACH ihm gezeichnet und verdeckt seine
untere Haelfte - er sitzt am Rechner. Ausserhalb greift dieselbe
Regel wie bei allen Dingen im Raum: was weiter vorne steht, wird
zuletzt gezeichnet.

Alle Masse stehen in konfig.py und lassen sich im Spiel mit F1
kontrollieren.
"""



# Feinheiten, die die Moebel im Raum verankern statt sie aufkleben
SCHATTEN_FARBE = (10, 4, 8)
SCHATTEN_TIEFE = 96             # Deckkraft des Kernschattens
SCHATTEN_HOEHE = 0.26           # Hoehe der Schattenellipse, Anteil der Breite
SCHEIN_FARBE = (13, 20, 31)     # kaltes Monitorlicht auf den Kacheln
SCHEIN_RUHE = 0.40              # Staerke, wenn niemand davorsitzt
SCHEIN_GROESSE = (330, 190)


def _weiche_ellipse(breite, hoehe, farbe, deckkraft, schaerfe=2.0):
    """Weich auslaufende Ellipse - fuer Schatten und Lichtschein.

    Wird einmal gebaut und danach nur noch geblittet."""
    flaeche = pygame.Surface((breite, hoehe), pygame.SRCALPHA)
    stufen = 22
    for i in range(stufen, 0, -1):
        t = i / stufen
        a = int(deckkraft * (1.0 - t) ** schaerfe)
        kasten = pygame.Rect(0, 0, max(2, int(breite * t)), max(2, int(hoehe * t)))
        kasten.center = (breite // 2, hoehe // 2)
        pygame.draw.ellipse(flaeche, farbe + (a,), kasten)
    return flaeche.convert_alpha()


def _auf_breite(bild, breite):
    """Bild auf eine Zielbreite bringen, Seitenverhaeltnis bleibt."""
    if bild.get_width() <= 0:
        return bild
    faktor = breite / bild.get_width()
    return pygame.transform.smoothscale(
        bild, (int(breite), max(1, int(bild.get_height() * faktor))))


class Moebel:
    """Tisch mit Rechner und Buerostuhl, samt Hitboxen und Sitzplatz."""

    def __init__(self, bildordner):
        self.ordner = bildordner
        self.tisch_rect = pygame.Rect(*R1_COMPUTER)
        self.stuhl_rect = pygame.Rect(*R1_STUHL)
        self.sitz_rect = pygame.Rect(*R1_SITZ)

        tisch = self._bild(("raum_computer.png", "Computer.png",
                            "computer.png", "pc.png"))
        if tisch is None:
            tisch = self._nottisch()
        stuhl = self._bild(("raum_stuhl.png", "Stuhl.png", "stuhl.png"))
        if stuhl is None:
            stuhl = self._notstuhl()

        self.tisch = _auf_breite(tisch, R1_TISCH_BREITE)
        self.stuhl = _auf_breite(stuhl, R1_STUHL_BREITE)

        # Fusspunkte: die Unterkante des Sprites steht auf der Unterkante
        # der jeweiligen Hitbox.
        self.tisch_pos = (self.tisch_rect.x,
                          R1_TISCH_FUSS_Y - self.tisch.get_height())
        self.stuhl_pos = (self.stuhl_rect.centerx - self.stuhl.get_width() // 2,
                          self.stuhl_rect.bottom - self.stuhl.get_height())

        # Schatten: ohne sie kleben die Moebel auf dem Boden statt darauf
        # zu stehen. Die Ellipse liegt auf der Unterkante der Hitbox.
        self.tisch_schatten = _weiche_ellipse(
            int(R1_TISCH_BREITE * 1.18),
            int(R1_TISCH_BREITE * 1.18 * SCHATTEN_HOEHE),
            SCHATTEN_FARBE, SCHATTEN_TIEFE)
        self.stuhl_schatten = _weiche_ellipse(
            int(R1_STUHL_BREITE * 1.30),
            int(R1_STUHL_BREITE * 1.30 * SCHATTEN_HOEHE),
            SCHATTEN_FARBE, SCHATTEN_TIEFE)

        # Der Bildschirm zeigt nach hinten oben, sein Licht faellt also
        # auf die Kacheln vor dem Tisch - genau dorthin, wo man sitzt.
        # Der Schein wird auf die Bodenflaeche beschnitten, sonst leuchtet
        # er neben dem Trapez auf der dunklen Wand weiter.
        self.schein = self._boden_schein()

    # ------------------------------------------------------------------
    def _bild(self, namen):
        for name in namen:
            pfad = os.path.join(self.ordner, name)
            if not os.path.exists(pfad):
                continue
            try:
                return pygame.image.load(pfad).convert_alpha()
            except pygame.error as fehler:
                print(f"{name} konnte nicht geladen werden: {fehler}")
        return None

    @staticmethod
    def _nottisch():
        """Ersatzbild: Tisch mit Monitor von hinten."""
        b, h = 240, 178
        s = pygame.Surface((b, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (86, 62, 46), (0, h - 52, b, 52))
        pygame.draw.rect(s, (56, 40, 30), (0, h - 52, b, 52), 3)
        pygame.draw.polygon(s, (76, 82, 92),
                            [(38, h - 52), (128, h - 52), (118, 26), (52, 26)])
        pygame.draw.polygon(s, (36, 40, 48),
                            [(38, h - 52), (128, h - 52), (118, 26), (52, 26)], 3)
        pygame.draw.rect(s, (66, 72, 82), (152, 34, 62, h - 86))
        pygame.draw.rect(s, (30, 34, 42), (152, 34, 62, h - 86), 3)
        return s

    @staticmethod
    def _notstuhl():
        b, h = 90, 159
        s = pygame.Surface((b, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (54, 52, 62), (18, 6, 54, 78), border_radius=10)
        pygame.draw.rect(s, (30, 28, 36), (18, 6, 54, 78), 3, border_radius=10)
        pygame.draw.rect(s, (54, 52, 62), (10, 84, 70, 22), border_radius=6)
        pygame.draw.rect(s, (30, 28, 36), (42, 106, 6, 30))
        for dx in (-34, -16, 0, 16, 34):
            pygame.draw.line(s, (30, 28, 36), (45, 136), (45 + dx, 152), 5)
        return s

    # ------------------------------------------------------------------
    # Abfragen
    # ------------------------------------------------------------------
    def sitzt(self, hitbox):
        """True, wenn der Spieler im Sitzplatz zwischen Stuhl und Tisch steht."""
        return self.sitz_rect.collidepoint(hitbox.center)

    def am_computer(self, hitbox, richtung):
        """True, wenn der Spieler den Rechner bedienen kann.

        Er muss nach unten schauen - man blickt von hinten auf die
        Geraete herab."""
        if richtung != "down":
            return False
        if self.sitzt(hitbox):
            return True
        dx = max(self.tisch_rect.left - hitbox.right,
                 hitbox.left - self.tisch_rect.right, 0)
        dy = max(self.tisch_rect.top - hitbox.bottom,
                 hitbox.top - self.tisch_rect.bottom, 0)
        return dx * dx + dy * dy < R1_COMPUTER_REICHWEITE ** 2

    # ------------------------------------------------------------------
    # Zeichnen
    # ------------------------------------------------------------------
    def _boden_schein(self):
        """Lichtfleck, auf das Bodentrapez zugeschnitten.

        Wird einmal gebaut; im Spiel bleibt ein einziger Blit."""
        flaeche = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fleck = _weiche_ellipse(SCHEIN_GROESSE[0], SCHEIN_GROESSE[1],
                                SCHEIN_FARBE, 255, schaerfe=3.2)
        flaeche.blit(fleck, (R1_MOEBEL_MITTE_X - SCHEIN_GROESSE[0] // 2,
                             self.tisch_rect.top - SCHEIN_GROESSE[1] // 2 - 6))
        maske = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(maske, (255, 255, 255, 255), r1_boden_polygon())
        flaeche.blit(maske, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return flaeche.convert_alpha()

    def boden_licht(self, screen, sitzt=False):
        """Monitorschein auf den Kacheln. Kommt vor alles andere."""
        self.schein.set_alpha(255 if sitzt else int(255 * SCHEIN_RUHE))
        screen.blit(self.schein, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def zeichne(self, screen, spieler_fuss, vorne):
        """Moebel zeichnen.

        vorne=False: was hinter dem Spieler steht (vor ihm zeichnen)
        vorne=True:  was vor ihm steht (nach ihm zeichnen)
        """
        for bild, pos, fuss, schatten, kasten in (
                (self.stuhl, self.stuhl_pos, self.stuhl_rect.bottom,
                 self.stuhl_schatten, self.stuhl_rect),
                (self.tisch, self.tisch_pos, R1_TISCH_FUSS_Y,
                 self.tisch_schatten, self.tisch_rect)):
            if (fuss > spieler_fuss) != vorne:
                continue
            screen.blit(schatten,
                        (kasten.centerx - schatten.get_width() // 2,
                         kasten.bottom - schatten.get_height() // 2 - 4))
            screen.blit(bild, pos)

    def zeichne_hilfslinien(self, flaeche):
        """F1-Anzeige: Sitzplatz und Sprite-Rahmen."""
        pygame.draw.rect(flaeche, (60, 220, 255, 90), self.sitz_rect)
        pygame.draw.rect(flaeche, (90, 240, 255, 230), self.sitz_rect, 2)
        for bild, pos in ((self.stuhl, self.stuhl_pos),
                          (self.tisch, self.tisch_pos)):
            pygame.draw.rect(flaeche, (255, 220, 90, 160),
                             pygame.Rect(pos[0], pos[1], bild.get_width(),
                                         bild.get_height()), 1)


# ######################################################################
# figuren.py
# ######################################################################
"""Die Frau: Sprites und Verhalten der Wegweiserin."""



def build_npc_placeholder():
    """Platzhalter-Skin: violette Gestalt, 4 Richtungen x 4 Frames.
    Wird automatisch durch images/npc.png ersetzt, sobald vorhanden
    (gleicher Sheet-Aufbau wie player.png: 4 Spalten, Zeilen = down/left/right/up)."""
    frames = {}
    base = (150, 90, 200)
    dark = (100, 55, 140)
    eye = (240, 240, 245)
    for direction in ("down", "left", "right", "up"):
        lst = []
        for f in range(4):
            surf = pygame.Surface((128, 128), pygame.SRCALPHA)
            bob = (0, 2, 0, -2)[f]
            foot = (0, 5, 0, -5)[f]
            pygame.draw.ellipse(surf, dark, (42 + foot, 106 + bob, 18, 12))
            pygame.draw.ellipse(surf, dark, (68 - foot, 106 + bob, 18, 12))
            pygame.draw.polygon(surf, base, [(64, 40 + bob), (34, 110 + bob), (94, 110 + bob)])
            pygame.draw.polygon(surf, dark, [(64, 40 + bob), (34, 110 + bob), (94, 110 + bob)], 3)
            pygame.draw.circle(surf, base, (64, 36 + bob), 22)
            pygame.draw.circle(surf, dark, (64, 36 + bob), 22, 3)
            if direction == "down":
                pygame.draw.circle(surf, eye, (56, 38 + bob), 4)
                pygame.draw.circle(surf, eye, (72, 38 + bob), 4)
            elif direction == "left":
                pygame.draw.circle(surf, eye, (50, 36 + bob), 4)
            elif direction == "right":
                pygame.draw.circle(surf, eye, (78, 36 + bob), 4)
            lst.append(surf)
        frames[direction] = lst
    return frames


def load_npc_sprites():
    """Laedt images/npc.png (Aufbau wie player.png); Fallback: Platzhalter."""
    for name in ("npc.png", "NPC.png"):
        path = os.path.join(image_dir, name)
        if os.path.exists(path):
            try:
                sheet = pygame.image.load(path).convert_alpha()
                s = (128, 128)
                return {
                    "down":  [sheet.subsurface(pygame.Rect(x * 128, 0, *s)) for x in range(4)],
                    "left":  [sheet.subsurface(pygame.Rect(x * 128, 128, *s)) for x in range(4)],
                    "right": [sheet.subsurface(pygame.Rect(x * 128, 256, *s)) for x in range(4)],
                    "up":    [sheet.subsurface(pygame.Rect(x * 128, 384, *s)) for x in range(4)],
                }
            except pygame.error as e:
                print(f"NPC-Bild konnte nicht geladen werden: {e}")
    return build_npc_placeholder()

class NPC:
    """Die Frau: erscheint alle ~15 Sekunden in der Naehe des Spielers
    und zeigt mit einem Pfeil, wohin es als Naechstes gehen soll."""

    def __init__(self, sprites, pos=None):
        self.sprites = sprites
        self.pos = list(pos) if pos else [400.0, -300.0]
        self.direction = "down"
        self.anim = 0.0
        self.signal_timer = NPC_SIGNAL_INTERVALL - 1.0  # kurz nach Weltstart zeigen
        self.arrow_timer = 0.0
        self.arrow_dir = (0.0, -1.0)

    @staticmethod
    def _face(dx, dy):
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        return "down" if dy > 0 else "up"

    def update_guide(self, dt, player_pos, target_pos):
        """Fuehrt den Spieler: alle NPC_SIGNAL_INTERVALL Sekunden erscheint
        sie zwischen Spieler und Ziel und zeigt die Richtung an."""
        self.signal_timer += dt
        self.arrow_timer = max(0.0, self.arrow_timer - dt)

        dx = target_pos[0] - player_pos[0]
        dy = target_pos[1] - player_pos[1]
        norm = max(1.0, (dx * dx + dy * dy) ** 0.5)
        nx, ny = dx / norm, dy / norm

        if self.signal_timer >= NPC_SIGNAL_INTERVALL:
            self.signal_timer = 0.0
            self.pos = [player_pos[0] + nx * 260 - 64,
                        player_pos[1] + ny * 260 - 64]
            self.arrow_timer = NPC_PFEIL_DAUER

        self.arrow_dir = (nx, ny)
        self.direction = self._face(dx, dy)
        self.anim = 0.0

    def draw(self, surface, camera):
        sprite = self.sprites[self.direction][int(self.anim)]
        sx = self.pos[0] - camera[0]
        sy = self.pos[1] - camera[1]
        if not (-140 < sx < WIDTH + 140 and -140 < sy < HEIGHT + 140):
            return
        surface.blit(sprite, (sx, sy))

        # Richtungspfeil ueber ihrem Kopf
        if self.arrow_timer > 0:
            cx, cy = sx + 64, sy - 18
            ax, ay = self.arrow_dir
            ex, ey = cx + ax * 44, cy + ay * 44
            px, py = -ay, ax  # senkrecht zur Pfeilrichtung
            col = (245, 235, 120)
            pygame.draw.line(surface, col, (cx, cy), (ex, ey), 6)
            pygame.draw.line(surface, col, (ex, ey),
                             (ex - ax * 16 + px * 10, ey - ay * 16 + py * 10), 6)
            pygame.draw.line(surface, col, (ex, ey),
                             (ex - ax * 16 - px * 10, ey - ay * 16 - py * 10), 6)

    def to_dict(self):
        return {"pos": self.pos}

    def from_dict(self, data):
        self.pos = list(data.get("pos", self.pos))


# ######################################################################
# landschaft.py
# ######################################################################
"""Landschaften der Aussenwelten: Waldreich, Erdreich, Labyrinth.

Alles, was in den unendlichen Welten auf dem Boden steht, wird hier
gewuerfelt und gezeichnet - Baeume, umgefallene Staemme, Felsen, Gras.
Dazu die Dunkelheit im Labyrinth samt Taschenlampe.

Wie es funktioniert
-------------------
Die Welten sind unendlich gross, also kann man die Landschaft nicht
vorher festlegen. Sie entsteht in Feldern von CHUNK Pixeln Kantenlaenge,
aus einem Zufallsgenerator, der mit den Feldkoordinaten gefuettert wird.
Dasselbe Feld liefert damit immer dieselbe Landschaft - egal wie oft man
hin und her laeuft. Nur sichtbare Felder werden gebaut und gemerkt.

Jedes Teil kennt seinen Fusspunkt. Was weiter hinten steht als der
Spieler, wird vor ihm gezeichnet, was weiter vorne steht, danach.

Hitboxen
--------
Baumstaemme bekommen eine Sperre aus Bildanteilen (nur der Stamm, nicht
die Krone). Felsen und Staemme bekommen sie aus den Bildpunkten: genommen
wird der Umriss des unteren Bildteils, also genau die Flaeche, mit der
das Ding auf dem Boden aufsitzt.

Bilder
------
Es werden ausschliesslich die Dateien aus BILDER benutzt. Fehlt eine,
gibt es ein magentafarbenes Rechteck und eine Meldung auf der Konsole -
kein handgemaltes Ersatzbild.
"""



# ---------------------------------------------------------------
# Stellschrauben
# ---------------------------------------------------------------
CHUNK = 640                 # Kantenlaenge eines Generierungsfeldes
FREI_UM_START = 420         # Radius um (0,0), der leer bleibt
CACHE_MAX = 600             # ab so vielen gemerkten Feldern wird geleert

# --- Welt 2: Waldreich -----------------------------------------
# Zwei Bestaende wechseln sich streifenweise ab. Weil im Bildsatz kein
# eigener Nadelbaum mehr liegt, unterscheiden sie sich ueber Farbton:
# heller, warmer Laubbestand gegen dunkleren, kuehleren Hochwald.
WALD_ZONE_BREITE = 2600     # wie breit ein Streifen ist
WALD_ZONE_NEIGUNG = 0.45    # 0 = senkrechte Streifen, 1 = 45 Grad
WALD_MISCHUNG = 0.16        # Anteil Baeume aus dem anderen Bestand

# Nur zwei Baumgroessen: mittel und gross. Dafuer stehen sie dicht.
WALD_BAUM_MITTEL = 250
WALD_BAUM_GROSS = 380
WALD_GROSS_ANTEIL = 0.42    # so viele der Baeume sind die grossen
WALD_BAEUME_PRO_FELD = (7, 11)
WALD_MINDESTABSTAND = 118   # Baeume duerfen sich beruehren, nicht decken
WALD_BAUM_SPERRT = True
WALD_STAMM_SPERRE = (0.26, 0.13)   # Breite/Hoehe der Stammhitbox am Bild

WALD_DEKO_PRO_FELD = (3, 6)
WALD_DEKO_HOEHE = (26, 62)
WALD_STEIN_CHANCE = 0.40

ZONE_DUNKEL_BAUM = (150, 190, 214)   # Farbfilter fuer den dunklen Bestand
# Der Boden ist ueberall derselbe - dadurch gibt es keine Kachelnaht mehr
# an den Zonengrenzen. Unterschiedlich sind nur noch die Baeume.

# --- Welt 3: Erdreich ------------------------------------------
# Die Felsen sind klein gehalten, damit das Pixelraster fein wirkt.
STEIN_SPERRT = True
STEIN_FUSS_ANTEIL = 0.62    # unterer Bildanteil, der auf dem Boden aufsitzt
STEIN_PRO_FELD = (1, 4)
# Die Felsen sind Pixelgrafik. Sie werden deshalb nur um ganze Faktoren
# vergroessert und ohne Glaettung - sonst verwaschen die Kanten.
STEIN_FAKTOREN = (1, 2)     # im Erdreich
WALD_STEIN_FAKTOREN = (1,)  # im Wald

# --- Welt 4: Labyrinth -----------------------------------------
W4_STEINE_PRO_FELD = (0, 2)
W4_STEIN_FAKTOREN = (1,)
WAND_KANTE = (18, 15, 15)
WAND_LICHT = (96, 88, 84)

# ---------------------------------------------------------------
# Bilder. Mehr als diese Dateien benutzt die Landschaft nicht.
# ---------------------------------------------------------------
BILDER = {
    "boden_wald":  "wald_boden.png",
    "boden_stein": "stein_boden.png",
    "wand_stein":  "stein_wand.png",
    "baum_1":      "wald_baum_normal.png",
    "baum_2":      "wald_baum_a.png",
    "baum_3":      "wald_baum_d.png",
    "gras_1":      "wald_gras_2.png",
    "gras_2":      "wald_gras_3.png",
    "stein_1":     "stein_1.png",
    "stein_2":     "stein_2.png",
    "stein_3":     "stein_3.png",
}

# Ein vorbereitetes Landschaftsteil: Bild plus Hitbox relativ zur
# linken oberen Ecke des Bildes (None = man laeuft hindurch).
Teil = namedtuple("Teil", "bild sperre")


# ---------------------------------------------------------------
# Bildwerkzeuge
# ---------------------------------------------------------------
def freistellen(bild, farbe=(0, 0, 0), toleranz=26, hart=200):
    """Hintergrundfarbe durchsichtig machen, mit weichem Uebergang.

    Ein Colorkey allein reicht nicht: die Rohbilder rauschen, reines
    Schwarz ist selten, und um die Felsen liegt ein feiner Schleier.
    Deshalb zwei Schwellen: unter toleranz ganz durchsichtig, ab hart
    voll deckend, dazwischen weich. Der Schleier bleibt damit sichtbar,
    zaehlt aber nicht mehr zum Umriss - genau das braucht die Hitbox.
    Ohne numpy bleibt der Colorkey als Notloesung."""
    bild = bild.convert_alpha()
    try:
        import numpy as np
        farben = pygame.surfarray.pixels3d(bild).astype(np.int16)
        alpha = pygame.surfarray.pixels_alpha(bild)
        abstand = abs(farben - np.array(farbe, np.int16)).sum(axis=2)
        weich = np.clip((abstand - toleranz) * 255 // max(1, hart - toleranz),
                        0, 255).astype(np.uint8)
        alpha[:] = np.minimum(alpha, weich)
        del farben, alpha
    except Exception:
        bild.set_colorkey(farbe)
    return bild


# Ab dieser Deckkraft zaehlt ein Pixel als "fest" - fuer Zuschnitt und
# Hitbox. Der weiche Schleier um die Felsen liegt darunter.
FEST = 200


def zuschneiden(bild, min_alpha=FEST):
    """Durchsichtigen Rand abschneiden - die Unterkante ist der Fusspunkt."""
    kasten = bild.get_bounding_rect(min_alpha)
    return bild.subsurface(kasten).copy() if kasten.width else bild


def auf_hoehe(bild, hoehe):
    faktor = hoehe / max(1, bild.get_height())
    return pygame.transform.smoothscale(
        bild, (max(1, int(bild.get_width() * faktor)), max(1, int(hoehe))))


def fussabdruck(bild, anteil, min_alpha=FEST):
    """Hitbox aus den Bildpunkten: Umriss des unteren Bildteils."""
    hoehe = bild.get_height()
    oben = int(hoehe * (1.0 - anteil))
    band = bild.subsurface(pygame.Rect(0, oben, bild.get_width(), hoehe - oben))
    umriss = band.get_bounding_rect(min_alpha)
    if umriss.width < 3 or umriss.height < 3:
        return None
    return pygame.Rect(umriss.x, oben + umriss.y, umriss.width, umriss.height)


def toenen(bild, farbe):
    """Farbfilter (Multiplikation, 255 = unveraendert)."""
    kopie = bild.copy()
    filter_ = pygame.Surface(bild.get_size(), pygame.SRCALPHA)
    filter_.fill(farbe + (255,))
    kopie.blit(filter_, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return kopie


# ---------------------------------------------------------------
# Dunkelheit und Taschenlampe
# ---------------------------------------------------------------
class Dunkelheit:
    """Schwarze Flaeche mit einem weichen Loch um den Spieler.

    Die Masken werden einmal gebaut und gemerkt - der Spieler steht in
    den Aussenwelten immer in der Bildmitte, also wandert das Loch nie.
    Pro Bild bleiben zwei Blits."""

    def __init__(self):
        self._masken = {}
        self._schein = {}
        self._flacker = pygame.Surface((WIDTH, HEIGHT))
        self._flacker.fill((0, 0, 0))

    @staticmethod
    def _mitte():
        # Koerpermitte des Spielers, nicht die Ecke seines Sprites
        return WIDTH // 2, HEIGHT // 2 + 20

    def _maske(self, radius):
        if radius not in self._masken:
            maske = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            maske.fill((0, 0, 0, 255))
            loch = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            stufen = 48
            for i in range(stufen, 0, -1):
                t = i / stufen
                deckung = 1.0 if t <= W4_LICHT_WEICH else \
                    1.0 - (t - W4_LICHT_WEICH) / (1.0 - W4_LICHT_WEICH)
                pygame.draw.circle(loch, (0, 0, 0, int(255 * deckung)),
                                   (radius, radius), int(radius * t))
            mx, my = self._mitte()
            maske.blit(loch, (mx - radius, my - radius),
                       special_flags=pygame.BLEND_RGBA_SUB)
            self._masken[radius] = maske.convert_alpha()
        return self._masken[radius]

    def _lichtschein(self, radius):
        """Warmer Schimmer im Kegel - macht die Lampe fuehlbar."""
        if radius not in self._schein:
            schein = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            mx, my = self._mitte()
            stufen = 24
            for i in range(stufen, 0, -1):
                t = i / stufen
                staerke = (1.0 - t) ** 2
                pygame.draw.circle(
                    schein, tuple(int(c * staerke) for c in W4_LICHT_FARBE) + (255,),
                    (mx, my), int(radius * t))
            self._schein[radius] = schein.convert_alpha()
        return self._schein[radius]

    def zeichne(self, screen, lampe_an, zeit):
        radius = W4_LICHT_AN if lampe_an else W4_LICHT_AUS
        if lampe_an:
            screen.blit(self._lichtschein(radius), (0, 0),
                        special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(self._maske(radius), (0, 0))
        if W4_LICHT_FLACKERN and lampe_an:
            # zwei ueberlagerte Schwingungen: unregelmaessig ohne Zufall
            wert = (math.sin(zeit * 11.0) + math.sin(zeit * 4.3)) * 0.5
            self._flacker.set_alpha(int(W4_LICHT_FLACKERN * (0.5 + 0.5 * wert)))
            screen.blit(self._flacker, (0, 0))



# ---------------------------------------------------------------
# Welt 5: Geister
# ---------------------------------------------------------------
class Geister:
    """Schemen, die im Lavareich quer durchs Bild ziehen.

    Sie starten immer ausserhalb des Blickfelds und fliegen geradlinig
    hindurch - so sieht man sie kommen und kann ausweichen. Wer sich
    beruehren laesst, hat die Welt verloren.

    Die Schemen sind rund, also braucht nichts gedreht zu werden. Der
    Schweif entsteht dadurch, dass dasselbe Bild ein paar Mal blasser
    hinter den Geist gesetzt wird - das kostet nur Blits."""

    SCHWEIF = (1.0, 0.42, 0.20, 0.09)   # Helligkeit der Schweifbilder
    KERN = 0.52                         # Helligkeit im Zentrum

    def __init__(self):
        self._bilder = {}
        self.geister = []
        self.naechster = 1.2
        self._rnd = random.Random()

    # ------------------------------------------------------------
    def _schemen(self, durchmesser):
        """Vier Stufen desselben Lichtflecks, von hell bis fast weg.

        Gezeichnet wird additiv, deshalb steckt die Helligkeit in den
        Farbwerten und nicht im Alphakanal - sonst addieren sich die
        Schweifbilder zu einem weissen Klecks."""
        if durchmesser not in self._bilder:
            stufen = []
            for staerke in self.SCHWEIF:
                bild = pygame.Surface((durchmesser, durchmesser),
                                      pygame.SRCALPHA)
                mitte = durchmesser // 2
                ringe = 30
                for i in range(ringe, 0, -1):
                    t = i / ringe
                    hell = self.KERN * staerke * (1.0 - t) ** 2.4
                    farbe = tuple(min(255, int(c * hell)) for c in W5_GEIST_FARBE)
                    pygame.draw.circle(bild, farbe + (255,), (mitte, mitte),
                                       max(1, int(mitte * t)))
                stufen.append(bild.convert_alpha())
            self._bilder[durchmesser] = stufen
        return self._bilder[durchmesser]

    # ------------------------------------------------------------
    def zuruecksetzen(self):
        self.geister.clear()
        self.naechster = 1.2

    def _neuer(self, mitte):
        """Startet ausserhalb des Bildes und zielt durch die Mitte."""
        rnd = self._rnd
        winkel = rnd.uniform(0, math.tau)
        abstand = 820                      # halbe Bilddiagonale plus Rand
        start = (mitte[0] + math.cos(winkel) * abstand,
                 mitte[1] + math.sin(winkel) * abstand)
        # Zielpunkt leicht neben dem Spieler - sonst wird es unausweichlich
        ziel = (mitte[0] + rnd.uniform(-170, 170),
                mitte[1] + rnd.uniform(-170, 170))
        dx, dy = ziel[0] - start[0], ziel[1] - start[1]
        laenge = max(1.0, math.hypot(dx, dy))
        tempo = rnd.uniform(*W5_GEIST_TEMPO)
        durchmesser = rnd.randrange(W5_GEIST_GROESSE[0], W5_GEIST_GROESSE[1], 10)
        self.geister.append({"pos": [start[0], start[1]],
                             "v": (dx / laenge * tempo, dy / laenge * tempo),
                             "d": durchmesser, "alter": 0.0})

    def update(self, dt, mitte):
        """Bewegt die Geister. True, wenn einer den Spieler erwischt hat."""
        self.naechster -= dt
        if self.naechster <= 0.0 and len(self.geister) < W5_GEIST_MAX:
            self._neuer(mitte)
            self.naechster = self._rnd.uniform(*W5_GEIST_INTERVALL)

        getroffen = False
        uebrig = []
        for g in self.geister:
            g["pos"][0] += g["v"][0] * dt
            g["pos"][1] += g["v"][1] * dt
            g["alter"] += dt
            dx, dy = g["pos"][0] - mitte[0], g["pos"][1] - mitte[1]
            if dx * dx + dy * dy < W5_GEIST_TREFFER ** 2:
                getroffen = True
                continue
            if dx * dx + dy * dy < 1100 ** 2:
                uebrig.append(g)
        self.geister = uebrig
        return getroffen

    def zeichne(self, screen, camera):
        for g in self.geister:
            stufen = self._schemen(g["d"])
            halb = g["d"] // 2
            # von hinten nach vorne: erst der blasseste Schweif
            for i in range(len(stufen) - 1, -1, -1):
                zurueck = i * 0.075
                x = g["pos"][0] - g["v"][0] * zurueck - camera[0] - halb
                y = g["pos"][1] - g["v"][1] * zurueck - camera[1] - halb
                if -g["d"] < x < WIDTH and -g["d"] < y < HEIGHT:
                    screen.blit(stufen[i], (int(x), int(y)),
                                special_flags=pygame.BLEND_RGB_ADD)


# ---------------------------------------------------------------
# Landschaft
# ---------------------------------------------------------------
class Landschaft:
    """Boden, Bewuchs und Kollision der Aussenwelten."""

    def __init__(self, bildordner):
        self.ordner = bildordner
        self.fehlend = []
        self._felder = {}
        self._extra = {}           # feste Zusatzobjekte, z.B. Nester um Blaetter
        self._lichtungen = {}      # freigeraeumte Kreise, z.B. um die Tuer
        self.dunkelheit = Dunkelheit()

        # ---------------- Boden ----------------
        self.boden_wald = self._kachel(self._bild("boden_wald"))
        self.boden_stein = self._kachel(self._bild("boden_stein"))
        self.boden_tunnel = toenen(self.boden_stein, (152, 132, 116))
        self.wand_kachel = self._bild("wand_stein")

        # ---------------- Baeume: genau zwei Groessen ----------------
        baeume = [self._bild(n) for n in ("baum_1", "baum_2", "baum_3")]
        self.baeume_laub = self._baumstufen(baeume)
        self.baeume_nadel = self._baumstufen(
            [toenen(b, ZONE_DUNKEL_BAUM) for b in baeume])

        # ---------------- Felsen ----------------
        felsen = [self._bild(n) for n in ("stein_1", "stein_2", "stein_3")]
        fuss = STEIN_FUSS_ANTEIL if STEIN_SPERRT else None
        self.steine = self._pixelstufen(felsen, STEIN_FAKTOREN, fuss)
        # Die grossen Brocken: fuer Ringe um Sammelpunkte, damit sie
        # aus der Ferne als Hindernis zu erkennen sind.
        self.steine_gross = self._pixelstufen(felsen, STEIN_FAKTOREN[-1:], fuss)
        self.steine_klein = self._pixelstufen(felsen, WALD_STEIN_FAKTOREN, fuss)
        self.brocken = self._pixelstufen(felsen, W4_STEIN_FAKTOREN, None)

        # ---------------- Kleinkram ----------------
        self.deko = self._stufen([self._bild("gras_1"), self._bild("gras_2")],
                                 WALD_DEKO_HOEHE, 2)

    # ------------------------------------------------------------------
    # Laden
    # ------------------------------------------------------------------
    def _bild(self, schluessel):
        dateiname = BILDER[schluessel]
        pfad = os.path.join(self.ordner, dateiname)
        if os.path.exists(pfad):
            try:
                return pygame.image.load(pfad).convert_alpha()
            except pygame.error as fehler:
                print(f"{dateiname} laesst sich nicht laden: {fehler}")
        self.fehlend.append(dateiname)
        print(f"BILD FEHLT: {dateiname}")
        platz = pygame.Surface((128, 128), pygame.SRCALPHA)
        platz.fill((255, 0, 200))
        pygame.draw.rect(platz, (0, 0, 0), platz.get_rect(), 3)
        return platz

    @staticmethod
    def _kachel(bild):
        return pygame.transform.scale(bild, (WIDTH, HEIGHT)).convert()

    @staticmethod
    def _pixelstufen(quellen, faktoren, fuss=None):
        """Pixelgrafik nur ganzzahlig und ohne Glaettung vergroessern."""
        fertig = []
        for bild in quellen:
            for f in faktoren:
                b = bild if f == 1 else pygame.transform.scale(
                    bild, (bild.get_width() * f, bild.get_height() * f))
                fertig.append(Teil(b, fussabdruck(b, fuss) if fuss else None))
        return fertig

    @staticmethod
    def _stufen(quellen, spanne, anzahl, fuss=None):
        """Jedes Bild in mehreren Groessen vorbereiten - dann muss
        waehrend des Spiels nichts mehr skaliert werden."""
        fertig = []
        for bild in quellen:
            for i in range(anzahl):
                t = i / max(1, anzahl - 1)
                b = auf_hoehe(bild, int(spanne[0] + t * (spanne[1] - spanne[0])))
                fertig.append(Teil(b, fussabdruck(b, fuss) if fuss else None))
        return fertig

    @staticmethod
    def _baumstufen(quellen):
        """Baeume in genau zwei Groessen: mittel und gross."""
        fertig = []
        for bild in quellen:
            for hoehe in (WALD_BAUM_MITTEL, WALD_BAUM_GROSS):
                b = auf_hoehe(bild, hoehe)
                kasten = None
                if WALD_BAUM_SPERRT:
                    br = int(b.get_width() * WALD_STAMM_SPERRE[0])
                    ho = int(b.get_height() * WALD_STAMM_SPERRE[1])
                    kasten = pygame.Rect((b.get_width() - br) // 2,
                                         b.get_height() - ho, br, ho)
                fertig.append(Teil(b, kasten))
        return fertig

    # ------------------------------------------------------------------
    # Zonen
    # ------------------------------------------------------------------
    @staticmethod
    def zone(x, y):
        i = math.floor((x + y * WALD_ZONE_NEIGUNG) / WALD_ZONE_BREITE)
        return "laub" if i % 2 == 0 else "nadel"

    # ------------------------------------------------------------------
    # Boden zeichnen
    # ------------------------------------------------------------------
    def boden(self, screen, camera, welt):
        """Untergrund der Welt. True, wenn zustaendig."""
        if welt == "world2":
            self._boden_gleich(screen, camera, self.boden_wald)
        elif welt == "world3":
            self._boden_gleich(screen, camera, self.boden_stein)
        elif welt == "world4":
            self._boden_gleich(screen, camera, self.boden_tunnel)
        else:
            return False
        return True

    @staticmethod
    def _boden_gleich(screen, camera, kachel):
        kw, kh = kachel.get_size()
        sx, sy = -(camera[0] % kw), -(camera[1] % kh)
        y = sy - kh
        while y < HEIGHT:
            x = sx - kw
            while x < WIDTH:
                screen.blit(kachel, (x, y))
                x += kw
            y += kh

    # ------------------------------------------------------------------
    # Landschaft wuerfeln
    # ------------------------------------------------------------------
    def _feld(self, welt, cx, cy):
        schluessel = (welt, cx, cy)
        if schluessel not in self._felder:
            if len(self._felder) > CACHE_MAX:
                self._felder.clear()
            objekte = self._bauen(welt, cx, cy)
            kreise = self._lichtungen.get(welt)
            if kreise:
                objekte = [o for o in objekte if not self._in_lichtung(o, kreise)]
            self._felder[schluessel] = objekte
        return self._felder[schluessel]

    @staticmethod
    def _wuerfel(welt, cx, cy):
        return random.Random((cx * 73856093) ^ (cy * 19349663)
                             ^ (hash(welt) & 0xFFFFFF))

    def _bauen(self, welt, cx, cy):
        if welt == "world2":
            return self._bauen_wald(cx, cy)
        if welt == "world3":
            return self._bauen_erde(cx, cy)
        if welt == "world4":
            return self._bauen_tunnel(cx, cy)
        return []

    @staticmethod
    def _nah_am_start(x, y):
        return abs(x) < FREI_UM_START and abs(y) < FREI_UM_START

    @staticmethod
    def _stellen(teil, x, fuss, lage=1):
        """Teil an einen Fusspunkt in Weltkoordinaten setzen.

        lage=0 heisst: liegt flach am Boden (umgefallener Stamm, Gras).
        Solche Teile werden immer zuerst gezeichnet, also hinter den
        Baeumen und hinter dem Spieler."""
        links = int(x - teil.bild.get_width() // 2)
        oben = int(fuss - teil.bild.get_height())
        sperre = None
        if teil.sperre is not None:
            sperre = pygame.Rect(links + teil.sperre.x, oben + teil.sperre.y,
                                 teil.sperre.width, teil.sperre.height)
        return {"bild": teil.bild, "x": links, "y": oben, "lage": lage,
                "fuss": int(fuss), "block": sperre}

    def _bauen_wald(self, cx, cy):
        rnd = self._wuerfel("world2", cx, cy)
        objekte, staemme = [], []
        bx, by = cx * CHUNK, cy * CHUNK

        for _ in range(rnd.randint(*WALD_BAEUME_PRO_FELD)):
            x, fuss = bx + rnd.randrange(CHUNK), by + rnd.randrange(CHUNK)
            if self._nah_am_start(x, fuss):
                continue
            # dicht, aber nicht deckungsgleich
            if any(abs(x - px) < WALD_MINDESTABSTAND
                   and abs(fuss - py) < WALD_MINDESTABSTAND
                   for px, py in staemme):
                continue
            staemme.append((x, fuss))
            art = self.zone(x, fuss)
            if rnd.random() < WALD_MISCHUNG:
                art = "nadel" if art == "laub" else "laub"
            vorrat = self.baeume_laub if art == "laub" else self.baeume_nadel
            gross = rnd.random() < WALD_GROSS_ANTEIL
            passend = [t for i, t in enumerate(vorrat) if (i % 2 == 1) == gross]
            objekte.append(self._stellen(rnd.choice(passend), x, fuss))

        for _ in range(rnd.randint(*WALD_DEKO_PRO_FELD)):
            objekte.append(self._stellen(rnd.choice(self.deko),
                                         bx + rnd.randrange(CHUNK),
                                         by + rnd.randrange(CHUNK), lage=0))

        if rnd.random() < WALD_STEIN_CHANCE:
            x, fuss = bx + rnd.randrange(CHUNK), by + rnd.randrange(CHUNK)
            if not self._nah_am_start(x, fuss):
                objekte.append(self._stellen(rnd.choice(self.steine_klein), x, fuss))

        objekte.sort(key=lambda o: (o["lage"], o["fuss"]))
        return objekte

    def _bauen_erde(self, cx, cy):
        rnd = self._wuerfel("world3", cx, cy)
        objekte = []
        for _ in range(rnd.randint(*STEIN_PRO_FELD)):
            x = cx * CHUNK + rnd.randrange(CHUNK)
            fuss = cy * CHUNK + rnd.randrange(CHUNK)
            if self._nah_am_start(x, fuss):
                continue
            objekte.append(self._stellen(rnd.choice(self.steine), x, fuss))
        objekte.sort(key=lambda o: o["fuss"])
        return objekte

    def _bauen_tunnel(self, cx, cy):
        rnd = self._wuerfel("world4", cx, cy)
        objekte = [self._stellen(rnd.choice(self.brocken),
                                 cx * CHUNK + rnd.randrange(CHUNK),
                                 cy * CHUNK + rnd.randrange(CHUNK))
                   for _ in range(rnd.randint(*W4_STEINE_PRO_FELD))]
        objekte.sort(key=lambda o: o["fuss"])
        return objekte

    # ------------------------------------------------------------------
    # Zugriff
    # ------------------------------------------------------------------
    def _umgebung(self, welt, bereich):
        for cy in range(math.floor(bereich.top / CHUNK),
                        math.floor(bereich.bottom / CHUNK) + 1):
            for cx in range(math.floor(bereich.left / CHUNK),
                            math.floor(bereich.right / CHUNK) + 1):
                for objekt in self._feld(welt, cx, cy):
                    yield objekt
        for objekt in self._extra.get(welt, ()):
            if bereich.colliderect(pygame.Rect(
                    objekt["x"], objekt["y"], objekt["bild"].get_width(),
                    objekt["bild"].get_height())):
                yield objekt

    def zeichne(self, screen, camera, welt, spieler_fuss, vorne):
        """vorne=False: hinter dem Spieler. vorne=True: davor."""
        if welt not in ("world2", "world3", "world4"):
            return
        sicht = pygame.Rect(camera[0] - 520, camera[1] - 520,
                            WIDTH + 1040, HEIGHT + 1040)
        for objekt in sorted(self._umgebung(welt, sicht),
                             key=lambda o: (o["lage"], o["fuss"])):
            if objekt["lage"] == 0:
                # liegt am Boden: immer hinter Baeumen und Spieler
                if vorne:
                    continue
            elif (objekt["fuss"] > spieler_fuss) != vorne:
                continue
            x, y = objekt["x"] - camera[0], objekt["y"] - camera[1]
            bild = objekt["bild"]
            if -bild.get_width() < x < WIDTH and -bild.get_height() < y < HEIGHT:
                screen.blit(bild, (x, y))

    def zeichne_waende(self, screen, camera, waende):
        """Labyrinthwaende aus Fels statt einfarbiger Kaesten."""
        kachel = self.wand_kachel
        kw, kh = kachel.get_size()
        sicht = pygame.Rect(camera[0] - 64, camera[1] - 64,
                            WIDTH + 128, HEIGHT + 128)
        alter_clip = screen.get_clip()
        for wand in waende:
            if not sicht.colliderect(wand):
                continue
            r = pygame.Rect(wand.x - camera[0], wand.y - camera[1],
                            wand.width, wand.height)
            screen.set_clip(r)
            y = r.y - (wand.y % kh)
            while y < r.bottom:
                x = r.x - (wand.x % kw)
                while x < r.right:
                    screen.blit(kachel, (x, y))
                    x += kw
                y += kh
            screen.set_clip(alter_clip)
            pygame.draw.rect(screen, WAND_KANTE, r, 2)
            pygame.draw.line(screen, WAND_LICHT, (r.left + 2, r.top + 2),
                             (r.right - 3, r.top + 2), 2)

    # ------------------------------------------------------------------
    # Kollision
    # ------------------------------------------------------------------
    def blockiert(self, welt, rect):
        if welt not in ("world2", "world3", "world4"):
            return False
        for objekt in self._umgebung(welt, rect):
            if objekt["block"] is not None and rect.colliderect(objekt["block"]):
                return True
        return False

    # ------------------------------------------------------------------
    # Nester: Hindernisse um ein Blatt, aber nie ohne Weg hinein
    # ------------------------------------------------------------------
    def belegung(self, welt, rect):
        """Wie viele Dinge stehen in diesem Bereich? Fuer die Platzsuche."""
        anzahl = 0
        for o in self._umgebung(welt, rect):
            bild = o["bild"]
            if rect.colliderect(pygame.Rect(o["x"], o["y"],
                                            bild.get_width(), bild.get_height())):
                anzahl += 1
        return anzahl

    def erreichbar(self, welt, pos, radius=430, schritt=24):
        """Kommt man von aussen an diesen Punkt heran?"""
        return self._erreichbar(welt, pos, radius, schritt)

    def nest_bauen(self, welt, pos, radius=None, stuecke=None, luecke=None,
                   vorrat=None):
        """Stellt einen Ring aus Baeumen und Staemmen um pos.

        Der Ring hat von vornherein eine Luecke. Danach wird
        nachgerechnet, ob man wirklich hineinkommt - und solange ein
        Stueck entfernt, bis es geht. True, wenn das Blatt am Ende
        erreichbar ist."""
        if welt not in ("world2", "world3", "world4"):
            return True
        radius = W2_NEST_RADIUS if radius is None else radius
        stuecke = W2_NEST_STUECKE if stuecke is None else stuecke
        luecke_breite = W2_NEST_LUECKE if luecke is None else luecke
        rnd = random.Random(int(pos[0]) * 7919 + int(pos[1]) * 104729)
        luecke = rnd.uniform(0, math.tau)
        liste = self._extra.setdefault(welt, [])
        neue = []
        for i in range(stuecke):
            w = math.tau * i / stuecke
            if abs((w - luecke + math.pi) % math.tau - math.pi) < luecke_breite:
                continue
            weite = radius * rnd.uniform(0.88, 1.12)
            x = pos[0] + math.cos(w) * weite
            y = pos[1] + math.sin(w) * weite
            if vorrat is not None:
                # Vorgegebener Vorrat, z.B. Felsen im Erdreich
                teil, lage = rnd.choice(vorrat), 1
            elif math.sin(w) > 0.25:
                # Unterhalb des Blattes keine Baeume: eine Krone wird weit
                # ueber ihrem Fuss gezeichnet und wuerde das Blatt sonst
                # verdecken, obwohl man hinkommt. Felsen sind flach genug.
                teil, lage = rnd.choice(self.steine_gross), 1
            else:
                teil, lage = rnd.choice(self.baeume_laub + self.baeume_nadel), 1
            objekt = self._stellen(teil, x, y, lage=lage)
            neue.append(objekt)
            liste.append(objekt)

        while not self._erreichbar(welt, pos):
            if not neue:
                return False
            weg = neue.pop(rnd.randrange(len(neue)))
            liste.remove(weg)
        return True

    def lichtung(self, welt, pos, radius):
        """Raeumt einen Kreis frei - fuer die Tuer und fuer Sammelpunkte.

        Zusatzobjekte werden gestrichen, und die betroffenen Felder
        werden vergessen; beim naechsten Zeichnen entstehen sie neu und
        lassen dabei alles weg, was in einer Lichtung liegt. Dadurch
        bleibt die Landschaft berechenbar, ohne dass man Objekte
        einzeln loeschen muss."""
        kreis = (int(pos[0]), int(pos[1]), int(radius))
        self._lichtungen.setdefault(welt, []).append(kreis)
        liste = self._extra.get(welt)
        if liste:
            self._extra[welt] = [o for o in liste if not self._in_lichtung(o, [kreis])]
        weg = [k for k in self._felder
               if k[0] == welt
               and abs(k[1] * CHUNK + CHUNK // 2 - kreis[0]) < radius + CHUNK
               and abs(k[2] * CHUNK + CHUNK // 2 - kreis[1]) < radius + CHUNK]
        for k in weg:
            del self._felder[k]

    @staticmethod
    def _in_lichtung(objekt, kreise):
        """Ueberdeckt das Objekt einen freigeraeumten Kreis?

        Gemessen wird am gezeichneten Rechteck, nicht am Fusspunkt -
        sonst haengt eine Baumkrone weit ueber der Lichtung."""
        bild = objekt["bild"]
        r = pygame.Rect(objekt["x"], objekt["y"],
                        bild.get_width(), bild.get_height())
        for mx, my, radius in kreise:
            if r.colliderect(pygame.Rect(mx - radius, my - radius,
                                         radius * 2, radius * 2)):
                return True
        return False

    def nester_loeschen(self, welt=None):
        """Alle Zusatzobjekte und Lichtungen einer Welt zuruecksetzen."""
        if welt is None:
            self._extra.clear()
            self._lichtungen.clear()
            self._felder.clear()
        else:
            self._extra.pop(welt, None)
            self._lichtungen.pop(welt, None)
            for k in [k for k in self._felder if k[0] == welt]:
                del self._felder[k]

    def _erreichbar(self, welt, pos, radius=430, schritt=24):
        """Kommt man von aussen an pos heran?

        Rasterlauf mit der Fussbox des Spielers. Startet am Blatt und
        sucht einen Weg nach draussen; findet er keinen, ist das Blatt
        eingemauert."""
        rand = radius + 120
        bereich = pygame.Rect(pos[0] - rand, pos[1] - rand, 2 * rand, 2 * rand)
        sperren = [o["block"] for o in self._umgebung(welt, bereich)
                   if o["block"] is not None]
        breite, hoehe = R1_HITBOX[2], R1_HITBOX[3]
        n = int(radius / schritt)

        def frei(gx, gy):
            kasten = pygame.Rect(int(pos[0] + gx * schritt - breite // 2),
                                 int(pos[1] + gy * schritt - hoehe // 2),
                                 breite, hoehe)
            return not any(kasten.colliderect(s) for s in sperren)

        if not frei(0, 0):
            return False
        gesehen = {(0, 0)}
        stapel = [(0, 0)]
        while stapel:
            gx, gy = stapel.pop()
            if gx * gx + gy * gy >= (n - 1) ** 2:
                return True            # draussen angekommen
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (gx + dx, gy + dy)
                if q in gesehen or q[0] * q[0] + q[1] * q[1] > n * n:
                    continue
                gesehen.add(q)
                if frei(*q):
                    stapel.append(q)
        return False

    def frei_ruecken(self, welt, pos, groesse=96, versuche=60):
        """Schiebt einen Punkt aus Hindernissen und dichtem Bewuchs.

        Damit landet kein Papier unter einem Baum oder hinter einem Fels."""
        if welt not in ("world2", "world3", "world4"):
            return pos
        rnd = random.Random(int(pos[0]) * 31 + int(pos[1]))
        for versuch in range(versuche):
            kasten = pygame.Rect(int(pos[0]) - groesse // 2,
                                 int(pos[1]) - groesse // 2, groesse, groesse)
            if not self._verdeckt(welt, kasten):
                return pos
            weite = 90 + versuch * 14
            pos[0] += rnd.randint(-weite, weite)
            pos[1] += rnd.randint(-weite, weite)
        return pos

    def _verdeckt(self, welt, kasten):
        for objekt in self._umgebung(welt, kasten):
            if objekt["block"] is not None and kasten.colliderect(objekt["block"]):
                return True
            bild = objekt["bild"]
            if bild.get_height() > 120 and kasten.colliderect(
                    pygame.Rect(objekt["x"], objekt["y"],
                                bild.get_width(), bild.get_height())):
                return True
        return False


# ######################################################################
# Dialogfenster.py
# ######################################################################
# ---------------------------------------------------------------
# Sprecherfarben: der Dialog nennt keine Namen mehr, die Farbe sagt,
# wer spricht.
# ---------------------------------------------------------------
FARBE_STANDARD = (0, 255, 0)         # Erzähler, Weltbeschreibung, Auswahl
FARBE_ZUKUNFTS_ICH = (255, 180, 65)  # das Zukunfts-Ich: warmes Bernstein
FARBE_FRAU = (255, 105, 105)         # die Frau
FARBE_GEDICHT = (0, 255, 0)          # Zettel und Gedichte: wie der Erzähler
FARBE_FEHLER = (255, 80, 80)         # falsche Eingabe im Finale


class DialogSystem:
    def __init__(self, screen, width=800, height=200):
        self.screen = screen
        self.width = width
        self.height = height
        self.dialog_surface = pygame.Surface((width, height))
        # Größere Schrift für Vollbild
        self.font = pygame.font.Font(None, int(height / 15))
        self.text_color = FARBE_STANDARD
        self.bg_color = (0, 0, 0)
        self.padding = int(width / 40)
        self.line_height = int(height / 15)
        self.current_text = []
        self.current_choices = []
        self.selected_choice = 0
        self.active = False
        self.max_lines = (height - 2 * self.padding) // self.line_height
        self.cursor_blink = 0
        self.show_cursor = True
        # Versmodus: Zeilen bleiben so, wie sie geschrieben sind, und werden
        # zentriert - für Gedichte und Zettel.
        self.vers_modus = False

        # ---- NEU: Eingabemodus für das Finale am Computer ----
        # Der Spieler tippt selbst. Funktioniert identisch im Browser
        # (pygbag liefert event.unicode bei KEYDOWN).
        self.input_modus = False
        self.input_buffer = ""
        self.input_max = 24
        self.input_hinweis = ""

    # -----------------------------------------------------------
    # Anzeigen
    # -----------------------------------------------------------
    def show_dialog(self, text, choices=None, farbe=None):
        """Normaler Dialog. farbe bestimmt, wer spricht."""
        self.active = True
        self.vers_modus = False
        self.input_modus = False
        self.text_color = farbe if farbe else FARBE_STANDARD
        self.current_text = self._wrap_text(text)
        self.current_choices = choices if choices else []
        self.selected_choice = 0

    def show_poem(self, text, choices=None, farbe=None):
        """Gedicht oder Zettel: Versform bleibt erhalten, alles zentriert,
        der Text füllt das ganze Dialogfeld."""
        self.active = True
        self.vers_modus = True
        self.input_modus = False
        self.text_color = farbe if farbe else FARBE_GEDICHT
        self.current_text = self._verse(text)
        self.current_choices = choices if choices else []
        self.selected_choice = 0

    def show_input(self, text, farbe=None, max_len=24, hinweis="", vorgabe=""):
        """NEU: Eingabefeld. Der Spieler tippt, ENTER bestätigt.

        handle_input() liefert dann das Tupel ("EINGABE", "was getippt wurde").
        ESC liefert ("ABBRUCH", "").
        """
        self.active = True
        self.vers_modus = True          # zentrierte Darstellung wie beim Gedicht
        self.input_modus = True
        self.input_buffer = vorgabe
        self.input_max = max_len
        self.input_hinweis = hinweis
        self.text_color = farbe if farbe else FARBE_STANDARD
        self.current_text = self._verse(text)
        self.current_choices = []
        self.selected_choice = 0
        # Fordert auf Android die Bildschirmtastatur an; am Rechner
        # schaltet es nur die TEXTINPUT-Ereignisse scharf.
        global TASTATUR_OFFEN
        TASTATUR_OFFEN = True
        pygame.key.start_text_input()

    def hide_dialog(self):
        self.active = False
        self.vers_modus = False
        if self.input_modus:
            global TASTATUR_OFFEN
            TASTATUR_OFFEN = False
            pygame.key.stop_text_input()
        self.input_modus = False
        self.input_buffer = ""
        self.input_hinweis = ""
        self.text_color = FARBE_STANDARD
        self.current_text = []
        self.current_choices = []

    # -----------------------------------------------------------
    # Textaufbereitung
    # -----------------------------------------------------------
    def _wrap_text(self, text):
        """Bricht zu lange Zeilen um - aber gesetzte Zeilenumbrüche
        bleiben erhalten (\\n und Leerzeilen)."""
        lines = []
        for absatz in text.split("\n"):
            if not absatz.strip():
                lines.append("")          # Leerzeile bleibt Leerzeile
                continue
            current_line = []
            for word in absatz.split():
                test_line = " ".join(current_line + [word])
                if self.font.size(test_line)[0] < self.width - 2 * self.padding:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
                        current_line = []
            if current_line:
                lines.append(" ".join(current_line))
        return lines

    def _verse(self, text):
        """Versform: jede Zeile bleibt eine Zeile. Nur wenn eine Zeile
        wirklich zu breit ist, wird sie umgebrochen."""
        lines = []
        for zeile in text.split("\n"):
            zeile = zeile.rstrip()
            if not zeile:
                lines.append("")
                continue
            if self.font.size(zeile)[0] <= self.width - 2 * self.padding:
                lines.append(zeile)
                continue
            # Notfall-Umbruch für überlange Verse
            current_line = []
            for word in zeile.split():
                test_line = " ".join(current_line + [word])
                if self.font.size(test_line)[0] < self.width - 2 * self.padding:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(" ".join(current_line))
        return lines

    # -----------------------------------------------------------
    # Eingabe
    # -----------------------------------------------------------
    def handle_input(self, event):
        if not self.active:
            return None

        # ---- NEU: Tippen im Eingabemodus ----
        if self.input_modus:
            # Buchstaben kommen als TEXTINPUT - nur so liefert die
            # Bildschirmtastatur ihre Zeichen. Steuertasten bleiben
            # KEYDOWN, die schickt auch Android so.
            if event.type == pygame.TEXTINPUT:
                for zeichen in event.text:
                    if (zeichen.isprintable()
                            and len(self.input_buffer) < self.input_max):
                        self.input_buffer += zeichen
                return None
            if event.type != pygame.KEYDOWN:
                return None
            if event.key == pygame.K_RETURN:
                return ("EINGABE", self.input_buffer.strip())
            if event.key == pygame.K_ESCAPE:
                return ("ABBRUCH", "")
            if event.key == pygame.K_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            return None

        if not self.current_choices:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_choice = (self.selected_choice - 1) % len(self.current_choices)
            elif event.key == pygame.K_DOWN:
                self.selected_choice = (self.selected_choice + 1) % len(self.current_choices)
            elif event.key == pygame.K_RETURN:
                return self.current_choices[self.selected_choice]
        return None

    # -----------------------------------------------------------
    # Zeichnen
    # -----------------------------------------------------------
    def draw(self):
        if not self.active:
            return

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))

        self.dialog_surface.fill(self.bg_color)
        # Rahmen in der Sprecherfarbe: auch der Rand zeigt, wer redet
        pygame.draw.rect(self.dialog_surface, self.text_color,
                         (0, 0, self.width, self.height), 2)

        zeilen = self.current_text[-self.max_lines:]

        # Blinken einmal pro Frame weiterzählen (wird unten gebraucht)
        self.cursor_blink += 1
        if self.cursor_blink >= 30:
            self.show_cursor = not self.show_cursor
            self.cursor_blink = 0

        if self.vers_modus:
            # Ganzer Block vertikal zentriert, jede Zeile horizontal zentriert
            block_h = len(zeilen) * self.line_height
            wahl_h = (len(self.current_choices) * self.line_height
                      + self.line_height // 2) if self.current_choices else 0
            # NEU: Platz für Eingabezeile + Hinweis reservieren
            eingabe_h = (self.line_height * 3) if self.input_modus else 0
            y = max(self.padding,
                    (self.height - block_h - wahl_h - eingabe_h) // 2)
            for line in zeilen:
                if line:
                    surf = self.font.render(line, True, self.text_color)
                    rect = surf.get_rect(centerx=self.width // 2, top=y)
                    self.dialog_surface.blit(surf, rect)
                y += self.line_height
        else:
            y = self.padding
            for line in zeilen:
                if line:
                    surf = self.font.render(line, True, self.text_color)
                    self.dialog_surface.blit(surf, (self.padding, y))
                y += self.line_height

        # ---- NEU: die getippte Zeile ----
        if self.input_modus:
            y += self.line_height // 2
            gezeigt = self.input_buffer + ("_" if self.show_cursor else " ")
            surf = self.font.render(gezeigt, True, FARBE_STANDARD)
            rect = surf.get_rect(centerx=self.width // 2, top=y)
            self.dialog_surface.blit(surf, rect)
            # Unterstrich als Eingabefeld
            linie_y = rect.bottom + 4
            breite = max(rect.width + 40, self.width // 3)
            pygame.draw.line(
                self.dialog_surface, FARBE_STANDARD,
                (self.width // 2 - breite // 2, linie_y),
                (self.width // 2 + breite // 2, linie_y), 2)
            y += self.line_height

            if self.input_hinweis:
                y += self.line_height // 2
                surf = self.font.render(self.input_hinweis, True, (150, 150, 150))
                rect = surf.get_rect(centerx=self.width // 2, top=y)
                self.dialog_surface.blit(surf, rect)
                y += self.line_height

        if self.current_choices:
            y += self.line_height // 2
            for i, choice in enumerate(self.current_choices):
                prefix = ">" if i == self.selected_choice else " "
                # Auswahl bleibt immer grün: das bist du, nicht der Sprecher
                surf = self.font.render(f"{prefix} {choice}", True, FARBE_STANDARD)
                if self.vers_modus:
                    rect = surf.get_rect(centerx=self.width // 2, top=y)
                    self.dialog_surface.blit(surf, rect)
                else:
                    self.dialog_surface.blit(surf, (self.padding, y))
                y += self.line_height

        if (self.show_cursor and not self.current_choices and not self.input_modus
                and zeilen and not self.vers_modus):
            letzte = zeilen[-1]
            cursor_pos = (self.padding + self.font.size(letzte)[0] + 4,
                          y - self.line_height)
            surf = self.font.render("_", True, self.text_color)
            self.dialog_surface.blit(surf, cursor_pos)

        dialog_x = (self.screen.get_width() - self.width) // 2
        dialog_y = (self.screen.get_height() - self.height) // 2
        self.screen.blit(self.dialog_surface, (dialog_x, dialog_y))


# ######################################################################
# Spielmenu.py
# ######################################################################
class Menu:
    def __init__(self, settings):
        self.settings = settings
        self.main_options = ["Spiel starten", "Spielstand laden", "Spiel speichern", "Highscores", "Einstellungen", "Spiel verlassen"]
        self.settings_options = ["Vollbild Ein/Aus", "Zurück"]
        self.current_menu = "main"
        self.selected_option = 0
        
        # Hintergrund einmal laden statt in jedem Bild neu von der
        # Karte holen - auf dem Handy waere das sonst der Bremsklotz.
        self.hintergrund = None
        hg_pfad = os.path.join(BASIS, "images", "menu_background.png")
        if os.path.exists(hg_pfad):
            try:
                self.hintergrund = pygame.transform.scale(
                    pygame.image.load(hg_pfad).convert(), (WIDTH, HEIGHT))
            except pygame.error as e:
                print(f"Fehler beim Laden des Hintergrunds: {e}")

        font_path = os.path.join(BASIS, "fonts", "graffiti.ttf")
        try:
            # Separate Schriftgrößen für Titel und Optionen
            self.title_font = pygame.font.Font(font_path, 140)  # Größere Schrift für Titel
            self.option_font = pygame.font.Font(font_path, 90)  # Original-Größe für Optionen
        except Exception as e:
            print(f"Fehler beim Laden der Schriftart: {e}")
            self.title_font = pygame.font.Font(None, 140)
            self.option_font = pygame.font.Font(None, 90)
            
        # Hellere Rottöne
        self.BLOOD_RED = (220, 20, 20)    # Helleres Rot für ausgewählte Optionen
        self.DARK_RED = (150, 20, 20)     # Helleres Rot für nicht ausgewählte Optionen
        
    def draw(self, screen):
        WIDTH, HEIGHT = screen.get_size()
        
        if self.hintergrund is None:
            screen.fill((0, 0, 0))
        else:
            screen.blit(self.hintergrund, (0, 0))
    
        if self.current_menu == "main":
            options = self.main_options
            title = "Hauptmenü"
        else:
            options = self.settings_options
            title = "Einstellungen"
        
        # Titel mit verstärktem Schatten und tieferer Position
        shadow_offset = 6
        title_shadow = self.title_font.render(title, True, (0, 0, 0))
        title_text = self.title_font.render(title, True, self.BLOOD_RED)
        
        # Titel tiefer positionieren
        title_y = HEIGHT // 3.5  # Angepasste Position (vorher HEIGHT // 5)
        shadow_rect = title_shadow.get_rect(center=(WIDTH // 2 + shadow_offset, title_y + shadow_offset))
        title_rect = title_text.get_rect(center=(WIDTH // 2, title_y))
        
        screen.blit(title_shadow, shadow_rect)
        screen.blit(title_text, title_rect)
        
        # Optionen zeichnen; Zeilenabstand dynamisch, damit auch 5 Punkte passen
        menu_y = int(HEIGHT // 2.35)
        if len(options) > 1:
            line_spacing = min(140, (HEIGHT - menu_y - 70) // (len(options) - 1))
        else:
            line_spacing = 140
        
        for i, option in enumerate(options):
            color = self.BLOOD_RED if i == self.selected_option else self.DARK_RED
            
            if self.current_menu == "settings" and option == "Vollbild Ein/Aus":
                status = "AN" if ist_vollbild() else "AUS"
                option = f"Vollbild: {status}"
            
            shadow = self.option_font.render(option, True, (0, 0, 0))
            text = self.option_font.render(option, True, color)
            
            y_pos = menu_y + i * line_spacing
            
            shadow_rect = shadow.get_rect(center=(WIDTH // 2 + shadow_offset, y_pos + shadow_offset))
            text_rect = text.get_rect(center=(WIDTH // 2, y_pos))
            
            screen.blit(shadow, shadow_rect)
            screen.blit(text, text_rect)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(
                    self._get_current_options()
                )
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(
                    self._get_current_options()
                )
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._handle_selection()
            elif event.key == pygame.K_ESCAPE:
                if self.current_menu != "main":
                    self.current_menu = "main"
                    self.selected_option = 0
        return None

    def _get_current_options(self):
        if self.current_menu == "main":
            return self.main_options
        else:
            return self.settings_options

    def _handle_selection(self):
        if self.current_menu == "main":
            option = self.main_options[self.selected_option]
            if option == "Einstellungen":
                self.current_menu = "settings"
                self.selected_option = 0
                return None
            return option
        
        else:  # settings menu
            option = self.settings_options[self.selected_option]
            if option == "Vollbild Ein/Aus":
                vollbild_umschalten()
            elif option == "Zurück":
                self.current_menu = "main"
                self.selected_option = 0
            return None


# ######################################################################
# main.py
# ######################################################################
# Pygame initialisieren
pygame.init()

# Konstanten, Texte und ausgelagerte Spielbausteine

# Spielfeld definieren
# pygame.SCALED: das Spiel rechnet immer in 1024x1024, pygame skaliert das
# Bild auf das Fenster bzw. den Monitor. Dadurch passt es auch auf Laptops,
# deren nutzbare Hoehe kleiner als 1024 ist (Taskleiste), und der
# Vollbildmodus funktioniert ohne Umrechnung von Koordinaten.
try:
    if ANDROID:
        # Auf dem Handy zeichnet das Spiel in eine eigene Flaeche von
        # 1024x1024; erst beim Anzeigen wird sie aufs Display gerechnet.
        # Nur so lassen sich die Bedienknoepfe in die schwarzen Balken
        # legen, wo die Daumen ohnehin liegen - mit pygame.SCALED
        # saessen sie mitten im Spielbild.
        anzeige = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        screen = pygame.Surface((WIDTH, HEIGHT)).convert()
    else:
        anzeige = screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                                   pygame.SCALED)
except pygame.error:
    # Aeltere Grafiktreiber koennen SCALED nicht - dann eben ohne.
    anzeige = screen = pygame.display.set_mode((WIDTH, HEIGHT))

# ------------------------------------------------------------------
# Bedienung auf dem Bildschirm
# ------------------------------------------------------------------
# Das Spiel kennt nur Tastatur. Statt die Spiellogik umzubauen, legt
# sich hier eine Schicht davor: die Knoepfe nehmen Fingertipper
# entgegen und schicken genau die Tasten, die auch eine Tastatur
# schicken wuerde.
#
# Gehaltene Tasten (Laufen, Sprint) meldet sie ueber tastenstand(),
# jeden Druck zusaetzlich als echtes KEYDOWN/KEYUP in der
# Warteschlange - davon leben die Menues und die Dialogauswahl.
# Der Rest des Spiels merkt von alldem nichts.

TASTE_ZURUECK = getattr(pygame, "K_AC_BACK", -1)   # Zurueck-Taste des Handys

# Blickrichtung je Pfeiltaste - fuers Zeichnen der Dreiecke
PFEILRICHTUNG = {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
                 pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0)}


class Bildschirmsteuerung:
    """Vier Pfeiltasten links unten, Knoepfe rechts, kleine Reihe oben.

    Die Pfeiltasten sind einzelne eckige Tasten im Kreuz angeordnet -
    dieselbe Form wie auf der Tastatur, jede ein eigenes Feld."""

    FUELLUNG = (18, 16, 22, 130)
    RAND = (168, 162, 178, 175)
    GEDRUECKT = (200, 40, 40, 190)
    SCHRIFT = (236, 233, 242)

    def __init__(self, flaeche):
        # Am Rechner bleibt sie aus und laesst sich mit F2 einschalten,
        # um das Handy-Gefuehl auszuprobieren.
        self.sichtbar = ANDROID
        self.finger = {}          # Finger-ID -> Taste (oder None)
        self.groesse = None
        self._aufbauen(flaeche.get_size())

    # --------------------------------------------------------------
    # Aufbau
    # --------------------------------------------------------------
    def _aufbauen(self, groesse):
        """Legt die Tasten an. Alle Masse haengen an der kurzen Seite,
        damit es auf jedem Display gleich gross wirkt.

        Ein Eintrag ist (x, y, halbe_breite, Beschriftung, Taste,
        halten, eckig)."""
        self.groesse = groesse
        b, h = groesse
        k = min(b, h)
        m = k * 0.05

        # ---- Pfeiltasten: Kreuz aus vier eckigen Tasten ----
        self.taste_h = k * 0.062          # halbe Kantenlaenge
        spalt = self.taste_h * 0.24
        schritt = self.taste_h * 2 + spalt
        cx = m + self.taste_h * 3 + spalt
        cy = h - m - self.taste_h * 3 - spalt
        th = self.taste_h
        pfeile = [
            (cx, cy - schritt, th, "", pygame.K_UP, True, True),
            (cx, cy + schritt, th, "", pygame.K_DOWN, True, True),
            (cx - schritt, cy, th, "", pygame.K_LEFT, True, True),
            (cx + schritt, cy, th, "", pygame.K_RIGHT, True, True),
        ]

        # ---- Knoepfe rechts und oben ----
        ra = k * 0.105
        rb = k * 0.068
        rs = k * 0.048
        self.knoepfe = pfeile + [
            (b - m - ra, h - m - ra, ra, "A", pygame.K_SPACE, False, False),
            (b - m - ra * 2 - rb * 1.15, h - m - rb, rb, "OK",
             pygame.K_RETURN, False, False),
            (b - m - rb, h - m - ra * 2 - rb * 1.15, rb, "Lauf",
             pygame.K_LSHIFT, True, False),
            # Die obere Reihe sitzt tiefer, als sie muesste: ganz oben
            # liegen bei vielen Handys Kerbe und Statusleiste.
            (b - m - rs, m * 2 + rs, rs, "Menü", pygame.K_ESCAPE, False, False),
            (b - m - rs * 2.6, m * 2 + rs, rs, "Zeug", pygame.K_i, False, False),
            (b - m - rs * 4.2, m * 2 + rs, rs, "Uhr", pygame.K_u, False, False),
            (b - m - rs * 5.8, m * 2 + rs, rs, "Licht", pygame.K_t, False, False),
        ]
        self.schrift = pygame.font.Font(None, max(14, int(rs * 0.78)))
        self.ruhe = self._ruhebild()

    def _ruhebild(self):
        """Das unveraenderliche Bild der Bedienung - einmal gezeichnet,
        danach nur noch geblittet."""
        flaeche = pygame.Surface(self.groesse, pygame.SRCALPHA)
        for eintrag in self.knoepfe:
            self._malen(flaeche, eintrag, self.FUELLUNG, self.RAND)
        return flaeche.convert_alpha()

    def _malen(self, flaeche, eintrag, fuellung, strich):
        x, y, r, text, taste, _halten, eckig = eintrag
        if eckig:
            kasten = pygame.Rect(x - r, y - r, r * 2, r * 2)
            ecke = int(r * 0.28)
            if fuellung:
                pygame.draw.rect(flaeche, fuellung, kasten, border_radius=ecke)
            pygame.draw.rect(flaeche, strich, kasten, 3, border_radius=ecke)
            ax, ay = PFEILRICHTUNG[taste]
            self._pfeil(flaeche, x, y, ax, ay, r * 0.42, strich)
            return
        if fuellung:
            pygame.draw.circle(flaeche, fuellung, (x, y), r)
        pygame.draw.circle(flaeche, strich, (x, y), r, 3)
        if text:
            schrift = self.schrift.render(text, True, self.SCHRIFT)
            flaeche.blit(schrift, schrift.get_rect(center=(x, y)))

    @staticmethod
    def _pfeil(flaeche, x, y, ax, ay, gr, farbe):
        """Gleichschenkliges Dreieck, das in Richtung (ax, ay) zeigt."""
        px, py = -ay, ax
        pygame.draw.polygon(flaeche, farbe, [
            (x + ax * gr, y + ay * gr),
            (x - ax * gr + px * gr * 0.9, y - ay * gr + py * gr * 0.9),
            (x - ax * gr - px * gr * 0.9, y - ay * gr - py * gr * 0.9)])

    # --------------------------------------------------------------
    # Treffer
    # --------------------------------------------------------------
    def _zone(self, pos):
        """Welche Taste liegt unter dem Finger? None, wenn keine.

        Die Pfeiltasten bekommen einen unsichtbaren Rand von einer
        Viertel Tastenbreite: auf Glas trifft der Daumen selten genau,
        und ein Schritt, der nicht kommt, faellt mehr auf als einer,
        der eine Spur zu frueh kommt."""
        x, y = pos
        for eintrag in self.knoepfe:
            kx, ky, r, _text, taste, _halten, eckig = eintrag
            if eckig:
                rand = r * 1.25
                if abs(x - kx) <= rand and abs(y - ky) <= rand:
                    return taste
            elif (x - kx) ** 2 + (y - ky) ** 2 <= r * r:
                return taste
        return None

    def _haelt(self, taste):
        for _x, _y, _r, _text, t, halten, _eckig in self.knoepfe:
            if t == taste:
                return halten
        return False

    def _fingerpunkt(self, e):
        """Fingerereignisse kommen als Anteil der Fensterbreite."""
        return e.x * self.groesse[0], e.y * self.groesse[1]

    @staticmethod
    def _schicke(art, taste):
        pygame.event.post(pygame.event.Event(
            art, key=taste, mod=0, unicode="", scancode=0))

    # --------------------------------------------------------------
    # Ereignisse
    # --------------------------------------------------------------
    def ereignis(self, e):
        """True, wenn das Ereignis zur Bedienung gehoerte und der Rest
        des Spiels es nicht mehr sehen soll."""
        if not self.sichtbar or TASTATUR_OFFEN:
            return False
        if e.type == pygame.FINGERDOWN:
            return self._runter(e.finger_id, self._fingerpunkt(e))
        if e.type == pygame.FINGERMOTION:
            return self._bewegt(e.finger_id, self._fingerpunkt(e))
        if e.type == pygame.FINGERUP:
            return self._hoch(e.finger_id)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            return self._runter("maus", e.pos)
        if e.type == pygame.MOUSEMOTION and e.buttons[0]:
            return self._bewegt("maus", e.pos)
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            return self._hoch("maus")
        return False

    def _runter(self, fid, pos):
        taste = self._zone(pos)
        if taste is None:
            return False
        self.finger[fid] = taste
        self._schicke(pygame.KEYDOWN, taste)
        return True

    def _bewegt(self, fid, pos):
        """Von einer Pfeiltaste auf die naechste rutschen, ohne
        abzusetzen. Wer den Finger daneben zieht, laesst los."""
        alt = self.finger.get(fid)
        if alt is None:
            return False
        if not self._haelt(alt):
            return True               # A, OK, Menü: Wischen aendert nichts
        neu = self._zone(pos)
        if neu == alt:
            return True
        self._schicke(pygame.KEYUP, alt)
        if neu is None or not self._haelt(neu):
            del self.finger[fid]
            return True
        self.finger[fid] = neu
        self._schicke(pygame.KEYDOWN, neu)
        return True

    def _hoch(self, fid):
        alt = self.finger.pop(fid, None)
        if alt is None:
            return False
        self._schicke(pygame.KEYUP, alt)
        return True

    def tasten(self):
        """Die gerade gehaltenen Tasten - fuer tastenstand()."""
        return {t for t in self.finger.values() if self._haelt(t)}

    # --------------------------------------------------------------
    # Zeichnen
    # --------------------------------------------------------------
    def zeichne(self, flaeche):
        if not self.sichtbar or TASTATUR_OFFEN:
            return
        if flaeche.get_size() != self.groesse:
            self._aufbauen(flaeche.get_size())      # Fenster hat sich geaendert
        flaeche.blit(self.ruhe, (0, 0))

        gedrueckt = set(self.finger.values())
        if not gedrueckt:
            return
        for eintrag in self.knoepfe:
            if eintrag[4] in gedrueckt:
                self._malen(flaeche, eintrag, None, self.GEDRUECKT)


class _Tastenstand:
    """Sieht aus wie das Ergebnis von pygame.key.get_pressed(), zaehlt
    aber die gehaltenen Bildschirmtasten dazu."""

    def __init__(self, echt, dazu):
        self.echt = echt
        self.dazu = dazu

    def __getitem__(self, taste):
        return bool(self.echt[taste]) or taste in self.dazu


def tastenstand():
    return _Tastenstand(pygame.key.get_pressed(), touch.tasten())


def ereignisse():
    """Ersatz fuer pygame.event.get(): die Bedienung sieht jedes
    Ereignis zuerst und behaelt, was ihr gilt."""
    uebrig = []
    for e in pygame.event.get():
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F2:
            touch.sichtbar = not touch.sichtbar     # zum Ausprobieren
            continue
        # Die Zurueck-Taste des Handys wirkt wie Escape.
        if e.type in (pygame.KEYDOWN, pygame.KEYUP) and e.key == TASTE_ZURUECK:
            e = pygame.event.Event(e.type, key=pygame.K_ESCAPE, mod=0,
                                   unicode="", scancode=0)
        if touch.ereignis(e):
            continue
        uebrig.append(e)
    return uebrig


touch = Bildschirmsteuerung(anzeige)
_SKALIERT = None


def bild_zeigen():
    """Ersatz fuer pygame.display.flip(): rechnet das Spielbild aufs
    Display, legt die Bedienung darueber, zeigt beides."""
    global _SKALIERT
    if screen is not anzeige:
        b, h = anzeige.get_size()
        faktor = min(b / WIDTH, h / HEIGHT)
        ziel = (int(WIDTH * faktor), int(HEIGHT * faktor))
        if _SKALIERT is None or _SKALIERT.get_size() != ziel:
            _SKALIERT = pygame.Surface(ziel).convert()
            anzeige.fill((0, 0, 0))
        pygame.transform.scale(screen, ziel, _SKALIERT)
        anzeige.blit(_SKALIERT, ((b - ziel[0]) // 2, (h - ziel[1]) // 2))
    touch.zeichne(anzeige)
    pygame.display.flip()

pygame.display.set_caption("Spiel mit Menü und Sprite-Animation")

# Wird in main() gesetzt, damit der Vollbild-Zustand gespeichert werden kann.
SETTINGS = None


def ist_vollbild():
    flaeche = pygame.display.get_surface()
    return bool(flaeche and flaeche.get_flags() & pygame.FULLSCREEN)


def vollbild_umschalten():
    """Wechselt zwischen Fenster und Vollbild und merkt sich den Zustand."""
    if ANDROID:
        return True          # auf dem Handy ist ohnehin immer Vollbild
    try:
        pygame.display.toggle_fullscreen()
    except Exception as exc:
        print(f"Vollbild nicht moeglich: {exc}")
        return ist_vollbild()
    zustand = ist_vollbild()
    if SETTINGS is not None:
        SETTINGS.current_settings["fullscreen"] = zustand
        try:
            SETTINGS.save_settings()
        except Exception:
            pass
    return zustand


def vollbild_taste(event):
    """True, wenn dieses Ereignis die Vollbild-Taste war (F11 oder Alt+Enter).

    In jeder Schleife direkt nach der QUIT-Pruefung aufrufen und bei True
    mit continue weitermachen - sonst schluckt der normale Tastencode das F11.
    """
    if event.type != pygame.KEYDOWN:
        return False
    if event.key == pygame.K_F11:
        vollbild_umschalten()
        return True
    if event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
        vollbild_umschalten()
        return True
    return False


def get_inspect_text(player_pos, door_visible, door_open, is_at_door, dead=False):
    """Untersuchen-Text für Raum 1."""
    gx = int(player_pos[0] // INSPECT_GRID)
    gy = int(player_pos[1] // INSPECT_GRID)
    rnd = random.Random((gx * 73856093) ^ (gy * 19349663))

    if dead:
        return rnd.choice(ROOM1_DEAD_TEXTS)

    if door_visible and is_at_door:
        if door_open:
            return "Eine offene Tür. Dahinter: die Wahrheit? Geh einfach durch."
        return "Eine verschlossene Tür. Vielleicht öffnet die Leertaste sie."

    return rnd.choice(FLAVOR_TEXTS)


def get_world_inspect_text(world_pos, texts=FLAVOR_TEXTS):
    """Untersuchen-Text für die unendlichen Welten."""
    gx = int(world_pos[0] // INSPECT_GRID)
    gy = int(world_pos[1] // INSPECT_GRID)
    rnd = random.Random((gx * 83492791) ^ (gy * 2654435761))
    return rnd.choice(texts)


def validiere_gegenstände(eingabe, reihenfolge):
    """Prüft ob Gegenstände in richtiger Reihenfolge und Schreibweise eingegeben.
    
    Groß-/Kleinschreibung egal."""
    teile = [t.strip().lower() for t in eingabe.split(",")]
    
    if len(teile) != len(reihenfolge):
        return False
    
    for i, teil in enumerate(teile):
        if teil != reihenfolge[i].lower():
            return False
    
    return True


def scatter_positions(center, count, spread, min_dist, keep_out=300):
    """Erzeugt zufällige Positionen um ein Zentrum mit Mindestabständen."""
    positions = []
    attempts = 0
    while len(positions) < count and attempts < 8000:
        attempts += 1
        x = center[0] + random.randint(-spread, spread)
        y = center[1] + random.randint(-spread, spread)
        if abs(x - center[0]) < keep_out and abs(y - center[1]) < keep_out:
            continue
        too_close = False
        for p in positions:
            if abs(p[0] - x) < min_dist and abs(p[1] - y) < min_dist:
                too_close = True
                break
        if too_close:
            continue
        positions.append([x, y])
    # Notfall: fehlende Positionen einfach auffüllen
    while len(positions) < count:
        positions.append([center[0] + random.randint(-spread, spread),
                          center[1] + random.randint(-spread, spread)])
    return positions


def spawn_papers(start_pos):
    """Welt 2: verteilt die Rilke-Papiere."""
    positions = scatter_positions(start_pos, PAPER_COUNT, PAPER_SPREAD, PAPER_MIN_DIST)
    return [
        {"pos": pos, "poem": RILKE_GEDICHTE[i % len(RILKE_GEDICHTE)], "collected": False}
        for i, pos in enumerate(positions)
    ]


# ---------------------------------------------------------------
# Speichersystem: 6 Slots in saves.json
# ---------------------------------------------------------------
class SaveManager:
    SLOT_COUNT = 6

    def __init__(self, path="saves.json"):
        self.path = daten_pfad(path)

    def load_all(self):
        """Liste mit 6 Einträgen (dict oder None)."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        slots = [None] * self.SLOT_COUNT
        for i, s in enumerate(data[:self.SLOT_COUNT]):
            slots[i] = s
        return slots

    def save_slot(self, index, snapshot):
        slots = self.load_all()
        slots[index] = {
            "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "welt": WORLD_NAMES.get(snapshot.get("world_state", "room1"), "?"),
            "fortschritt": snapshot.get("fortschritt", ""),
            "state": snapshot,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(slots, f, ensure_ascii=False, indent=2)

    def load_slot(self, index):
        return self.load_all()[index]


class Settings:
    def __init__(self):
        self.settings_file = daten_pfad("settings.json")
        self.default_settings = {
            "fullscreen": False
        }
        self.current_settings = self.load_settings()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
            merged = self.default_settings.copy()
            merged.update(data)
            return merged
        except (FileNotFoundError, json.JSONDecodeError):
            return self.default_settings.copy()

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.current_settings, f, indent=2)


def _tueren_zuschneiden(geschlossen, offen):
    """Schneidet durchsichtige Raender weg und richtet beide Tuerbilder
    auf dieselbe Groesse aus, Unterkante buendig.

    Ohne das haengt die Tuer im Zimmer in der Luft: im urspruenglichen
    Blatt war jede Zelle 256 px hoch, die Tuer darin aber nur 172 px -
    die restlichen 84 px waren durchsichtig. Wer die Unterkante des
    Sprites auf den Boden setzt, setzt dann Luft auf den Boden.
    """
    zug = []
    for flaeche in (geschlossen, offen):
        r = flaeche.get_bounding_rect(min_alpha=1)
        zug.append(flaeche.subsurface(r).copy() if r.width and r.height
                   else flaeche.copy())
    breite = max(f.get_width() for f in zug)
    hoehe = max(f.get_height() for f in zug)
    ergebnis = []
    for f in zug:
        ziel = pygame.Surface((breite, hoehe), pygame.SRCALPHA)
        # mittig und unten buendig einsetzen
        ziel.blit(f, ((breite - f.get_width()) // 2, hoehe - f.get_height()))
        ergebnis.append(ziel.convert_alpha())
    return ergebnis[0], ergebnis[1]


def load_game_resources():
    try:
        background_image = pygame.image.load(os.path.join(image_dir, "background.png")).convert()
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

        sprite_sheet = pygame.image.load(os.path.join(image_dir, "player.png")).convert_alpha()
        sprite_size = (128, 128)
        player_sprites = {
            "down": [pygame.transform.scale(sprite_sheet.subsurface(pygame.Rect(x * sprite_size[0], 0, *sprite_size)), sprite_size) for x in range(4)],
            "left": [pygame.transform.scale(sprite_sheet.subsurface(pygame.Rect(x * sprite_size[0], 128, *sprite_size)), sprite_size) for x in range(4)],
            "right": [pygame.transform.scale(sprite_sheet.subsurface(pygame.Rect(x * sprite_size[0], 256, *sprite_size)), sprite_size) for x in range(4)],
            "up": [pygame.transform.scale(sprite_sheet.subsurface(pygame.Rect(x * sprite_size[0], 384, *sprite_size)), sprite_size) for x in range(4)],
        }

        door_sheet = pygame.image.load(os.path.join(image_dir, "Tür.png")).convert_alpha()
        # Das Blatt hat 4 Spalten und 2 Zeilen. Die Zellgroesse wird aus dem
        # Bild gelesen, nicht fest angenommen - so passen altes und neues
        # Blatt. Zelle (0,0) ist die geschlossene, (1,0) die offene Tuer.
        zelle_b = door_sheet.get_width() // 4
        zelle_h = door_sheet.get_height() // 2
        door_closed = door_sheet.subsurface(pygame.Rect(0, 0, zelle_b, zelle_h))
        door_open = door_sheet.subsurface(pygame.Rect(zelle_b, 0, zelle_b, zelle_h))
        door_closed, door_open = _tueren_zuschneiden(door_closed, door_open)
        if TUER_SKALIERUNG != 1.0:
            neu_gr = (int(door_closed.get_width() * TUER_SKALIERUNG),
                      int(door_closed.get_height() * TUER_SKALIERUNG))
            door_closed = pygame.transform.scale(door_closed, neu_gr)
            door_open = pygame.transform.scale(door_open, neu_gr)

        return background_image, player_sprites, (door_closed, door_open)

    except Exception as e:
        print(f"Fehler beim Laden der Spielressourcen: {e}")
        return None, None, None


def load_paper_sprite():
    """Lädt das Papier-Bild; Fallback: gezeichnetes weißes Blatt."""
    for name in ("Papier.png", "papier.png", "paper.png"):
        path = os.path.join(image_dir, name)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (64, 64))
            except pygame.error as e:
                print(f"Papier-Bild konnte nicht geladen werden: {e}")
    surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.rect(surf, WHITE, (10, 4, 44, 56))
    pygame.draw.rect(surf, GRAY, (10, 4, 44, 56), 2)
    for y in (16, 26, 36, 46):
        pygame.draw.line(surf, GRAY, (16, y), (48, y), 1)
    return surf


def lade_objekt_bilder():
    """Die sechs Objekte aus images/gegenstaende.png.

    Das Blatt hat 3 Spalten und 2 Zeilen in der Reihenfolge von
    WORLD_OBJECTS: oben Träne, Schuhe, Lampe - unten Glas, Batterien,
    Herz. Zu jedem Bild wird der Umriss der sichtbaren Pixel gemerkt;
    das ist die Hitbox zum Aufheben. Die leeren Ecken der Zelle zaehlen
    also nicht mit."""
    bilder, hitboxen = {}, {}
    pfad = os.path.join(image_dir, OBJEKT_BLATT)
    blatt = None
    if os.path.exists(pfad):
        try:
            blatt = pygame.image.load(pfad).convert_alpha()
        except pygame.error as fehler:
            print(f"{OBJEKT_BLATT} laesst sich nicht laden: {fehler}")
    else:
        print(f"BILD FEHLT: {OBJEKT_BLATT}")

    for nr in WORLD_OBJECTS:
        if blatt is not None:
            zb = blatt.get_width() // OBJEKT_SPALTEN
            zh = blatt.get_height() // OBJEKT_ZEILEN
            sp, ze = (nr - 1) % OBJEKT_SPALTEN, (nr - 1) // OBJEKT_SPALTEN
            zelle = blatt.subsurface(pygame.Rect(sp * zb, ze * zh, zb, zh))
            bild = pygame.transform.smoothscale(
                zelle, (OBJEKT_GROESSE, OBJEKT_GROESSE))
        else:
            bild = pygame.Surface((OBJEKT_GROESSE, OBJEKT_GROESSE),
                                  pygame.SRCALPHA)
            bild.fill((255, 0, 200))
        bilder[nr] = bild
        umriss = bild.get_bounding_rect()
        hitboxen[nr] = umriss if umriss.width > 2 else bild.get_rect()
    return bilder, hitboxen


def lade_frau_liegend():
    """Die tote Frau im Zimmer - images/Frau_liegend.png."""
    pfad = os.path.join(image_dir, "Frau_liegend.png")
    if os.path.exists(pfad):
        try:
            bild = pygame.image.load(pfad).convert_alpha()
            faktor = R1_FRAU_BREITE / max(1, bild.get_width())
            return pygame.transform.scale(
                bild, (R1_FRAU_BREITE, max(1, int(bild.get_height() * faktor))))
        except pygame.error as fehler:
            print(f"Frau_liegend.png laesst sich nicht laden: {fehler}")
    print("BILD FEHLT: Frau_liegend.png")
    ersatz = pygame.Surface((R1_FRAU_BREITE, R1_FRAU_BREITE // 3),
                            pygame.SRCALPHA)
    ersatz.fill((255, 0, 200))
    return ersatz


def lade_frau_sprites():
    """Sprite-Blatt der Frau, aufgebaut wie player.png.

    Vier Zeilen zu je vier Bildern: unten, links, rechts, oben.
    Fehlt die Datei, wird None zurueckgegeben und die alte
    Platzhalterfigur aus figuren.py benutzt."""
    for name in ("Frau.png", "frau.png"):
        pfad = os.path.join(image_dir, name)
        if not os.path.exists(pfad):
            continue
        try:
            blatt = pygame.image.load(pfad).convert_alpha()
        except pygame.error as fehler:
            print(f"Frau-Sprites konnten nicht geladen werden: {fehler}")
            continue
        zelle_b = blatt.get_width() // 4
        zelle_h = blatt.get_height() // 4

        def reihe(zeile):
            return [pygame.transform.scale(
                blatt.subsurface(pygame.Rect(spalte * zelle_b, zeile * zelle_h,
                                             zelle_b, zelle_h)), (128, 128))
                for spalte in range(4)]

        return {"down": reihe(0), "left": reihe(1),
                "right": reihe(2), "up": reihe(3)}
    return None


def load_stone_background():
    """Lädt background3.png (Steinwelt); Fallback: prozedurale Steintextur."""
    path = os.path.join(image_dir, "background3.png")
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert()
            return pygame.transform.scale(img, (WIDTH, HEIGHT))
        except pygame.error as e:
            print(f"Steinwelt-Bild konnte nicht geladen werden: {e}")
    # Prozedurale Steintextur (deterministisch, kachelt in sich)
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill((72, 72, 78))
    rnd = random.Random(42)
    for _ in range(420):
        x = rnd.randint(0, WIDTH)
        y = rnd.randint(0, HEIGHT)
        w = rnd.randint(20, 120)
        h = rnd.randint(15, 80)
        shade = rnd.randint(-18, 18)
        color = (max(0, min(255, 72 + shade)),
                 max(0, min(255, 72 + shade)),
                 max(0, min(255, 78 + shade)))
        pygame.draw.ellipse(surf, color, (x, y, w, h))
    for _ in range(120):
        x = rnd.randint(0, WIDTH)
        y = rnd.randint(0, HEIGHT)
        pygame.draw.line(surf, (55, 55, 60), (x, y),
                         (x + rnd.randint(-60, 60), y + rnd.randint(-60, 60)), 2)
    return surf


def load_watch_overlay():
    """Lädt Uhr.png; Fallback: gezeichnetes Handgelenk mit Armbanduhr."""
    for name in ("Uhr.png", "uhr.png", "watch.png"):
        path = os.path.join(image_dir, name)
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except pygame.error as e:
                print(f"Uhr-Bild konnte nicht geladen werden: {e}")
    return None


def draw_wrist_watch(surface, remaining_seconds, font_big, font_small, custom_overlay):
    """Zeichnet das Handgelenk mit der Uhr am unteren Bildschirmrand."""
    if custom_overlay is not None:
        rect = custom_overlay.get_rect(midbottom=(WIDTH // 2, HEIGHT))
        surface.blit(custom_overlay, rect)
        # Zeit auf das eigene Bild schreiben (mittig im unteren Drittel)
        mins = max(0, int(remaining_seconds)) // 60
        secs = max(0, int(remaining_seconds)) % 60
        t = font_big.render(f"{mins:02d}:{secs:02d}", True, (30, 200, 90))
        surface.blit(t, t.get_rect(center=(rect.centerx, rect.centery)))
        return

    # Fallback: Arm + Uhr zeichnen
    skin = (222, 178, 138)
    skin_dark = (190, 145, 105)
    arm_w = 260
    arm_x = WIDTH // 2 - arm_w // 2
    pygame.draw.rect(surface, skin, (arm_x, HEIGHT - 380, arm_w, 380), border_radius=60)
    pygame.draw.rect(surface, skin_dark, (arm_x, HEIGHT - 380, arm_w, 380), 4, border_radius=60)

    # Armband
    pygame.draw.rect(surface, (40, 40, 45), (arm_x - 10, HEIGHT - 300, arm_w + 20, 70), border_radius=18)

    # Ziffernblatt
    center = (WIDTH // 2, HEIGHT - 265)
    pygame.draw.circle(surface, (25, 25, 30), center, 95)
    pygame.draw.circle(surface, (200, 200, 210), center, 95, 5)
    pygame.draw.circle(surface, (15, 15, 18), center, 82)

    mins = max(0, int(remaining_seconds)) // 60
    secs = max(0, int(remaining_seconds)) % 60
    color = (30, 200, 90) if remaining_seconds > 60 else (220, 60, 60)
    t = font_big.render(f"{mins:02d}:{secs:02d}", True, color)
    surface.blit(t, t.get_rect(center=center))
    label = font_small.render("verbleibend", True, (120, 120, 130))
    surface.blit(label, label.get_rect(center=(center[0], center[1] + 34)))



# ---------------------------------------------------------------
# Highscore: Datum, Spielzeit, Spielfortschritt in Prozent
# ---------------------------------------------------------------
class HighscoreManager:
    MAX_EINTRAEGE = 10

    def __init__(self, path=daten_pfad("highscores.json")):
        self.path = path

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def add(self, prozent, spielzeit_sek, art):
        eintrag = {
            "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "zeit": int(spielzeit_sek),
            "prozent": int(prozent),
            "art": art,
        }
        eintraege = self.load()
        eintraege.append(eintrag)
        eintraege.sort(key=lambda e: (-e["prozent"], e["zeit"]))
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(eintraege[:self.MAX_EINTRAEGE], f, ensure_ascii=False, indent=2)
        return eintrag


def zeit_format(sekunden):
    m, s = divmod(int(sekunden), 60)
    return f"{m:02d}:{s:02d}"


def highscore_screen(hs_manager, neuester=None):
    """Highscore-Tabelle: Datum | Spielzeit | Fortschritt | Ergebnis."""
    font_title = pygame.font.Font(None, 72)
    font = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()
    eintraege = hs_manager.load()

    while True:
        for event in ereignisse():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if vollbild_taste(event):
                continue
            if event.type == pygame.KEYDOWN:
                return

        screen.fill((18, 18, 26))
        t = font_title.render("Highscore", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, 90)))

        kopf = font.render(f"{'Datum':<18}{'Spielzeit':<12}{'Fortschritt':<14}Ergebnis",
                           True, (150, 150, 160))
        screen.blit(kopf, (110, 180))
        pygame.draw.line(screen, (90, 90, 100), (110, 218), (WIDTH - 110, 218), 2)

        if not eintraege:
            leer = font.render("Noch keine Einträge.", True, (140, 140, 150))
            screen.blit(leer, leer.get_rect(center=(WIDTH // 2, 320)))

        for i, e in enumerate(eintraege):
            y = 240 + i * 52
            ist_neu = (neuester is not None
                       and e["datum"] == neuester["datum"]
                       and e["zeit"] == neuester["zeit"]
                       and e["prozent"] == neuester["prozent"])
            farbe = (120, 220, 160) if ist_neu else (225, 225, 230)
            zeile = (f"{e['datum']:<18}{zeit_format(e['zeit']):<12}"
                     f"{str(e['prozent']) + ' %':<14}{e['art']}")
            screen.blit(font.render(zeile, True, farbe), (110, y))

        hint = font_small.render("Beliebige Taste: zurück", True, (150, 150, 160))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 50)))
        bild_zeigen()
        clock.tick(30)


def mathe_ausdruck(n):
    """Kleine Rechenaufgabe, deren Ergebnis n ist (für Welt 5, Mathe-Modus)."""
    for f in (25, 20, 10, 5, 4, 2):
        if n % f == 0:
            if random.random() < 0.5:
                return f"({n // f} × {f})"
            return f"({n * 2} ÷ 2)"
    return str(n)


def richtung_aus_tasten(keys):
    """Pfeiltasten -> (dx, dy, Blickrichtung). Eine Richtung zur Zeit."""
    if keys[pygame.K_LEFT]:
        return -1, 0, "left"
    if keys[pygame.K_RIGHT]:
        return 1, 0, "right"
    if keys[pygame.K_UP]:
        return 0, -1, "up"
    if keys[pygame.K_DOWN]:
        return 0, 1, "down"
    return 0, 0, None


def game_loop(background_image, player_sprites, door_sprites,
              settings, hs_manager, load_state=None):
    clock = pygame.time.Clock()
    dialog = DialogSystem(screen, 840, 600)
    door_closed_sprite, door_open_sprite = door_sprites
    paper_sprite = load_paper_sprite()
    landschaft = Landschaft(image_dir)
    geister = Geister()
    moebel = Moebel(image_dir)
    frau_liegend = lade_frau_liegend()
    watch_overlay = load_watch_overlay()
    watch_font_big = pygame.font.Font(None, 54)
    watch_font_small = pygame.font.Font(None, 26)
    hud_font = pygame.font.Font(None, 40)
    ruf_font = pygame.font.Font(None, 110)   # Richtungsruf in Welt 3
    vers_font = pygame.font.Font(None, 40)   # Rilke-Wegweiser in Welt 3
    inv_font = pygame.font.Font(None, 42)
    inv_font_small = pygame.font.Font(None, 32)

    def lade_kachel(name, farbe):
        path = os.path.join(image_dir, name)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                return pygame.transform.scale(img, (WIDTH, HEIGHT))
            except pygame.error:
                pass
        t = pygame.Surface((WIDTH, HEIGHT))
        t.fill(farbe)
        for _ in range(180):
            x, y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)
            c = tuple(min(255, max(0, v + random.randint(-16, 16))) for v in farbe)
            pygame.draw.circle(t, c, (x, y), random.randint(2, 5))
        return t

    def toene(tile, farbe):
        t = tile.copy()
        ov = pygame.Surface((WIDTH, HEIGHT))
        ov.fill(farbe)
        t.blit(ov, (0, 0), special_flags=pygame.BLEND_MULT)
        return t

    # Waldreich, Erdreich und Labyrinth kommen aus landschaft.py -
    # hier bleiben nur die beiden Welten mit einfarbigem Untergrund.
    lava_tile = lade_kachel("lava.png", (150, 62, 34))
    himmel_tile = lade_kachel("himmel.png", (152, 190, 232))
    TILES = {"world5": lava_tile, "world6": himmel_tile}

    objekt_bilder, objekt_hitboxen = lade_objekt_bilder()

    frau_bilder = lade_frau_sprites()
    try:
        npc = NPC(frau_bilder) if frau_bilder else NPC(load_npc_sprites())
    except Exception as fehler:
        print(f"Frau-Sprites passen nicht zur NPC-Klasse: {fehler}")
        npc = NPC(load_npc_sprites())

    # ---------------- Spielzustand ----------------
    world_state = "room1"
    player_pos = [WIDTH // 2, HEIGHT // 2]
    world_pos = [0.0, 0.0]
    current_direction = "down"
    animation_index = 0.0
    walk_speed = 8
    sprint_speed = 16
    ausdauer = AUSDAUER_MAX    # Sprint-Kraft, siehe konfig.py
    sprint_gesperrt = False    # leer gesprintet -> Pause bis AUSDAUER_SPERRE
    steps_taken = 0
    play_time = 0.0
    inv_visible = False
    uhr_an = True              # U blendet die Uhr ein und aus
    zeige_hitboxen = False     # F1: Wand-Hitboxen zum Justieren einblenden
    taschenlampe = W4_LAMPE_START_AN   # T: nur im Labyrinth
    # Welt 6: welcher der drei Wege genommen wurde. Alle drei fuehren
    # zurueck ins Zimmer, aber nur bei "ja" ist dort niemand.
    w6_ausgang = None          # "ja", "jaein" oder "nein"
    frau_tot = False           # liegt sie im Zimmer?
    frau_gerettet = False      # hat er sich fuer sie entschieden?
    inspect_active = False
    w2_warte = 0.0             # Frau erst zeigen, dann fragen
    w4_warte = 0.0

    intro_fade = INTRO_FADE_DAUER   # Sekunden schwarz -> hell
    intro_stufe = 0            # 0: Kopfschmerzen, 1: Instruktionen, 2: fertig

    # Raum 1
    r1_stufe = 0               # 0: wartet auf 20 Schritte, dann Story
    door_visible = False
    door_open = False
    # Tuer: waagerecht mittig, Fuss auf der hinteren Bodenkante der Rueckwand
    # Die Tuer steht an der Rueckwand: Unterkante genau auf der Fluchtlinie.
    # Ist das Sprite hoeher als R1_TUER_MAX_HOEHE, wird nur der obere Teil
    # gezeichnet - die Tuer wird unten abgeschnitten und bleibt im Raum.
    tuer_hoehe = min(door_closed_sprite.get_height(), R1_TUER_MAX_HOEHE)
    door_pos = [WIDTH // 2 - door_closed_sprite.get_width() // 2 + R1_TUER_VERSATZ_X,
                R1_TUER_UNTEN - tuer_hoehe]
    door_target = None
    raum1_fertig = False
    fiebertraum = False        # Finale: zurück im Zimmer

    # Tipp-Finale am Computer: alle Objekte der Reihe nach aus dem
    # Gedaechtnis eintippen. Erst danach ist das Spiel gewonnen.
    finale_aktiv = False       # gerade wird getippt
    finale_index = 0           # welches Objekt abgefragt wird (0..5)
    finale_fehler = 0          # falsche Versuche insgesamt
    finale_richtig = []        # was schon korrekt eingetippt wurde
    finale_auftakt = False     # Hinweis "geh an den Computer" gezeigt
    finale_fertig = False      # alle Objekte richtig -> Sieg moeglich

    # Welt 2
    papers = []
    papers_collected = 0
    poem_paper = None
    w2_stufe = 0
    frau_aktiv = False

    # Welt 3
    w3_index = 0               # wie viele Punkte insgesamt geschafft
    w3_punkt = None            # Weltkoordinate des aktuellen Punkts
    w3_zeit = W3_ZEIT          # Gesamtuhr
    schwierigkeit = SCHWIERIGKEITEN[SCHWIERIGKEIT_STANDARD][0]
    zeit_faktor = SCHWIERIGKEITEN[SCHWIERIGKEIT_STANDARD][1]
    w2_zeit = W2_ZEIT          # Uhr im Waldreich - das Spiel ist ein Speedrun
    w2_laeuft = False
    w3_laeuft = False
    w3_vers_text = ""          # Rilke-Wegweiser im Erdreich
    w3_vers_zeit = 0.0
    w3_phase = 0               # welche der W3_PHASEN gerade laeuft
    w3_in_phase = 0            # wievielter Sammelpunkt dieser Phase
    w3_hetze = None            # Richtungsname waehrend der Hetze, sonst None
    w3_hetz_zeit = 0.0         # Restsekunden der Hetze
    w3_gegen = None            # Richtung des Gegenpunkts nach der Hetze
    w3_hetze_richtung = "oben"  # letzte Hetzrichtung, fuer den Gegenpunkt

    # Welt 4
    w4_stufe = 0
    w4_zeit = W4_ZEIT
    w4_laeuft = False
    w4_waende = []
    w4_zettel = []
    w4_gesammelt = 0
    w4_wegpunkte = []
    w4_wp_index = 0
    w4_zettel_offen = None
    w4_ziel_pos = [0, 0]       # Position der Tuer am Labyrinth-Ende
    w4_frau_wartet = 0.0       # Countdown, bis die Frau losläuft
    w4_frau_tempo = W4_FRAU_TEMPO   # ihr aktuelles Tempo, gleitet mit
    sprinting = False          # ob der Spieler gerade sprintet
    w4_rennen_aus = False      # True, sobald das Rennen entschieden ist

    # Welt 5
    w5_stufe = 0
    w5_mathe = False
    w5_tueren = 0
    w5_anweisung = ""

    # Welt 6 - REDESIGN
    w6_stufe = "fliehen"            # fliehen → dialog1 → folgen/suchen → eingabe → zusammenbruch
    w6_timer = 0.0
    w6_flucht_tempo = 6.0
    ewig_zettel = 0
    ewig_drop = 0.0
    w6_frau_distanz = 0.0           # Pixel-Distanz seit Weltstart
    w6_dialog_ausgeloest = False    # Dialog "Was willst du von mir?" schon gezeigt?
    w6_gegenstände_input = ""       # Eingabepuffer für Gegenstände
    w6_eingabe_aktiv = False        # Gerade am PC eingeben?
    w6_tueren = []                  # 7 Türen mit zufälliger Anordnung
    w6_frau_erreicht = False        # Hat Spieler Frau erreicht?
    w6_dunkel_raum = False          # Sind wir im dunklen Raum?
    
    # Gegenstände in chronologischer Reihenfolge
    GEGENSTÄNDE_REIHENFOLGE = ["träne", "schuhe", "lampe", "glas", "batterien", "herz"]

    # Türen (eine pro Welt aktiv), Objekte, Ende
    tuer = None                # {"open", "pos", "target"}
    belohnungen = []           # {"nr","name","pos","world","taken"}
    dead_aktiv = False
    dead_timer = 0.0
    gewonnen = False
    abschluss = None           # ("Highscore", eintrag) wenn das Spiel endet

    # ---------------- Helfer ----------------

    def nearest_item(items, reichweite=110):
        """Naechstes aufhebbares Ding.

        Gemessen wird vom Fusspunkt des Spielers zur Mitte des Sprites,
        nicht von Ecke zu Ecke - sonst muss man schraeg danebenstehen,
        damit es klappt."""
        fx, fy = spieler_fusspunkt()
        best, best_d = None, None
        for it in items:
            if it.get("collected") or it.get("taken"):
                continue
            dx = it["pos"][0] + 32 - fx
            dy = it["pos"][1] + 32 - fy
            d = dx * dx + dy * dy
            if d < reichweite * reichweite and (best_d is None or d < best_d):
                best, best_d = it, d
        return best

    def draw_infinite_background(camera, tile):
        tw, th = tile.get_size()
        sx = -(camera[0] % tw)
        sy = -(camera[1] % th)
        y = sy - th
        while y < HEIGHT:
            x = sx - tw
            while x < WIDTH:
                screen.blit(tile, (x, y))
                x += tw
            y += th

    def draw_hud(text, zeile=0):
        surf = hud_font.render(text, True, WHITE)
        rect = surf.get_rect(topleft=(24, 20 + zeile * 44))
        bg = pygame.Surface((rect.width + 24, rect.height + 12), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        screen.blit(bg, (rect.x - 12, rect.y - 6))
        screen.blit(surf, rect)

    def draw_bottom_timer(rest, gesamt, zusatz=""):
        """Timer am unteren Bildrand: Balken + Restzeit."""
        rest = max(0.0, rest)
        breite, hoehe = 520, 26
        x = WIDTH // 2 - breite // 2
        y = HEIGHT - 160    # ueber dem ggf. abgeschnittenen Fensterrand

        rahmen = pygame.Rect(x - 4, y - 4, breite + 8, hoehe + 8)
        bg = pygame.Surface((rahmen.width, rahmen.height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        screen.blit(bg, rahmen.topleft)

        anteil = max(0.0, min(1.0, rest / gesamt)) if gesamt > 0 else 0.0
        if anteil > 0.5:
            farbe = (110, 200, 120)
        elif anteil > 0.2:
            farbe = (225, 195, 90)
        else:
            farbe = (215, 85, 75)
        pygame.draw.rect(screen, (40, 40, 44), pygame.Rect(x, y, breite, hoehe))
        pygame.draw.rect(screen, farbe, pygame.Rect(x, y, int(breite * anteil), hoehe))
        pygame.draw.rect(screen, (200, 200, 205), pygame.Rect(x, y, breite, hoehe), 2)

        text = zeit_format(int(rest))
        if zusatz:
            text += "   " + zusatz
        surf = watch_font_small.render(text, True, WHITE)
        screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y + hoehe + 20)))

    def draw_ausdauer():
        """Gelber Kraftbalken rechts unten - sinkt beim Rennen."""
        breite, hoehe = 200, 14
        x = WIDTH - breite - 24
        # Deutlich ueber dem Fensterrand: bei 1024er Hoehe schneidet der
        # Windows-Desktop (Taskleiste + Titelzeile) sonst die unteren
        # Pixel ab und der Balken waere unsichtbar.
        y = HEIGHT - 140
        bg = pygame.Surface((breite + 12, hoehe + 12), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        screen.blit(bg, (x - 6, y - 6))
        anteil = ausdauer / AUSDAUER_MAX
        pygame.draw.rect(screen, (40, 40, 44), (x, y, breite, hoehe))
        pygame.draw.rect(screen, (240, 210, 90),
                         (x, y, int(breite * anteil), hoehe))
        # Rahmen: rot waehrend der Zwangspause, sonst hell
        rahmen = (225, 70, 60) if sprint_gesperrt else (200, 200, 205)
        pygame.draw.rect(screen, rahmen, (x, y, breite, hoehe), 2)

    def fortschritt_prozent():
        if gewonnen:
            return 100
        if world_state == "room1" and not raum1_fertig:
            return min(8, 2 + steps_taken // 4)
        if world_state == "world2":
            return int(10 + papers_collected / PAPER_COUNT * 20)
        if world_state == "world3":
            return int(30 + min(w3_index, W3_PUNKTE_GESAMT)
                       / W3_PUNKTE_GESAMT * 20)
        if world_state == "world4":
            return int(50 + min(w4_gesammelt, W4_ZETTEL_MIN) / W4_ZETTEL_MIN * 20)
        if world_state == "world5":
            return int(70 + w5_tueren / W5_TUEREN_ZIEL * 20)
        if world_state == "world6":
            return 90
        return 10

    def finish(art):
        nonlocal abschluss
        eintrag = hs_manager.add(fortschritt_prozent(), play_time, art)
        hs_manager.letzter = eintrag
        abschluss = "Highscore"

    def neustart():
        """Von vorne. game_loop gibt das an main() zurueck, und main
        startet einen frischen Durchgang."""
        nonlocal abschluss
        abschluss = "Neustart"

    def start_dead_end(text):
        nonlocal dead_aktiv, dead_timer, frau_aktiv, inspect_active
        dead_aktiv = True
        dead_timer = DEAD_END_DAUER
        frau_aktiv = False
        inspect_active = True
        dialog.show_dialog(text, ["..."])

    def r1_platz_vor_tuer():
        """Spieler 3 Schritte vor der Tuer, Fuesse auf dem Boden, Blick nach oben.
        Rutscht noetigenfalls nach vorn, falls die Stelle nicht begehbar ist."""
        fuss_hoehe = R1_HITBOX[1] + R1_HITBOX[3]
        x = door_pos[0] + door_closed_sprite.get_width() // 2 - R1_HITBOX[0] \
            - R1_HITBOX[2] // 2
        fuss_y = R1_BODEN_HINTEN_Y + R1_ABSTAND_SCHRITTE * R1_SCHRITT_PX
        pos = [x, fuss_y - fuss_hoehe]
        for _ in range(40):          # Notfall: Schritt fuer Schritt nach vorn
            if not r1_blockiert(pos):
                break
            pos[1] -= 8
        return pos

    def spawn_tuer(pos, target):
        nonlocal tuer
        frei = landschaft.frei_ruecken(world_state, list(pos), groesse=200)
        tuer = {"open": False, "target": target,
                "pos": [frei[0] - door_closed_sprite.get_width() // 2,
                        frei[1] - door_closed_sprite.get_height() // 2]}

    def spieler_fusspunkt():
        """Wo der Spieler steht - nicht wo sein Sprite anfaengt.

        Das Sprite ist 128x128 gross, die Fuesse sitzen unten in der
        Mitte. Alle Abstandsrechnungen gehen von diesem Punkt aus."""
        if world_state == "room1":
            hb = r1_hitbox(player_pos)
            return hb.centerx, hb.bottom
        return (world_pos[0] + R1_HITBOX[0] + R1_HITBOX[2] // 2,
                world_pos[1] + R1_HITBOX[1] + R1_HITBOX[3])

    def spawn_belohnung(nr, mitte, world):
        """mitte ist der gewuenschte MITTELPUNKT des Objekts."""
        frei = landschaft.frei_ruecken(world, list(mitte), groesse=140)
        belohnungen.append({"nr": nr, "name": WORLD_OBJECTS[nr],
                            "pos": [frei[0] - OBJEKT_GROESSE // 2,
                                    frei[1] - OBJEKT_GROESSE // 2],
                            "world": world, "taken": False})

    def belohnung_kasten(b):
        """Die sichtbaren Pixel des Objekts in Weltkoordinaten."""
        hb = objekt_hitboxen[b["nr"]]
        return pygame.Rect(b["pos"][0] + hb.x, b["pos"][1] + hb.y,
                           hb.width, hb.height)

    def belohnung_mitte(b):
        return belohnung_kasten(b).center

    def belohnung_in_reichweite():
        fx, fy = spieler_fusspunkt()
        for b in belohnungen:
            if b["taken"] or b["world"] != world_state:
                continue
            k = belohnung_kasten(b)
            dx = max(k.left - fx, fx - k.right, 0)
            dy = max(k.top - fy, fy - k.bottom, 0)
            if dx * dx + dy * dy < BELOHNUNG_REICHWEITE ** 2:
                return b
        return None

    def nimm_belohnung(b):
        nonlocal inspect_active
        b["taken"] = True
        inspect_active = True
        dialog.show_dialog(f"Objekt Welt {b['nr']} – {b['name']}\n\nAufgenommen.", ["OK"])

    def objekt_count(nr):
        return sum(1 for b in belohnungen if b["taken"] and b["nr"] == nr)

    def am_computer():
        """True, wenn der Spieler den Rechner bedienen kann.

        Entweder sitzt er im Platz zwischen Stuhl und Tisch, oder er
        steht dicht daneben. Blickrichtung immer nach unten - man schaut
        von hinten auf die Geraete herab."""
        if world_state != "room1":
            return False
        return moebel.am_computer(r1_hitbox(player_pos), current_direction)

    # ---------------- Tipp-Finale ----------------

    def _norm(s):
        """Vergleich gnaedig machen: Gross/klein, Umlaute, Zeichen egal."""
        s = s.strip().lower()
        for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
            s = s.replace(a, b)
        return "".join(c for c in s if c.isalnum())

    def finale_frage(kopf=None, farbe=FARBE_ZUKUNFTS_ICH):
        """Stellt die Frage nach dem naechsten Objekt."""
        nr = finale_index + 1
        gesamt = len(WORLD_OBJECTS)
        vorher = "   ".join(finale_richtig) if finale_richtig else "—"
        text = kopf if kopf else "Du sitzt am Computer.\n\nDer Cursor blinkt."
        dialog.show_input(
            f"{text}\n\n{nr}. Was hast du mitgenommen?",
            farbe=farbe,
            max_len=20,
            hinweis=f"{vorher}      ({nr}/{gesamt})",
        )

    def finale_starten():
        nonlocal finale_aktiv, finale_index, finale_fehler, finale_richtig
        nonlocal inspect_active
        # Wichtig: sonst schluckt die Untersuchen-Sperre spaeter das
        # abschliessende "..." und der Sieg wird nie ausgeloest.
        inspect_active = False
        finale_aktiv = True
        finale_index = 0
        finale_fehler = 0
        finale_richtig = []
        finale_frage()

    def finale_abbrechen():
        nonlocal finale_aktiv
        finale_aktiv = False

    def finale_pruefen(eingabe):
        """Wertet eine Eingabe aus und stellt die naechste Frage."""
        nonlocal finale_aktiv, finale_index, finale_fehler, finale_fertig

        if not eingabe:
            finale_frage()
            return

        erwartet = WORLD_OBJECTS[finale_index + 1]

        if _norm(eingabe) == _norm(erwartet):
            finale_richtig.append(erwartet)
            finale_index += 1
            if finale_index >= len(WORLD_OBJECTS):
                finale_aktiv = False
                finale_fertig = True
                dialog.show_poem(
                    "\n".join(finale_richtig) + "\n\nDas warst du.",
                    ["..."], farbe=FARBE_ZUKUNFTS_ICH)
                return
            finale_frage("Ja.")
            return

        finale_fehler += 1
        if finale_fehler >= FINALE_VERSUCHE:
            finale_aktiv = False
            start_dead_end("Der Bildschirm wird schwarz.\n\n"
                           "Du hast es vergessen.")
            return
        rest = FINALE_VERSUCHE - finale_fehler
        finale_frage(f"Nein.\n\nNoch {rest} Versuch{'e' if rest != 1 else ''}.",
                     farbe=FARBE_FEHLER)

    def frau_kasten():
        """Wo die liegende Frau im Zimmer liegt (Weltkoordinaten)."""
        breite = frau_liegend.get_width()
        hoehe = frau_liegend.get_height()
        return pygame.Rect(R1_FRAU_POS[0] - breite // 2,
                           R1_FRAU_POS[1] - hoehe, breite, hoehe)

    def an_frau():
        """True, wenn der Spieler dicht genug an ihr steht."""
        if world_state != "room1" or not frau_tot or frau_gerettet:
            return False
        fx, fy = spieler_fusspunkt()
        k = frau_kasten()
        dx = max(k.left - fx, fx - k.right, 0)
        dy = max(k.top - fy, fy - k.bottom, 0)
        return dx * dx + dy * dy < R1_FRAU_REICHWEITE ** 2

    def frau_ansprechen():
        """Der Dialog, der erst hier moeglich wird - nicht am Computer."""
        if w6_ausgang == "jaein":
            # Halbe Entscheidung, halbes Ergebnis: sie antwortet nicht mehr.
            dialog.show_dialog('"Wow, du willst mich retten?"\n\n'
                               'Ihre Stimme kommt von weit her.\n'
                               'Dann ist da nichts mehr.',
                               ["Zu spät"], farbe=FARBE_FRAU)
        else:
            dialog.show_dialog('"Wow, du willst mich retten?"',
                               ["Ja, ich helfe dir", "Nein, ich gehe"],
                               farbe=FARBE_FRAU)

    def an_tuer():
        if not tuer:
            return False
        ref = player_pos if world_state == "room1" else world_pos
        rect = pygame.Rect(tuer["pos"][0], tuer["pos"][1] + door_closed_sprite.get_height() - 80,
                           door_closed_sprite.get_width(), 110)
        return pygame.Rect(ref[0], ref[1], 64, 64).colliderect(rect)

    def tuer_durchgang(new_pos):
        """True = blockiert. Öffnet den Durchgang nach oben, Tür verschwindet danach."""
        nonlocal tuer
        if not tuer:
            return False
        rect = pygame.Rect(tuer["pos"][0] + 20, tuer["pos"][1],
                           door_closed_sprite.get_width() - 40,
                           door_closed_sprite.get_height() - 60)
        prect = pygame.Rect(new_pos[0], new_pos[1], 64, 64)
        if tuer["open"] and prect.colliderect(rect) and current_direction == "up":
            ziel = tuer["target"]
            tuer = None
            betrete_welt(ziel)
            return True
        return prect.colliderect(rect)

    # ---------------- Weltaufbau ----------------

    def baue_tunnel():
        """Welt 4: enges Labyrinth mit vielen Gassen, Zettel in den Sackgassen,
        Tuer am anderen Ende - dorthin geht der Wettlauf gegen die Frau."""
        nonlocal w4_waende, w4_zettel, w4_wegpunkte, w4_wp_index
        nonlocal w4_ziel_pos, w4_frau_wartet, w4_rennen_aus, w4_frau_tempo

        start_zelle = (0, W4_START_ZEILE)
        ziel_zelle = (W4_SPALTEN - 1, W4_START_ZEILE)

        verbunden, sackgassen = w4_erzeuge_labyrinth()
        w4_waende = w4_wand_rects(verbunden)

        # Der Weg, den die Frau nimmt - gleichzeitig ihre Wegweisung
        zellweg = w4_kuerzester_weg(verbunden, start_zelle, ziel_zelle)
        w4_wegpunkte = [w4_zell_mitte(cx, cy) for cx, cy in zellweg]
        w4_wp_index = 0
        w4_ziel_pos = w4_zell_mitte(*ziel_zelle)

        # ---- Die Tuer immer frei zugaenglich machen ----
        # Das Labyrinth wird gewuerfelt; je nach Wurf steht die Tuer in einer
        # engen Ecke oder wird von einem Wandstueck ueberdeckt. Deshalb wird
        # rund um die Zielzelle aufgeraeumt: alle Wandstuecke, die in den
        # Freiraum ragen, fallen weg. Es entsteht eine kleine Kammer vor der
        # Tuer. Der Weg dorthin bleibt Labyrinth.
        frei = pygame.Rect(
            w4_ziel_pos[0] - W4_TUER_FREIRAUM,
            w4_ziel_pos[1] - W4_TUER_FREIRAUM,
            W4_TUER_FREIRAUM * 2, W4_TUER_FREIRAUM * 2)
        vorher = len(w4_waende)
        w4_waende = [w for w in w4_waende if not frei.colliderect(w)]
        if vorher != len(w4_waende):
            print(f"Labyrinth: {vorher - len(w4_waende)} Wandstuecke vor der "
                  f"Tuer entfernt")

        # Zettel in Sackgassen legen: Umwege kosten Zeit
        woerter = W4_WOERTER.copy()
        random.shuffle(woerter)
        kandidaten = [z for z in sackgassen if z not in (start_zelle, ziel_zelle)]
        random.shuffle(kandidaten)
        if len(kandidaten) < len(woerter):
            # zu wenige Sackgassen: mit Zellen abseits des Wegs auffuellen
            abseits = [(cx, cy) for cx in range(W4_SPALTEN) for cy in range(W4_ZEILEN)
                       if (cx, cy) not in zellweg and (cx, cy) not in kandidaten]
            random.shuffle(abseits)
            kandidaten += abseits
        w4_zettel = []
        for wort, zelle in zip(woerter, kandidaten):
            mitte = w4_zell_mitte(*zelle)
            w4_zettel.append({"pos": [mitte[0] - 32, mitte[1] - 32],
                              "wort": wort, "collected": False})

        # Die Frau startet mit ein paar Zellen Vorsprung auf ihrem Weg
        vorsprung = min(W4_FRAU_VORSPRUNG, len(w4_wegpunkte) - 1)
        w4_wp_index = vorsprung
        start_wp = w4_wegpunkte[vorsprung]
        npc.pos = [float(start_wp[0] - 64), float(start_wp[1] - 64)]
        npc.direction = "right"
        w4_frau_wartet = W4_FRAU_VERZOEGERUNG
        w4_rennen_aus = False
        w4_frau_tempo = W4_FRAU_TEMPO

    # ---------------- Welt 3: Punkte, Hetze, Ende ----------------

    def w2_tuer_setzen():
        """Setzt die Tuer nach Welt 3 - immer im Bild und freistehend.

        Zwoelf Richtungen um den Spieler werden geprueft; genommen wird
        die, in der am wenigsten im Weg steht. Danach wird dort eine
        Lichtung geschlagen. Steht da ein grosser Baum, faellt er."""
        mitte = (world_pos[0] + 64, world_pos[1] + 120)
        kandidaten = []
        for i in range(12):
            w = math.tau * i / 12
            p = [mitte[0] + math.cos(w) * W2_TUER_ABSTAND,
                 mitte[1] + math.sin(w) * W2_TUER_ABSTAND]
            kasten = pygame.Rect(int(p[0]) - 120, int(p[1]) - 120, 240, 240)
            kandidaten.append((landschaft.belegung("world2", kasten), i, p))
        kandidaten.sort(key=lambda t: (t[0], t[1]))
        ziel = kandidaten[0][2]
        landschaft.lichtung("world2", ziel, W2_TUER_LICHTUNG)
        spawn_tuer(ziel, "world3")
        return ziel

    def w3_punkt_freimachen(p, mit_ring):
        """Macht einen Sammelpunkt erreichbar.

        Erst wird der Punkt selbst freigeraeumt - er soll nie in einem
        Felsen stecken. Bei normalen Punkten kommt danach ein weiter,
        offener Ring drumherum; bei Hetz- und Gegenpunkten nicht, dort
        ist die Zeit schon das Hindernis. Zum Schluss wird geprueft, ob
        man wirklich herankommt."""
        punkt = [float(p[0]), float(p[1])]
        landschaft.lichtung("world3", punkt, W3_PUNKT_FREI)
        if mit_ring:
            landschaft.nest_bauen("world3", punkt, W3_NEST_RADIUS,
                                  W3_NEST_STUECKE, W3_NEST_LUECKE,
                                  vorrat=landschaft.steine_gross)
        if not landschaft.erreichbar("world3", punkt):
            landschaft.lichtung("world3", punkt, W3_NEST_RADIUS + 80)
        return punkt

    def w3_vers_zeigen(richtung):
        """Rilke-Vers als Wegweiser einblenden."""
        nonlocal w3_vers_text, w3_vers_zeit
        w3_vers_text = w3_vers(richtung)
        w3_vers_zeit = W3_VERS_DAUER

    def w3_sammelpunkt():
        """Naechster Sammelpunkt - immer im Blickfeld.

        Der erste Punkt einer Phase liegt am Bildrand, jeder weitere
        rueckt naeher. Der Abstand bleibt unter der halben Bildbreite,
        damit der Punkt garantiert zu sehen ist.
        """
        anzahl = W3_PHASEN[w3_phase][1]
        if anzahl > 1:
            t = w3_in_phase / (anzahl - 1)
        else:
            t = 0.0
        d = W3_ABSTAND_MAX + (W3_ABSTAND_MIN - W3_ABSTAND_MAX) * t
        winkel = random.uniform(0, 6.283)
        fx, fy = spieler_fusspunkt()
        return w3_punkt_freimachen(
            [fx + math.cos(winkel) * d, fy + math.sin(winkel) * d], True)

    def w3_hetze_starten():
        """Richtung zurufen und den Punkt weit weg in diese Richtung legen.

        Die Ausdauer wird dabei aufgefuellt: die Hetze soll an Reaktion und
        Richtung haengen, nicht daran, ob man zwei Sekunden vorher zufaellig
        gesprintet ist. Willst du es haerter, nimm die beiden Zeilen raus.
        """
        nonlocal w3_hetze, w3_hetz_zeit, w3_punkt, ausdauer, sprint_gesperrt
        nonlocal w3_hetze_richtung, w3_vers_text, w3_vers_zeit
        ausdauer = AUSDAUER_MAX
        sprint_gesperrt = False
        w3_hetze = W3_PHASEN[w3_phase][0]
        w3_hetze_richtung = w3_hetze
        w3_hetz_zeit = W3_SPRINT_ZEIT * zeit_faktor
        (rx, ry), _ = W3_RICHTUNGEN[w3_hetze]
        fx, fy = spieler_fusspunkt()
        w3_punkt = w3_punkt_freimachen(
            [fx + rx * W3_SPRINT_DISTANZ, fy + ry * W3_SPRINT_DISTANZ], False)
        w3_vers_zeigen(w3_hetze)

    def w3_gegenpunkt_setzen():
        """Direkt nach der Hetze: der naechste Punkt liegt ausserhalb des
        Bildes, und zwar genau in der Gegenrichtung. Wer gerade nach oben
        gerannt ist, muss sofort wieder zurueck nach unten."""
        nonlocal w3_gegen, w3_punkt, w3_vers_text, w3_vers_zeit
        w3_gegen = w3_hetze_richtung
        (rx, ry), _ = W3_RICHTUNGEN[w3_gegen]
        fx, fy = spieler_fusspunkt()
        w3_punkt = w3_punkt_freimachen(
            [fx - rx * W3_GEGEN_DISTANZ, fy - ry * W3_GEGEN_DISTANZ], False)
        # Der Gegenpunkt liegt ausserhalb des Bildes. Der Vers ist der
        # einzige Hinweis, wohin man muss.
        w3_vers_zeigen(GEGENRICHTUNG[w3_gegen])

    def w3_ende():
        """Alle Punkte geschafft: Objekt und Tuer erscheinen."""
        nonlocal w3_punkt, w3_hetze, w3_gegen, inspect_active
        w3_punkt = None
        w3_hetze = None
        w3_gegen = None
        spawn_belohnung(3, [world_pos[0] + 170, world_pos[1] + 120], "world3")
        spawn_tuer([world_pos[0] + 32, world_pos[1] - 260], "world4")
        inspect_active = True
        dialog.show_dialog(
            f"{W3_PUNKTE_GESAMT} Punkte. Alle durch.\n\n"
            "Die Uhr läuft weiter, aber nicht mehr für dich.\n\n"
            "Vor dir erscheinen das Objekt dieser Welt\n"
            "und die Tür zu Welt 4.", ["Verstanden"])

    def w5_neue_anweisung():
        nonlocal w5_anweisung
        dx = random.choice([-1, 1]) * random.choice([800, 900, 1000, 1200, 1400])
        dy = random.choice([-1, 1]) * random.choice([300, 400, 500, 600, 800])
        ziel = [world_pos[0] + dx, world_pos[1] + dy]
        ostwest = "Osten" if dx > 0 else "Westen"
        nordsued = "Süden" if dy > 0 else "Norden"
        if w5_mathe:
            t1, t2 = mathe_ausdruck(abs(dx)), mathe_ausdruck(abs(dy))
        else:
            t1, t2 = str(abs(dx)), str(abs(dy))
        w5_anweisung = f"{t1} Schritte nach {ostwest}, {t2} nach {nordsued}."
        spawn_tuer(ziel, "world5_weiter")
        dialog.show_dialog(f'"Tür {w5_tueren + 1} von {W5_TUEREN_ZIEL}:\n'
                           f'{w5_anweisung}"', ["..."], farbe=FARBE_ZUKUNFTS_ICH)

    def betrete_welt(ziel):
        nonlocal world_state, world_pos, frau_aktiv, raum1_fertig, w6_stufe
        nonlocal w2_stufe, w4_stufe, w5_stufe, fiebertraum, inspect_active
        if ziel == "world5_weiter":
            # Zwischentür in der Lava-Welt
            zwischentuer_geschafft()
            return
        if ziel == "finale":
            # Zurück ins Zimmer: Was ein Fiebertraum.
            world_state = "room1"
            fiebertraum = True
            inspect_active = False
            player_pos[:] = [WIDTH // 2, HEIGHT // 2]
            if w6_ausgang in ("jaein", "nein"):
                nonlocal frau_tot
                frau_tot = True
                dialog.show_dialog('"Was ein Fiebertraum."\n\n'
                                   'Auf den Kacheln liegt jemand.', ["..."])
            else:
                dialog.show_dialog('"Was ein Fiebertraum."', ["..."])
            return
        world_state = ziel
        world_pos[:] = [0.0, 0.0]
        raum1_fertig = True
        if ziel == "world4":
            nonlocal taschenlampe
            taschenlampe = W4_LAMPE_START_AN
        if ziel == "world5":
            geister.zuruecksetzen()
        if ziel == "world2":
            nonlocal papers, w2_zeit, w2_laeuft
            papers = spawn_papers(world_pos)
            landschaft.nester_loeschen("world2")
            for blatt in papers:
                landschaft.frei_ruecken("world2", blatt["pos"])
                # Ring aus Baeumen und Staemmen drumherum - aber nur so
                # dicht, dass ein Weg hinein bleibt. Klappt das nicht,
                # wandert das Blatt und wir versuchen es noch einmal.
                for _ in range(4):
                    if landschaft.nest_bauen("world2", blatt["pos"]):
                        break
                    blatt["pos"][0] += 260
                    landschaft.frei_ruecken("world2", blatt["pos"])
            w2_zeit = W2_ZEIT * zeit_faktor
            w2_laeuft = True
            frau_aktiv = True
            w2_stufe = 1
            dialog.show_dialog("Waldreich.\n\nZwischen den Bäumen liegen Papiere.\n"
                               "Sammle alle 10.", ["Verstanden"])
        elif ziel == "world3":
            nonlocal w3_zeit
            w3_zeit = W3_ZEIT * zeit_faktor
            landschaft.nester_loeschen("world3")
            landschaft.lichtung("world3", (64, 120), W3_FREIRAUM)
            frau_aktiv = False
            dialog.show_dialog("Erdreich.\n\nSchwarze Punkte werden erscheinen. Lauf hinein.\n"
                               f"Es sind {W3_PUNKTE_GESAMT}.\n\n"
                               "Zwischendurch wird dir eine Richtung zugerufen.\n"
                               f"Dann hast du {W3_SPRINT_ZEIT * zeit_faktor:.1f} Sekunden. Renn.\n\n"
                               f"An deinem Handgelenk: eine Uhr. "
                               f"{int(w3_zeit // 60)}:{int(w3_zeit % 60):02d} Minuten.\n"
                               "(U blendet sie ein und aus)",
                               ["Verstanden"])
        elif ziel == "world4":
            nonlocal w4_zeit
            w4_zeit = W4_ZEIT * zeit_faktor
            baue_tunnel()
            frau_aktiv = True
            w4_stufe = 1
            dialog.show_dialog("Labyrinth.\n\nEnge Gassen, überall Abzweigungen.\n"
                               "Am anderen Ende: eine Tür.\n\n"
                               "Die Frau kennt den Weg. Sie läuft ihn auch.\n"
                               "Sei vor ihr da.\n\n"
                               "Jedes Wort, das du aufhebst,\n"
                               "lässt sie kurz innehalten.",
                               ["Verstanden"])
        elif ziel == "world5":
            frau_aktiv = False
            w5_stufe = 1
            dialog.show_dialog('"Du hast\'s doch gemacht. Dacht ich mir..."',
                               ["Halt doch einfach dein Maul!", "Ok"],
                               farbe=FARBE_ZUKUNFTS_ICH)
        elif ziel == "world6":
            papers = []
            frau_aktiv = True
            w6_stufe = "fliehen"
            w6_frau_distanz = 0.0
            w6_dialog_ausgeloest = False
            # Frau startet weit oben
            npc.pos = [world_pos[0], world_pos[1] - 500]
            dialog.show_dialog("Eine endlose Himmelwelt.\n\nSie ist hier.\n\n"
                               "Vor dir... sie.",
                               ["..."])
        elif ziel == "room1_w6_ende":
            # Nach "Was suchst du hier?" → Room 1 mit toter Frau
            world_state = "room1"
            frau_tot = True
            w6_stufe = "eingabe"
            player_pos[:] = [WIDTH // 2, HEIGHT // 2]
            dialog.show_dialog(
                'Die tote Frau liegt auf dem Boden.\n\n'
                'Ihr Blick starrt dich an.\n\n'
                'Am Computer wartet dein Zukunfts-Ich.',
                ["Zum PC"]
            )
        elif ziel == "w6_dunkel":
            # Dunkler Raum - falsche Tür
            w6_dunkel_raum = True
            w6_stufe = "dunkel_raum"
            start_dead_end("Das war wohl nichts.")

    def zwischentuer_geschafft():
        nonlocal w5_tueren
        w5_tueren += 1
        if w5_tueren >= W5_TUEREN_ZIEL:
            spawn_belohnung(5, [world_pos[0] + 170, world_pos[1] + 120], "world5")
            spawn_tuer([world_pos[0] + 32, world_pos[1] - 260], "world6")
            dialog.show_dialog(f"Das war Tür {W5_TUEREN_ZIEL} von {W5_TUEREN_ZIEL}.\n\n"
                               "Vor dir: das Objekt dieser Welt und die letzte Tür.",
                               ["Verstanden"])
        else:
            w5_neue_anweisung()

    # ---------------- Speichern & Laden ----------------

    def build_snapshot():
        return {
            "world_state": world_state,
            "fortschritt": f"{fortschritt_prozent()} %",
            "player_pos": player_pos,
            "world_pos": world_pos,
            "steps_taken": steps_taken,
            "play_time": play_time,
            "intro_fade": intro_fade, "intro_stufe": intro_stufe,
            "r1_stufe": r1_stufe, "door_visible": door_visible,
            "door_open": door_open, "door_target": door_target,
            "raum1_fertig": raum1_fertig, "fiebertraum": fiebertraum,
            "papers": papers, "papers_collected": papers_collected,
            "w2_stufe": w2_stufe, "frau_aktiv": frau_aktiv,
            "schwierigkeit": schwierigkeit, "zeit_faktor": zeit_faktor,
            "w2_zeit": w2_zeit, "w2_laeuft": w2_laeuft,
            "w3_index": w3_index, "w3_punkt": w3_punkt,
            "w3_vers_text": w3_vers_text, "w3_vers_zeit": w3_vers_zeit,
            "w3_zeit": w3_zeit, "w3_laeuft": w3_laeuft,
            "w3_phase": w3_phase, "w3_in_phase": w3_in_phase,
            "w3_hetze": w3_hetze, "w3_hetz_zeit": w3_hetz_zeit,
            "w3_gegen": w3_gegen,
            "w4_stufe": w4_stufe, "w4_zeit": w4_zeit, "w4_laeuft": w4_laeuft,
            "w4_waende": [list(r) for r in w4_waende],
            "w4_zettel": w4_zettel, "w4_gesammelt": w4_gesammelt,
            "w4_wegpunkte": w4_wegpunkte, "w4_wp_index": w4_wp_index,
            "w4_ziel_pos": w4_ziel_pos, "w4_frau_wartet": w4_frau_wartet,
            "w4_rennen_aus": w4_rennen_aus, "ausdauer": ausdauer,
            "w5_stufe": w5_stufe, "w5_mathe": w5_mathe,
            "w5_tueren": w5_tueren, "w5_anweisung": w5_anweisung,
            "w6_ausgang": w6_ausgang, "frau_tot": frau_tot,
            "frau_gerettet": frau_gerettet,
            "w6_stufe": w6_stufe, "w6_timer": w6_timer,
            "w6_flucht_tempo": w6_flucht_tempo,
            "ewig_zettel": ewig_zettel,
            "tuer": tuer, "belohnungen": belohnungen,
            "dead_aktiv": dead_aktiv, "dead_timer": dead_timer,
            "finale_index": finale_index, "finale_fehler": finale_fehler,
            "finale_richtig": finale_richtig, "finale_auftakt": finale_auftakt,
            "finale_fertig": finale_fertig,
            "npc": npc.to_dict(),
        }

    def apply_load_state(s):
        nonlocal world_state, player_pos, world_pos, steps_taken, play_time
        nonlocal intro_fade, intro_stufe, r1_stufe, door_visible, door_open
        nonlocal door_target, raum1_fertig, fiebertraum, papers, papers_collected
        nonlocal w2_stufe, frau_aktiv, w3_index, w3_punkt, w3_zeit, w3_laeuft
        nonlocal w2_zeit, w2_laeuft, schwierigkeit, zeit_faktor
        nonlocal w3_vers_text, w3_vers_zeit
        nonlocal w3_phase, w3_in_phase, w3_hetze, w3_hetz_zeit, w3_gegen
        nonlocal w4_stufe, w4_zeit, w4_laeuft, w4_waende, w4_zettel, w4_gesammelt
        nonlocal w4_wegpunkte, w4_wp_index, w5_stufe, w5_mathe, w5_tueren
        nonlocal w4_ziel_pos, w4_frau_wartet, w4_rennen_aus
        nonlocal ausdauer, sprint_gesperrt
        nonlocal w5_anweisung, w6_stufe, w6_timer, w6_flucht_tempo, ewig_zettel
        nonlocal w6_ausgang, frau_tot, frau_gerettet
        nonlocal tuer, belohnungen, dead_aktiv, dead_timer
        nonlocal finale_aktiv, finale_index, finale_fehler
        nonlocal finale_richtig, finale_auftakt, finale_fertig
        finale_aktiv = False       # nach dem Laden wird nicht mitten im Tippen fortgesetzt
        finale_index = s.get("finale_index", 0)
        finale_fehler = s.get("finale_fehler", 0)
        finale_richtig = list(s.get("finale_richtig", []))
        finale_auftakt = s.get("finale_auftakt", False)
        finale_fertig = s.get("finale_fertig", False)
        world_state = s.get("world_state", "room1")
        player_pos = list(s.get("player_pos", player_pos))
        world_pos = [float(v) for v in s.get("world_pos", [0.0, 0.0])]
        steps_taken = s.get("steps_taken", 0)
        play_time = float(s.get("play_time", 0.0))
        intro_fade = float(s.get("intro_fade", 0.0))
        intro_stufe = s.get("intro_stufe", 2)
        r1_stufe = s.get("r1_stufe", 0)
        door_visible = s.get("door_visible", False)
        door_open = s.get("door_open", False)
        door_target = s.get("door_target")
        raum1_fertig = s.get("raum1_fertig", False)
        fiebertraum = s.get("fiebertraum", False)
        papers = s.get("papers", [])
        papers_collected = s.get("papers_collected", 0)
        w2_stufe = s.get("w2_stufe", 0)
        frau_aktiv = s.get("frau_aktiv", False)
        schwierigkeit = s.get("schwierigkeit", schwierigkeit)
        zeit_faktor = float(s.get("zeit_faktor", 1.0))
        w2_zeit = s.get("w2_zeit", W2_ZEIT)
        w2_laeuft = s.get("w2_laeuft", False)
        w3_index = s.get("w3_index", 0)
        w3_vers_text = s.get("w3_vers_text", "")
        w3_vers_zeit = float(s.get("w3_vers_zeit", 0.0))
        w3_punkt = s.get("w3_punkt")
        w3_zeit = float(s.get("w3_zeit", W3_ZEIT))
        w3_laeuft = s.get("w3_laeuft", False)
        w3_phase = s.get("w3_phase", 0)
        w3_in_phase = s.get("w3_in_phase", 0)
        # Eine laufende Hetze wird nicht fortgesetzt - sonst startet man
        # nach dem Laden mit halber Sekunde Restzeit.
        w3_hetze = None
        w3_hetz_zeit = 0.0
        w3_gegen = s.get("w3_gegen")
        w4_stufe = s.get("w4_stufe", 0)
        w4_zeit = float(s.get("w4_zeit", W4_ZEIT))
        w4_laeuft = s.get("w4_laeuft", False)
        w4_waende = [pygame.Rect(r) for r in s.get("w4_waende", [])]
        w4_zettel = s.get("w4_zettel", [])
        w4_gesammelt = s.get("w4_gesammelt", 0)
        w4_wegpunkte = s.get("w4_wegpunkte", [])
        w4_wp_index = s.get("w4_wp_index", 0)
        w4_ziel_pos = s.get("w4_ziel_pos", [0, 0])
        w4_frau_wartet = float(s.get("w4_frau_wartet", 0.0))
        w4_rennen_aus = s.get("w4_rennen_aus", False)
        ausdauer = float(s.get("ausdauer", AUSDAUER_MAX))
        sprint_gesperrt = False
        w5_stufe = s.get("w5_stufe", 0)
        w5_mathe = s.get("w5_mathe", False)
        w5_tueren = s.get("w5_tueren", 0)
        w5_anweisung = s.get("w5_anweisung", "")
        w6_stufe = s.get("w6_stufe", "start")
        w6_ausgang = s.get("w6_ausgang")
        frau_tot = s.get("frau_tot", False)
        frau_gerettet = s.get("frau_gerettet", False)
        w6_timer = float(s.get("w6_timer", 0.0))
        w6_flucht_tempo = float(s.get("w6_flucht_tempo", 6.0))
        ewig_zettel = s.get("ewig_zettel", 0)
        tuer = s.get("tuer")
        belohnungen[:] = s.get("belohnungen", [])
        dead_aktiv = s.get("dead_aktiv", False)
        dead_timer = float(s.get("dead_timer", 0.0))
        npc.from_dict(s.get("npc", {}))

    # ---------------- Inventar ----------------

    def draw_inventory():
        zeilen = [f"Blätter (Waldreich): {papers_collected} von {PAPER_COUNT}",
                  f"Zettel (Tunnel): {w4_gesammelt} von {len(W4_WOERTER)}"]
        if ewig_zettel:
            zeilen.append(f"Rilke-Zettel (Ewigkeit): {ewig_zettel}")
        gefunden = [b for b in belohnungen if b["taken"]]
        obj = [f"Objekt Welt {b['nr']} – {b['name']}" for b in gefunden] \
            or ["– noch keine –"]
        hoehe = min(HEIGHT - 60, 190 + (len(zeilen) + len(obj)) * 38)
        panel = pygame.Surface((620, hoehe), pygame.SRCALPHA)
        panel.fill((15, 15, 22, 228))
        pygame.draw.rect(panel, (120, 220, 160), panel.get_rect(), 3, border_radius=12)
        y = 22
        panel.blit(inv_font.render("Inventar", True, (240, 240, 240)), (26, y)); y += 52
        for z in zeilen:
            panel.blit(inv_font_small.render(z, True, (200, 230, 205)), (26, y)); y += 38
        y += 10
        panel.blit(inv_font.render("Objekte", True, (240, 240, 240)), (26, y)); y += 48
        klein = OBJEKT_GROESSE // 2
        for i, z in enumerate(obj):
            farbe = (235, 210, 140) if z != "– noch keine –" else (140, 140, 150)
            if i < len(gefunden):
                panel.blit(pygame.transform.smoothscale(
                    objekt_bilder[gefunden[i]["nr"]], (klein, klein)),
                    (24, y - 4))
            panel.blit(inv_font_small.render(z, True, farbe),
                       (26 + klein + 8 if i < len(gefunden) else 26, y))
            y += 38
        screen.blit(panel, ((WIDTH - 620) // 2, (HEIGHT - hoehe) // 2))

    # ---------------- Dialog-Verarbeitung ----------------

    def spawn_w6_tueren():
        """7 Türen mit zufälliger Anordnung spawnen."""
        nonlocal w6_tueren
        
        # Eine richtige Tür (führt zu neuem Level), 6 falsche (dunkler Raum)
        tueren_art = ["richtig"] + ["falsch"] * 6
        random.shuffle(tueren_art)
        
        # Nebeneinander anordnen (ca. 100px Abstand)
        base_x = world_pos[0] - 300
        spacing = 100
        
        w6_tueren = []
        for i, art in enumerate(tueren_art):
            pos = [base_x + i * spacing, world_pos[1] - 260]
            w6_tueren.append({
                "pos": pos,
                "art": art,  # "richtig" oder "falsch"
                "index": i
            })
            target = "world2" if art == "richtig" else "w6_dunkel"
            spawn_tuer(pos, target)

    def handle_dialog(result):
        nonlocal inspect_active, poem_paper, papers_collected, r1_stufe
        nonlocal w2_warte, w4_warte
        nonlocal door_visible, door_target, w2_stufe, w3_laeuft, w4_stufe
        nonlocal w4_laeuft, w4_gesammelt, w4_zettel_offen, w5_stufe, w5_mathe
        nonlocal w4_frau_wartet, w4_rennen_aus
        nonlocal w6_stufe, w6_timer, w6_flucht_tempo, frau_aktiv, gewonnen
        nonlocal w6_ausgang, frau_tot, frau_gerettet
        nonlocal player_pos, current_direction, intro_stufe
        nonlocal finale_auftakt
        nonlocal w6_frau_distanz, w6_dialog_ausgeloest, w6_frau_erreicht, w6_tueren

        # ---- Eingaben (Tupel): Finale UND W6 ----
        # Muss ganz oben stehen, sonst schluckt die Untersuchen-Sperre sie.
        if isinstance(result, tuple):
            art, text = result
            if art == "ABBRUCH":
                if world_state == "room1" and w6_stufe == "eingabe":
                    # W6 Abbruch
                    dialog.show_dialog(
                        '"Tja, ich habs dir gesagt."',
                        ["Jow und ich wollte nicht hören"],
                        farbe=FARBE_ZUKUNFTS_ICH
                    )
                    return "continue_dialog"
                else:
                    # Finale Abbruch
                    finale_abbrechen()
                    return None
            if art == "EINGABE":
                if world_state == "room1" and w6_stufe == "eingabe":
                    # W6 Eingabe
                    if validiere_gegenstände(text, GEGENSTÄNDE_REIHENFOLGE):
                        # RICHTIG!
                        dialog.show_dialog(
                            "Alle Namen stimmen.\n\n"
                            "Ein merkwürdiges Labyrinth, indem man viele trifft.\n"
                            "In jeder Geschichte gibt es einen Guten und einen Bösen.\n"
                            "Ein ewig währender Kampf im Inneren wie Außen.\n\n"
                            "Sich benehmen: Ich bin und du bist.",
                            ["Verstanden"]
                        )
                        gewonnen = True
                        return "continue_dialog"
                    else:
                        # FALSCH!
                        dialog.show_dialog(
                            '"Tja, ich habs dir gesagt."',
                            ["Ja und ich hab nicht zugehört"],
                            farbe=FARBE_ZUKUNFTS_ICH
                        )
                        return "continue_dialog"
                else:
                    # Finale Eingabe
                    finale_pruefen(text)
                    return "continue_dialog"
            return None

        # Intro
        if intro_stufe == 0 and result == "...":
            intro_stufe = 1
            dialog.show_dialog(
                "Steuerung\n\n"
                "Pfeiltasten: Bewegen\n"
                "Shift halten: Sprinten\n"
                "Leertaste: Untersuchen, Aufheben, Türen öffnen\n"
                "I: Inventar öffnen und schließen\n"
                "F11: Vollbild an und aus\n"
                "ESC: Hauptmenü – dort kannst du speichern",
                ["Verstanden"])
            return "continue_dialog"
        if intro_stufe == 1 and result == "Verstanden":
            intro_stufe = 2
            return None

        # Untersuchen / Objekte
        if inspect_active:
            inspect_active = False
            if dead_aktiv or result not in ("OK", "...", "Verstanden"):
                pass
            return None

        # Welt 2: Gedicht-Papier
        if poem_paper is not None:
            p = poem_paper
            poem_paper = None
            if result == "Aufsammeln":
                p["collected"] = True
                papers_collected += 1
            return None

        # Welt 4: Zettel
        if w4_zettel_offen is not None:
            z = w4_zettel_offen
            w4_zettel_offen = None
            if result == "Aufsammeln":
                z["collected"] = True
                w4_gesammelt += 1
                # Jedes aufgehobene Wort laesst die Frau kurz innehalten
                if w4_laeuft and not w4_rennen_aus:
                    w4_frau_wartet += W4_ZETTEL_STOPP
            return None

        # ---- Raum 1: Zukunfts-Ich ----
        if result == "Ignorieren":
            start_dead_end('Du ignorierst die Stimme.\n\nSie sagt nichts mehr.\n'
                           'Niemand sagt mehr etwas.')
            return "continue_dialog"
        if result == "Mit was?":
            dialog.show_dialog('"Mit dem, was du tust. Lass es einfach.\n'
                               'Bleib liegen und ruf……"',
                               ["Was? Wen soll ich rufen?!", "Ach, der hat doch keine Ahnung"],
                               farbe=FARBE_ZUKUNFTS_ICH)
            return "continue_dialog"
        if result == "Ach, der hat doch keine Ahnung":
            door_visible = True
            door_target = "world3"
            player_pos = r1_platz_vor_tuer()
            current_direction = "up"
            spawn_belohnung(1, R1_OBJEKT_1, "room1")
            spawn_belohnung(2, R1_OBJEKT_2, "room1")
            spawn_tuer([door_pos[0] + door_closed_sprite.get_width() // 2,
                        door_pos[1] + tuer_hoehe // 2], "world3")
            return None
        if result == "Was? Wen soll ich rufen?!":
            door_visible = True
            door_target = "world2"
            player_pos = r1_platz_vor_tuer()
            current_direction = "up"
            spawn_belohnung(1, R1_OBJEKT_1, "room1")
            spawn_tuer([door_pos[0] + door_closed_sprite.get_width() // 2,
                        door_pos[1] + tuer_hoehe // 2], "world2")
            return None

        # ---- Welt 2: Frau & Zukunfts-Ich ----
        if w2_stufe == 1 and result == "Verstanden":
            # Erst erscheint die Frau sichtbar neben dem Spieler ...
            w2_stufe = 2
            w2_warte = 2.0
            npc.pos = [world_pos[0] + 210, world_pos[1] - 170]
            npc.signal_timer = NPC_SIGNAL_INTERVALL  # Pfeil sofort
            return None
        if w2_stufe == 3 and result == "...":
            w2_stufe = 4
            dialog.show_dialog('"Mach das nicht. Sonst ......."', ["..."],
                               farbe=FARBE_ZUKUNFTS_ICH)
            return "continue_dialog"

        # ---- Welt 4: Tunnel ----
        if w4_stufe == 1 and result == "Verstanden":
            # Die Frau steht sichtbar am Tunnelanfang; erst kurz zeigen, dann fragen
            w4_stufe = 2
            w4_warte = 2.0
            return None
        if w4_stufe == 3 and result == "...":
            w4_stufe = 4
            dialog.show_dialog('"Hör zu. Noch bist du nicht zu tief drin.\n'
                               'Fang an aufzuhören..."',
                               ["Wie?", "Kann der endlich mal die Schnauze halten??"],
                               farbe=FARBE_ZUKUNFTS_ICH)
            return "continue_dialog"
        if result == "Wie?":
            for z in w4_zettel:
                if z["wort"] in ("Ich", "Du", "Er") and not z["collected"] and w4_gesammelt < 3:
                    z["collected"] = True
                    w4_gesammelt += 1
            dialog.show_dialog('"Nimm die hier. Ich, Du, Er.\n'
                               'Ein Anfang.\n\nUnd jetzt: Lauf."', ["Lauf"],
                               farbe=FARBE_ZUKUNFTS_ICH)
            return "continue_dialog"
        if result == "Kann der endlich mal die Schnauze halten??":
            dialog.show_dialog('"…\n\nLauf."', ["Lauf"], farbe=FARBE_ZUKUNFTS_ICH)
            return "continue_dialog"
        if result == "Lauf":
            w4_laeuft = True
            return None

        # ---- Welt 5: Lava ----
        if result == "Halt doch einfach dein Maul!":
            w5_mathe = True
            dialog.show_dialog('"Bloß nicht so frech. Ich muss dich hier\n'
                               'durchführen, weil ....\n\nWeißt du was? Rechne selbst."',
                               ["Meinetwegen"], farbe=FARBE_ZUKUNFTS_ICH)
            return "continue_dialog"
        if result == "Ok":
            w5_mathe = False
            dialog.show_dialog('"Okay, super. Ich bring dich hier raus.\n'
                               'Irgendwie bin ....\n\nEgal. Hör einfach zu."',
                               ["Meinetwegen"], farbe=FARBE_ZUKUNFTS_ICH)
            return "continue_dialog"
        if result == "Meinetwegen":
            w5_neue_anweisung()
            return "continue_dialog"

        # ---- Welt 6: Entscheidungen ----
        if result == "leben":
            w6_stufe = "verfolgung"
            w6_timer = 120.0
            frau_aktiv = True
            npc.pos = [world_pos[0] + 500, world_pos[1] - 300]
            return None
        if result == "Leben":
            dialog.show_dialog('"Sicher?"', ["Ja", "Jaein", "Nein"])
            return "continue_dialog"
        if result in ("Ja", "Jaein", "Nein"):
            # Alle drei Antworten fuehren zurueck ins Zimmer. Nur bei "Ja"
            # ist dort niemand; sonst liegt sie da.
            w6_ausgang = {"Ja": "ja", "Jaein": "jaein", "Nein": "nein"}[result]
            spawn_belohnung(6, [world_pos[0] + 170, world_pos[1] + 120], "world6")
            spawn_tuer([world_pos[0] + 32, world_pos[1] - 260], "finale")
            return None
        if result == "Keine Ahnung":
            frau_aktiv = False
            start_dead_end('Die Frau:\n\n"Okay, dann lass mich in Ruhe, du Weirdo!"\n\n'
                           'Sie ist fort.')
            return "continue_dialog"
        if result == "Wie heißt du?":
            w6_stufe = "flucht"
            w6_timer = 30.0
            w6_flucht_tempo = 8.0
            dialog.show_dialog('"Ich hab dich als Erstes gefragt."', ["..."],
                               farbe=FARBE_FRAU)
            return "continue_dialog"
        if result == "Hinterher?":
            w6_stufe = "ewigkeit"
            w6_timer = W6_EWIGKEIT * zeit_faktor
            return None
        if result == "Zuhören":
            gewonnen = True
            dialog.show_dialog('"Endlich. Danke.\n\nDu hast gewonnen."',
                               ["Zum Highscore"], farbe=FARBE_ZUKUNFTS_ICH)
            return "continue_dialog"
        if result == "Zum Highscore":
            finish("Gewonnen")
            return None
        # ---- Die Frau im Zimmer ----
        if result == "Ja, ich helfe dir":
            frau_gerettet = True
            dialog.show_dialog('"Dann bleib."\n\nSie atmet wieder.\n\n'
                               'Der Computer wartet noch auf dich.',
                               ["Verstanden"], farbe=FARBE_FRAU)
            return "continue_dialog"
        if result == "Nein, ich gehe":
            neustart()
            return None
        if result == "Zu spät":
            neustart()
            return None

        # ---- Finale im Zimmer ----
        # Gewonnen wird erst, wenn alle Objekte eingetippt wurden.
        if fiebertraum and result == "..." and finale_fertig:
            if frau_tot and not frau_gerettet:
                dialog.show_dialog(
                    "Die Namen stimmen alle.\n\nUnd trotzdem geht nichts "
                    "weiter.\n\nSie liegt immer noch da.", ["Verstanden"])
                return "continue_dialog"
            gewonnen = True
            finish("Gewonnen")
            return None
        if fiebertraum and result == "..." and not finale_auftakt:
            finale_auftakt = True
            dialog.show_dialog(
                "Der Computer steht noch da.\n\n"
                "Setz dich hin und schreib auf, was du mitgenommen hast.",
                ["..."])
            return "continue_dialog"

        # ========== WELT 6 REDESIGN ==========
        
        # === DIALOG 1: "Was willst du von mir?" ===
        if world_state == "world6" and w6_stufe == "fliehen" and w6_dialog_ausgeloest:
            if result == "Ich will wissen wer du bist!?":
                w6_stufe = "folgen"
                dialog.show_dialog(
                    "Du machst dich auf, ihr zu folgen...",
                    ["..."]
                )
                return "continue_dialog"
            
            elif result == "Was suchst du hier?":
                w6_stufe = "suchen"
                dialog.show_dialog(
                    'Stille.\n\nDann, scharf und direkt:',
                    ["..."],
                    farbe=FARBE_FRAU
                )
                return "continue_dialog"
        
        # === DIALOG 2: Nach "Wer du bist?" - Frau erreicht ===
        if world_state == "world6" and w6_stufe == "suchen" and w6_frau_erreicht:
            if result == "...":
                # 7 Türen spawnen
                w6_stufe = "tueren"
                spawn_w6_tueren()
                dialog.show_dialog(
                    "Sieben Türen öffnen sich vor dir.\n\n"
                    "Sechs führen ins Nichts.\n"
                    "Eine führt zurück.",
                    ["..."]
                )
                return "continue_dialog"
        
        # === ROOM 1 W6 ENDE: Zum PC ===
        if world_state == "room1" and w6_stufe == "eingabe" and result == "Zum PC":
            w6_eingabe_aktiv = True
            dialog.show_input(
                "Gegenstände in chronologischer Reihenfolge:\n\n"
                "Getrennt durch Komma",
                farbe=FARBE_ZUKUNFTS_ICH,
                max_len=100,
                hinweis="Bsp: Träne, Schuhe, Lampe, Glas, Batterien, Herz"
            )
            return "continue_dialog"
        
        # === NACH FALSCHER EINGABE: Nochmal versuchen ===
        if world_state == "room1" and w6_stufe == "eingabe":
            if result == "Ja und ich hab nicht zugehört":
                # Nochmal versuchen
                dialog.show_input(
                    "Gegenstände in chronologischer Reihenfolge:\n\n"
                    "Getrennt durch Komma",
                    farbe=FARBE_ZUKUNFTS_ICH,
                    max_len=100,
                    hinweis="Bsp: Träne, Schuhe, Lampe, Glas, Batterien, Herz"
                )
                return "continue_dialog"
        
        # Generische Schließer
        if result in ("OK", "...", "Verstanden", "Liegen lassen"):
            return None
        if result == "Zurück zum Hauptmenü":
            return "Hauptmenü"
        return "continue_dialog"

    # ---------------- Start ----------------

    if load_state is not None:
        apply_load_state(load_state)
        inspect_active = True
        dialog.show_dialog("Spielstand geladen. Weiter geht's!", ["Verstanden"])
    else:
        schwierigkeit, zeit_faktor = schwierigkeit_screen()
        w2_zeit = W2_ZEIT * zeit_faktor
        w3_zeit = W3_ZEIT * zeit_faktor
        w4_zeit = W4_ZEIT * zeit_faktor
        dialog.show_dialog("Kopfschmerzen.... Fuck...", ["..."])

    # ---------------- Hauptschleife ----------------

    while True:
        dt = clock.get_time() / 1000.0
        play_time += dt

        for event in ereignisse():
            if event.type == pygame.QUIT:
                return "Spiel beenden", build_snapshot()

            if vollbild_taste(event):
                continue

            if dialog.active:
                dialog_result = dialog.handle_input(event)
                if dialog_result:
                    r = handle_dialog(dialog_result)
                    if r == "Hauptmenü":
                        return "Hauptmenü", build_snapshot()
                    elif r == "continue_dialog":
                        continue
                    else:
                        dialog.hide_dialog()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "Hauptmenü", build_snapshot()

                if event.key == pygame.K_i:
                    inv_visible = not inv_visible
                elif event.key == pygame.K_u:
                    uhr_an = not uhr_an
                elif event.key == pygame.K_F1:
                    zeige_hitboxen = not zeige_hitboxen
                elif event.key == pygame.K_t and world_state == "world4":
                    # Die Lampe gibt es nur im Tunnel - anderswo tut T nichts
                    taschenlampe = not taschenlampe

                if event.key == pygame.K_SPACE and not dead_aktiv:
                    b = belohnung_in_reichweite()
                    if tuer and not tuer["open"] and an_tuer():
                        tuer["open"] = True
                    elif b is not None:
                        nimm_belohnung(b)
                    elif world_state == "world2":
                        p = nearest_item(papers)
                        if p is not None:
                            poem_paper = p
                            dialog.show_poem(p["poem"],
                                             ["Aufsammeln", "Liegen lassen"])
                        else:
                            inspect_active = True
                            dialog.show_dialog(get_world_inspect_text(world_pos), ["OK"])
                    elif world_state == "world4":
                        z = nearest_item(w4_zettel)
                        if z is not None:
                            w4_zettel_offen = z
                            dialog.show_poem(
                                f'Ein Zettel.\n\n{z["wort"]}',
                                ["Aufsammeln", "Liegen lassen"])
                        else:
                            inspect_active = True
                            dialog.show_dialog(
                                get_world_inspect_text(world_pos, STONE_FLAVOR_TEXTS), ["OK"])
                    elif an_frau():
                        frau_ansprechen()
                    elif world_state == "room1" and am_computer():
                        if fiebertraum and not gewonnen and not finale_fertig:
                            # Finale: alle Objekte aus dem Gedaechtnis eintippen
                            finale_starten()
                        else:
                            # Sonst ist der Rechner im Zimmer das Menue
                            return "Hauptmenü", build_snapshot()
                    elif world_state == "room1":
                        inspect_active = True
                        dialog.show_dialog(
                            get_inspect_text(player_pos, door_visible,
                                             bool(tuer and tuer["open"]),
                                             an_tuer()), ["OK"])
                    else:
                        inspect_active = True
                        texts = STONE_FLAVOR_TEXTS if world_state == "world3" else FLAVOR_TEXTS
                        dialog.show_dialog(get_world_inspect_text(world_pos, texts), ["OK"])

        # ---------------- Bewegung ----------------
        if not dialog.active and intro_fade <= 0:
            keys = tastenstand()

            # Sprint nur mit Ausdauer; leer gesprintet -> Pause
            if sprint_gesperrt and ausdauer >= AUSDAUER_SPERRE:
                sprint_gesperrt = False
            sprint_wunsch = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            sprinting = sprint_wunsch and ausdauer > 0 and not sprint_gesperrt
            speed = sprint_speed if sprinting else walk_speed

            dx, dy, richtung = richtung_aus_tasten(keys)
            moved = richtung is not None
            if moved:
                current_direction = richtung

            if world_state == "room1":
                new_pos = [player_pos[0] + dx * speed,
                           player_pos[1] + dy * speed]
                new_pos[0] = max(0, min(WIDTH - 128, new_pos[0]))
                new_pos[1] = max(0, min(HEIGHT - 128, new_pos[1]))
                if moved and r1_blockiert(new_pos):
                    moved = False          # Wand: Schritt wird verworfen
                if moved and not tuer_durchgang(new_pos):
                    if new_pos != player_pos:
                        steps_taken += 1
                    player_pos = new_pos
                    animation_index = (animation_index + 0.2) % 4
            else:
                new_world = [world_pos[0] + dx * speed,
                             world_pos[1] + dy * speed]
                blocked = tuer_durchgang(new_world)
                if world_state == "world4" and not blocked:
                    prect = pygame.Rect(new_world[0], new_world[1], 64, 64)
                    blocked = any(prect.colliderect(w) for w in w4_waende)
                if not blocked and world_state in ("world2", "world3", "world4"):
                    # Fuer Baeume und Felsen zaehlt der Fussbereich -
                    # dieselbe Box wie im Zimmer, nur in Weltkoordinaten.
                    fuss = pygame.Rect(new_world[0] + R1_HITBOX[0],
                                       new_world[1] + R1_HITBOX[1],
                                       R1_HITBOX[2], R1_HITBOX[3])
                    blocked = landschaft.blockiert(world_state, fuss)
                    if blocked:
                        # Steckt er schon fest, zaehlt keine Sperre mehr -
                        # sonst sitzt man bis zum Ende der Uhr in einem
                        # Felsen. Herauslaufen geht immer.
                        jetzt = pygame.Rect(world_pos[0] + R1_HITBOX[0],
                                            world_pos[1] + R1_HITBOX[1],
                                            R1_HITBOX[2], R1_HITBOX[3])
                        if landschaft.blockiert(world_state, jetzt):
                            blocked = False
                if moved and not blocked:
                    world_pos = new_world
                    steps_taken += 1
                    animation_index = (animation_index + 0.2) % 4

            if not moved:
                animation_index = 0.0

            # Ausdauer: Sprint zehrt, alles andere erholt
            if sprinting and moved:
                ausdauer = max(0.0, ausdauer - AUSDAUER_VERBRAUCH * dt)
                if ausdauer <= 0:
                    sprint_gesperrt = True
            else:
                ausdauer = min(AUSDAUER_MAX, ausdauer + AUSDAUER_REGEN * dt)

        # ---------------- Intro & Raum-1-Story ----------------
        if intro_fade > 0:
            intro_fade = max(0.0, intro_fade - dt)
        if world_state == "room1" and not raum1_fertig and not fiebertraum \
                and intro_stufe == 2 and r1_stufe == 0 and steps_taken >= 20 \
                and not dialog.active:
            r1_stufe = 1
            dialog.show_dialog('"Hör auf damit!"', ["Mit was?", "Ignorieren"],
                               farbe=FARBE_ZUKUNFTS_ICH)

        # ---------------- Dead End ----------------
        if dead_aktiv and not dialog.active:
            dead_timer -= dt
            if dead_timer <= 0:
                finish("Dead End")

        # ---------------- Welt 2: Frau + Abschluss ----------------
        if world_state == "world2" and not dialog.active and not dead_aktiv:
            if w2_laeuft and papers_collected < PAPER_COUNT:
                w2_zeit -= dt
                if w2_zeit <= 0.0:
                    w2_zeit = 0.0
                    w2_laeuft = False
                    frau_aktiv = False
                    start_dead_end("Die Uhr steht.\n\n"
                                   "Der Wald hat dich behalten.")
            if w2_stufe == 2:
                w2_warte -= dt
                if w2_warte <= 0:
                    w2_stufe = 3
                    dialog.show_dialog('Du denkst:\n\n"Wer ist sie?"', ["..."])
            if frau_aktiv and papers_collected < PAPER_COUNT:
                ziel = None
                best = None
                for p in papers:
                    if p["collected"]:
                        continue
                    d = (p["pos"][0] - world_pos[0]) ** 2 + (p["pos"][1] - world_pos[1]) ** 2
                    if best is None or d < best:
                        best = d
                        ziel = [p["pos"][0] + 32, p["pos"][1] + 32]
                if ziel:
                    npc.update_guide(dt, (world_pos[0] + 32, world_pos[1] + 32), ziel)
            if papers_collected >= PAPER_COUNT and tuer is None and w2_stufe < 5:
                w2_stufe = 5
                w2_laeuft = False
                frau_aktiv = False
                spawn_belohnung(2, [world_pos[0] + 170, world_pos[1] + 120], "world2")
                w2_tuer_setzen()
                inspect_active = True
                dialog.show_dialog("Alle 10 Papiere.\n\nVor dir erscheinen das Objekt dieser\n"
                                   "Welt und eine Tür.\n\nDie Frau ist fort.", ["Verstanden"])

        # ---------------- Welt 3: Kampf gegen die Uhr ----------------
        if world_state == "world3" and not dialog.active and not dead_aktiv:
            if not w3_laeuft:
                w3_laeuft = True
                w3_phase = 0
                w3_in_phase = 0
                w3_hetze = None
                w3_gegen = None
                w3_punkt = w3_sammelpunkt()

            if w3_vers_zeit > 0:
                w3_vers_zeit -= dt

            if w3_punkt is not None:
                # Gesamtuhr am Handgelenk
                w3_zeit -= dt
                if w3_zeit <= 0:
                    w3_punkt = None
                    w3_hetze = None
                    start_dead_end("Die Uhr an deinem Handgelenk bleibt stehen.\n\n"
                                   "Vorbei.")
                else:
                    # Uhr der laufenden Hetze
                    if w3_hetze is not None:
                        w3_hetz_zeit -= dt
                        if w3_hetz_zeit <= 0:
                            richtung = W3_RICHTUNGEN[w3_hetze][1]
                            w3_punkt = None
                            w3_hetze = None
                            start_dead_end(f"{richtung}\n\nDu warst zu langsam.")

                if w3_punkt is not None and not dead_aktiv:
                    # Gemessen wird vom Fusspunkt des Spielers, nicht von
                    # der linken oberen Ecke seines Sprites - sonst passt
                    # der Griffbereich nicht zu dem, was man sieht.
                    fx, fy = spieler_fusspunkt()
                    dx = w3_punkt[0] - fx
                    dy = w3_punkt[1] - fy
                    if dx * dx + dy * dy < W3_TREFFER_RADIUS ** 2:
                        w3_index += 1
                        # Der Boden, auf dem er gerade steht, bleibt frei -
                        # egal was als Naechstes erscheint. Sonst wacht man
                        # nach dem Durchqueren in einem Felsen auf.
                        landschaft.lichtung("world3", (fx, fy), W3_FREIRAUM)
                        war_hetze = w3_hetze is not None
                        war_gegen = w3_gegen is not None
                        w3_hetze = None

                        if war_hetze:
                            # Hetze geschafft: sofort in die Gegenrichtung
                            w3_gegenpunkt_setzen()
                        else:
                            if war_gegen:
                                # Gegenpunkt geschafft: naechste Phase
                                w3_gegen = None
                                w3_phase += 1
                                w3_in_phase = 0
                            else:
                                w3_in_phase += 1

                            if w3_phase >= len(W3_PHASEN):
                                w3_ende()
                            elif w3_in_phase >= W3_PHASEN[w3_phase][1]:
                                w3_hetze_starten()
                            else:
                                w3_punkt = w3_sammelpunkt()

        # ---------------- Welt 4: Tunnel ----------------
        if world_state == "world4" and not dialog.active and not dead_aktiv:
            if w4_stufe == 2:
                w4_warte -= dt
                if w4_warte <= 0:
                    w4_stufe = 3
                    dialog.show_dialog('Du denkst:\n\n"Wer zum Teufel ist das eigentlich?"',
                                       ["..."])
            if w4_laeuft and not w4_rennen_aus:
                # Zeitlimit laeuft waehrend des ganzen Rennens
                w4_zeit -= dt
                if w4_zeit <= 0:
                    w4_rennen_aus = True
                    frau_aktiv = False
                    start_dead_end("Zeit vorbei.\n\nDas Labyrinth behält dich.")

                # Die Frau laeuft ihren Weg zur Tuer
                if not w4_rennen_aus and frau_aktiv:
                    if w4_frau_wartet > 0:
                        w4_frau_wartet -= dt
                        npc.anim = 0.0
                    elif w4_wp_index < len(w4_wegpunkte):
                        wp = w4_wegpunkte[w4_wp_index]
                        dx = wp[0] - (npc.pos[0] + 64)
                        dy = wp[1] - (npc.pos[1] + 64)
                        d = max(1.0, (dx * dx + dy * dy) ** 0.5)
                        if d < 24:
                            w4_wp_index += 1
                        else:
                            # Sie zieht mit: sprintet er, wird sie schneller.
                            # Das Tempo gleitet, damit es nicht nach einem
                            # Schalter aussieht.
                            ziel_tempo = W4_FRAU_TEMPO * (
                                W4_FRAU_SPRINT_FAKTOR if sprinting else 1.0)
                            anteil = min(1.0, W4_FRAU_ANPASSUNG * dt)
                            w4_frau_tempo += (ziel_tempo - w4_frau_tempo) * anteil
                            schritt = w4_frau_tempo * dt
                            npc.pos[0] += dx / d * schritt
                            npc.pos[1] += dy / d * schritt
                            npc.direction = npc._face(dx, dy)
                            # Sie laeuft sichtbar schneller, wenn sie zulegt
                            npc.anim = (npc.anim
                                        + 12.0 * dt * w4_frau_tempo
                                        / W4_FRAU_TEMPO) % 4

                # Erreicht sie die Tuer zuerst?
                if not w4_rennen_aus and frau_aktiv:
                    fdx = w4_ziel_pos[0] - (npc.pos[0] + 64)
                    fdy = w4_ziel_pos[1] - (npc.pos[1] + 64)
                    if fdx * fdx + fdy * fdy < W4_ZIEL_RADIUS * W4_ZIEL_RADIUS:
                        w4_rennen_aus = True
                        frau_aktiv = False
                        start_dead_end("Sie war schneller.\n\nSie geht durch die Tür "
                                       "und schließt sie\nhinter sich.")

                # Erreicht der Spieler die Tuer zuerst?
                if not w4_rennen_aus:
                    pdx = w4_ziel_pos[0] - (world_pos[0] + 32)
                    pdy = w4_ziel_pos[1] - (world_pos[1] + 32)
                    if pdx * pdx + pdy * pdy < W4_ZIEL_RADIUS * W4_ZIEL_RADIUS:
                        w4_rennen_aus = True
                        w4_stufe = 9
                        frau_aktiv = False
                        spawn_belohnung(4, [w4_ziel_pos[0],
                                            w4_ziel_pos[1] + 120], "world4")
                        spawn_tuer(w4_ziel_pos, "world5")
                        inspect_active = True
                        dialog.show_dialog("Du bist vor ihr da.\n\n"
                                           f"Zettel: {w4_gesammelt} von "
                                           f"{len(W4_WOERTER)}.\n"
                                           "Vor dir: das Objekt dieser Welt "
                                           "und die Tür.", ["Verstanden"])

        # ---------------- Welt 5: Geister ----------------
        # Sie ziehen unabhaengig von allem anderen durchs Bild. Waehrend
        # eines Dialogs ruhen sie - sonst stirbt man beim Lesen.
        if world_state == "world5" and not dialog.active and not dead_aktiv:
            mitte = (world_pos[0] + 64, world_pos[1] + 64)
            if geister.update(dt, mitte):
                geister.zuruecksetzen()
                start_dead_end("Etwas Kaltes geht durch dich hindurch.\n\n"
                               "Du bleibst stehen.")

        # ============ WELT 6: REDESIGN ============
        if world_state == "world6" and not dialog.active and not dead_aktiv:
            px, py = world_pos[0] + 32, world_pos[1] + 32
            
            # === PHASE 1: Frau läuft WEG ===
            if w6_stufe == "fliehen":
                # Distanz messen (akkumuliert)
                bewegung = (player_vel[0]**2 + player_vel[1]**2)**0.5 * dt
                w6_frau_distanz += bewegung
                
                # Frau läuft WEG vom Spieler
                if frau_aktiv:
                    dx = npc.pos[0] + 64 - px
                    dy = npc.pos[1] + 64 - py
                    d = max(1.0, (dx * dx + dy * dy) ** 0.5)
                    
                    # Richtung: WEG (negativ)
                    if d < 800:
                        tempo = 5.0
                        npc.pos[0] -= (dx / d) * tempo * dt
                        npc.pos[1] -= (dy / d) * tempo * dt
                        npc.direction = npc._face(-dx, -dy)
                        npc.anim = (npc.anim + 0.15) % 4
                    else:
                        npc.anim = 0.0
                
                # Nach ~200 Pixel: Dialog auslösen
                if w6_frau_distanz > 200.0 and not w6_dialog_ausgeloest:
                    w6_dialog_ausgeloest = True
                    dialog.show_dialog(
                        'Sie dreht sich um.\n\n"Was willst du von mir?"',
                        ["Ich will wissen wer du bist!?", "Was suchst du hier?"],
                        farbe=FARBE_FRAU
                    )
            
            # === PHASE 2a: Spieler folgt ihr ===
            elif w6_stufe == "folgen":
                # Frau läuft weiter (oder nicht?)
                if frau_aktiv:
                    npc.anim = 0.0  # Sie wartet
            
            # === PHASE 2b: Spieler sucht sie ===
            elif w6_stufe == "suchen":
                if frau_aktiv:
                    dx = npc.pos[0] + 64 - px
                    dy = npc.pos[1] + 64 - py
                    d = max(1.0, (dx * dx + dy * dy) ** 0.5)
                    
                    # Hat Spieler sie erreicht?
                    if d < 100:
                        w6_frau_erreicht = True
                        frau_aktiv = False
                        spawn_tuer([world_pos[0] + 32, world_pos[1] - 260], "room1_w6_ende")
                        npc.anim = 0.0
                        dialog.show_dialog(
                            '"DICH!"\n\n'
                            'Sie starrt dich einfach an.\n'
                            'Nicht fragend. Einfach... an.',
                            ["..."],
                            farbe=FARBE_FRAU
                        )
            
            # === PHASE 3: Sieben Türen ===
            elif w6_stufe == "tueren":
                # Türen wurden schon gespawnt, spieler muss wählen
                pass
            
            # === PHASE 4: Dunkler Raum ===
            elif w6_stufe == "dunkel_raum":
                start_dead_end("Das war wohl nichts.")

        # ---------------- Zeichnen ----------------
        if world_state == "room1":
            spieler_fuss = r1_hitbox(player_pos).bottom
            screen.blit(background_image, (0, 0))
            # Monitorlicht auf den Kacheln - liegt unter allem anderen
            moebel.boden_licht(screen, moebel.sitzt(r1_hitbox(player_pos)))
            # Moebel, die weiter hinten stehen als der Spieler
            moebel.zeichne(screen, spieler_fuss, vorne=False)
            if frau_tot and R1_FRAU_POS[1] <= spieler_fuss:
                screen.blit(frau_liegend, frau_kasten().topleft)
            if door_visible:
                d = door_open_sprite if door_open or (tuer and tuer["open"]) \
                    else door_closed_sprite
                # Nur bis zur Fluchtlinie zeichnen: was tiefer laege, faellt weg
                sichtbar = max(0, min(d.get_height(), R1_TUER_UNTEN - door_pos[1]))
                if sichtbar > 0:
                    screen.blit(d, door_pos,
                                pygame.Rect(0, 0, d.get_width(), sichtbar))
            for b in belohnungen:
                if b["world"] == "room1" and not b["taken"]:
                    screen.blit(objekt_bilder[b["nr"]], b["pos"])
            if not dialog.active:
                sprite = player_sprites[current_direction][int(animation_index)]
                screen.blit(sprite, player_pos)
            if frau_tot and R1_FRAU_POS[1] > spieler_fuss:
                screen.blit(frau_liegend, frau_kasten().topleft)
            # Alles, was vor dem Spieler steht - im Sitzplatz ist das der
            # Tisch, der ihm dabei die untere Haelfte verdeckt.
            moebel.zeichne(screen, spieler_fuss, vorne=True)
            if not dialog.active and an_frau() and not dead_aktiv:
                draw_hud("Leertaste: mit ihr sprechen")
            elif not dialog.active and am_computer() and not dead_aktiv:
                if moebel.sitzt(r1_hitbox(player_pos)):
                    draw_hud("Leertaste: Computer bedienen")
                else:
                    draw_hud("Leertaste: Menü am Computer")
            if zeige_hitboxen:
                ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                eck = r1_boden_polygon()
                pygame.draw.polygon(ov, (60, 220, 120, 60), eck)
                pygame.draw.polygon(ov, (90, 255, 150, 230), eck, 3)
                for e in eck:
                    pygame.draw.circle(ov, (255, 230, 80, 255), e, 7)
                for h in R1_HINDERNISSE:
                    r = pygame.Rect(*h)
                    pygame.draw.rect(ov, (220, 40, 40, 110), r)
                    pygame.draw.rect(ov, (255, 90, 90, 220), r, 2)
                # Fluchtlinie der Tuer: hier wird sie unten abgeschnitten
                pygame.draw.line(ov, (255, 200, 60, 230),
                                 (0, R1_TUER_UNTEN), (WIDTH, R1_TUER_UNTEN), 2)
                pygame.draw.rect(ov, (255, 200, 60, 200),
                                 (door_pos[0], door_pos[1],
                                  door_closed_sprite.get_width(), tuer_hoehe), 2)
                moebel.zeichne_hilfslinien(ov)
                # Aufhebe-Reichweite um jedes liegende Objekt
                for b in belohnungen:
                    if b["world"] == "room1" and not b["taken"]:
                        pygame.draw.circle(ov, (255, 230, 80, 70),
                                           belohnung_mitte(b),
                                           BELOHNUNG_REICHWEITE)
                        pygame.draw.circle(ov, (255, 230, 80, 200),
                                           belohnung_mitte(b),
                                           BELOHNUNG_REICHWEITE, 2)
                fx, fy = spieler_fusspunkt()
                pygame.draw.circle(ov, (60, 200, 255, 255), (fx, fy), 5)
                hb = r1_hitbox(player_pos)
                pygame.draw.rect(ov, (60, 200, 255, 230), hb, 2)
                li, re = r1_boden_grenzen(hb.bottom)
                pygame.draw.line(ov, (60, 200, 255, 160),
                                 (li, hb.bottom), (re, hb.bottom), 1)
                screen.blit(ov, (0, 0))
                draw_hud("F1  hinten y=%d  %d..%d" % (
                    R1_BODEN_HINTEN_Y, R1_BODEN_HINTEN_LINKS,
                    R1_BODEN_HINTEN_RECHTS), zeile=1)
                draw_hud("    vorne  y=%d  %d..%d   Fuesse y=%d" % (
                    R1_BODEN_VORNE_Y, R1_BODEN_VORNE_LINKS,
                    R1_BODEN_VORNE_RECHTS, hb.bottom), zeile=2)
                draw_hud("    Tuer   unten y=%d  hoehe=%d  x=%d" % (
                    R1_TUER_UNTEN, tuer_hoehe, door_pos[0]), zeile=3)
        else:
            sprite = player_sprites[current_direction][int(animation_index)]
            camera = [world_pos[0] - WIDTH // 2 + sprite.get_width() // 2,
                      world_pos[1] - HEIGHT // 2 + sprite.get_height() // 2]
            if not landschaft.boden(screen, camera, world_state):
                draw_infinite_background(camera, TILES[world_state])

            # Fusspunkt des Spielers - danach richtet sich, was vor und
            # was hinter ihm gezeichnet wird.
            spieler_fuss = world_pos[1] + R1_HITBOX[1] + R1_HITBOX[3]

            if world_state == "world4":
                landschaft.zeichne_waende(screen, camera, w4_waende)
                if tuer is None:
                    # Ziel-Tuer am Labyrinth-Ende: das Rennziel
                    screen.blit(door_closed_sprite,
                                (w4_ziel_pos[0] - door_closed_sprite.get_width() // 2
                                 - camera[0],
                                 w4_ziel_pos[1] - door_closed_sprite.get_height() // 2
                                 - camera[1]))
                items = w4_zettel
            elif world_state in ("world2", "world6"):
                items = papers
            else:
                items = []

            # Bewuchs hinter dem Spieler
            landschaft.zeichne(screen, camera, world_state, spieler_fuss,
                               vorne=False)

            for it in items:
                if it.get("collected"):
                    continue
                sx = it["pos"][0] - camera[0]
                sy = it["pos"][1] - camera[1]
                if -80 < sx < WIDTH + 80 and -80 < sy < HEIGHT + 80:
                    screen.blit(paper_sprite, (sx, sy))

            if world_state == "world3" and w3_punkt is not None:
                radius = 30 + int(4 * math.sin(play_time * 5))
                pygame.draw.circle(screen, (10, 10, 12),
                                   (int(w3_punkt[0] - camera[0]),
                                    int(w3_punkt[1] - camera[1])), radius)
                if w3_hetze is not None:
                    # Der Hetzpunkt liegt weit ausserhalb: Pfeil am Bildrand
                    (rx, ry), _ = W3_RICHTUNGEN[w3_hetze]
                    cx, cy = WIDTH // 2, HEIGHT // 2
                    puls = 150 + int(60 * math.sin(play_time * 9))
                    sx, sy = cx + rx * puls, cy + ry * puls
                    ex, ey = cx + rx * (puls + 90), cy + ry * (puls + 90)
                    px, py = -ry, rx
                    farbe = (235, 90, 80)
                    pygame.draw.line(screen, farbe, (sx, sy), (ex, ey), 10)
                    pygame.draw.polygon(screen, farbe, [
                        (ex + rx * 34, ey + ry * 34),
                        (ex + px * 26, ey + py * 26),
                        (ex - px * 26, ey - py * 26)])

            if tuer:
                d = door_open_sprite if tuer["open"] else door_closed_sprite
                screen.blit(d, (tuer["pos"][0] - camera[0], tuer["pos"][1] - camera[1]))

            for b in belohnungen:
                if b["world"] == world_state and not b["taken"]:
                    screen.blit(objekt_bilder[b["nr"]],
                                (b["pos"][0] - camera[0], b["pos"][1] - camera[1]))

            if frau_aktiv:
                npc.draw(screen, camera)

            if not dialog.active:
                screen.blit(sprite, (world_pos[0] - camera[0], world_pos[1] - camera[1]))

            # Bewuchs vor dem Spieler - hier laeuft man dahinter durch
            landschaft.zeichne(screen, camera, world_state, spieler_fuss,
                               vorne=True)

            if world_state == "world5":
                geister.zeichne(screen, camera)

            # Dunkelheit im Tunnel. Kommt nach der ganzen Welt und vor
            # dem HUD - Uhr und Zaehler bleiben also lesbar.
            if world_state == "world4" and W4_DUNKEL:
                landschaft.dunkelheit.zeichne(screen, taschenlampe,
                                              pygame.time.get_ticks() / 1000.0)

            # HUD
            if world_state == "world2":
                draw_hud(f"Blätter: {papers_collected} von {PAPER_COUNT}")
                draw_hud("U: Uhr " + ("aus" if uhr_an else "an"), zeile=1)
                if w2_laeuft and uhr_an:
                    draw_wrist_watch(screen, w2_zeit, watch_font_big,
                                     watch_font_small, watch_overlay)
            elif world_state == "world3" and w3_laeuft and w3_punkt is not None:
                draw_hud(f"Punkte: {w3_index} von {W3_PUNKTE_GESAMT}")
                if w3_hetze is not None:
                    ruf = W3_RICHTUNGEN[w3_hetze][1]
                    # Der Ruf blinkt, damit man ihn nicht uebersieht
                    if int(play_time * 6) % 2 == 0:
                        farbe = (245, 90, 80)
                    else:
                        farbe = (255, 200, 120)
                    surf = ruf_font.render(ruf, True, farbe)
                    rect = surf.get_rect(center=(WIDTH // 2, 150))
                    bg = pygame.Surface((rect.width + 60, rect.height + 24),
                                        pygame.SRCALPHA)
                    bg.fill((0, 0, 0, 170))
                    screen.blit(bg, (rect.x - 30, rect.y - 12))
                    screen.blit(surf, rect)
                    draw_bottom_timer(w3_hetz_zeit, W3_SPRINT_ZEIT * zeit_faktor)
                if w3_vers_zeit > 0 and w3_vers_text:
                    # Blendet zum Schluss weich aus, damit es nicht
                    # einfach wegspringt.
                    deckung = int(255 * min(1.0, w3_vers_zeit / 1.5))
                    zeilen = w3_vers_text.split("\n")
                    breite = max(vers_font.size(z)[0] for z in zeilen) + 56
                    hoehe = len(zeilen) * 40 + 30
                    kasten = pygame.Surface((breite, hoehe), pygame.SRCALPHA)
                    kasten.fill((0, 0, 0, int(160 * deckung / 255)))
                    pygame.draw.rect(kasten, (190, 175, 130, deckung),
                                     kasten.get_rect(), 2, border_radius=8)
                    for i, z in enumerate(zeilen):
                        surf = vers_font.render(z, True, (226, 216, 186))
                        surf.set_alpha(deckung)
                        kasten.blit(surf, surf.get_rect(
                            center=(breite // 2, 22 + i * 40)))
                    screen.blit(kasten, kasten.get_rect(
                        center=(WIDTH // 2, 260)))
                if uhr_an and w3_hetze is None:
                    draw_wrist_watch(screen, w3_zeit, watch_font_big, watch_font_small,
                                     watch_overlay)
            elif world_state == "world4":
                draw_hud(f"Zettel: {w4_gesammelt} von {len(W4_WOERTER)}")
                if W4_DUNKEL:
                    draw_hud("T: Lampe " + ("aus" if taschenlampe else "an"),
                             zeile=1)
                # Kein Balken mehr: du sollst nicht wissen, wie sie steht.
                # Wer die Restzeit sehen will, blendet mit U die Uhr ein.
                if w4_laeuft and not w4_rennen_aus and uhr_an:
                    draw_wrist_watch(screen, w4_zeit, watch_font_big,
                                     watch_font_small, watch_overlay)
            elif world_state == "world5" and w5_anweisung:
                draw_hud(f"Zukunfts-Ich: {w5_anweisung}")
                draw_hud(f"Türen: {w5_tueren} von {W5_TUEREN_ZIEL}", zeile=1)
            elif world_state == "world6" and ewig_zettel:
                draw_hud(f"Rilke-Zettel: {ewig_zettel}")

        if not dialog.active and not dead_aktiv:
            draw_ausdauer()

        if inv_visible and not dialog.active:
            draw_inventory()

        if dialog.active:
            dialog.draw()

        # Intro-Einblendung: schwarz -> hell
        if intro_fade > 0:
            fade = pygame.Surface((WIDTH, HEIGHT))
            fade.fill((0, 0, 0))
            fade.set_alpha(int(255 * intro_fade / INTRO_FADE_DAUER))
            screen.blit(fade, (0, 0))
            if dialog.active:
                dialog.draw()

        bild_zeigen()
        clock.tick(30)

        if abschluss == "Highscore":
            return "Highscore", build_snapshot()
        if abschluss == "Neustart":
            return "Neustart", None


def slot_screen(save_manager, title, allow_empty=True):
    """Zeigt die 6 Speicherslots. Gibt den gewählten Slot-Index zurück oder None (ESC).
    allow_empty=False: leere Slots sind nicht wählbar (beim Laden)."""
    font_title = pygame.font.Font(None, 64)
    font = pygame.font.Font(None, 44)
    font_small = pygame.font.Font(None, 32)
    slots = save_manager.load_all()
    cursor = 0
    clock = pygame.time.Clock()

    while True:
        for event in ereignisse():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if vollbild_taste(event):
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_UP:
                    cursor = (cursor - 1) % SaveManager.SLOT_COUNT
                elif event.key == pygame.K_DOWN:
                    cursor = (cursor + 1) % SaveManager.SLOT_COUNT
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if slots[cursor] is not None or allow_empty:
                        return cursor

        screen.fill((24, 24, 30))
        t = font_title.render(title, True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, 80)))

        for i in range(SaveManager.SLOT_COUNT):
            y = 150 + i * 128
            rect = pygame.Rect(112, y, WIDTH - 224, 108)
            pygame.draw.rect(screen, (40, 40, 48), rect, border_radius=12)
            if i == cursor:
                pygame.draw.rect(screen, (120, 220, 160), rect, 5, border_radius=12)
            else:
                pygame.draw.rect(screen, (90, 90, 100), rect, 2, border_radius=12)

            s = slots[i]
            if s is None:
                txt = font.render(f"Slot {i + 1}   -  leer  -", True, (120, 120, 130))
                screen.blit(txt, (rect.x + 30, rect.y + 36))
            else:
                l1 = font.render(f"Slot {i + 1}   {s['welt']}", True, WHITE)
                l2 = font_small.render(f"{s['datum']}   |   {s['fortschritt']}",
                                       True, (170, 220, 180))
                screen.blit(l1, (rect.x + 30, rect.y + 18))
                screen.blit(l2, (rect.x + 30, rect.y + 64))

        hint = font_small.render(
            "Pfeiltasten: wählen   Leertaste: bestätigen   ESC: zurück",
            True, (150, 150, 160))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

        bild_zeigen()
        clock.tick(30)


def schwierigkeit_screen():
    """Auswahl vor dem ersten Schritt. Gibt (Name, Zeitfaktor) zurueck.

    Die Stufen unterscheiden sich ausschliesslich in der Zeit - Wege,
    Hindernisse und Gegner bleiben gleich."""
    font_titel = pygame.font.Font(None, 64)
    font = pygame.font.Font(None, 50)
    font_klein = pygame.font.Font(None, 32)
    cursor = SCHWIERIGKEIT_STANDARD
    clock = pygame.time.Clock()
    while True:
        for event in ereignisse():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if vollbild_taste(event):
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    cursor = (cursor - 1) % len(SCHWIERIGKEITEN)
                elif event.key == pygame.K_DOWN:
                    cursor = (cursor + 1) % len(SCHWIERIGKEITEN)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    name, faktor, _ = SCHWIERIGKEITEN[cursor]
                    return name, faktor
                elif event.key == pygame.K_ESCAPE:
                    name, faktor, _ = SCHWIERIGKEITEN[SCHWIERIGKEIT_STANDARD]
                    return name, faktor

        screen.fill((20, 20, 26))
        t = font_titel.render("Wie viel Zeit willst du?", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, 190)))
        for i, (name, faktor, satz) in enumerate(SCHWIERIGKEITEN):
            y = 330 + i * 150
            rect = pygame.Rect(150, y, WIDTH - 300, 122)
            pygame.draw.rect(screen, (38, 38, 46), rect, border_radius=12)
            pygame.draw.rect(screen, (120, 220, 160) if i == cursor
                             else (90, 90, 100), rect, 5 if i == cursor else 2,
                             border_radius=12)
            screen.blit(font.render(name, True, WHITE), (rect.x + 32, rect.y + 20))
            screen.blit(font_klein.render(satz, True, (170, 215, 180)),
                        (rect.x + 32, rect.y + 72))
            minuten = font_klein.render(
                f"Waldreich {int(W2_ZEIT * faktor // 60)}:{int(W2_ZEIT * faktor % 60):02d}   "
                f"Erdreich {int(W3_ZEIT * faktor // 60)}:{int(W3_ZEIT * faktor % 60):02d}   "
                f"Labyrinth {int(W4_ZEIT * faktor // 60)}:{int(W4_ZEIT * faktor % 60):02d}",
                True, (150, 150, 165))
            screen.blit(minuten, minuten.get_rect(
                topright=(rect.right - 32, rect.y + 74)))
        hinweis = font_klein.render(
            "Pfeiltasten: wählen   Enter: starten", True, (150, 150, 160))
        screen.blit(hinweis, hinweis.get_rect(center=(WIDTH // 2, HEIGHT - 60)))
        bild_zeigen()
        clock.tick(30)


def info_screen(text):
    """Kurze Meldung; jede Taste schließt sie."""
    font = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()
    while True:
        for event in ereignisse():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if vollbild_taste(event):
                continue
            if event.type == pygame.KEYDOWN:
                return
        screen.fill((24, 24, 30))
        for i, line in enumerate(text.split("\n")):
            surf = font.render(line, True, WHITE)
            screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40 + i * 56)))
        hint = font_small.render("Beliebige Taste drücken", True, (150, 150, 160))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 60)))
        bild_zeigen()
        clock.tick(30)



def main():
    global SETTINGS
    settings = Settings()
    SETTINGS = settings
    # Gespeicherten Vollbild-Zustand wiederherstellen
    if settings.current_settings.get("fullscreen") and not ist_vollbild():
        vollbild_umschalten()
    save_manager = SaveManager()
    hs_manager = HighscoreManager()
    hs_manager.letzter = None

    background_image, player_sprites, door_sprites = load_game_resources()
    if background_image is None or player_sprites is None or door_sprites is None:
        print("Fehler beim Laden der Spielressourcen!")
        pygame.quit()
        sys.exit(1)

    menu = Menu(settings)
    game_state = "Hauptmenü"
    last_snapshot = None


    while True:
        if game_state == "Highscore":
            highscore_screen(hs_manager, neuester=hs_manager.letzter)
            hs_manager.letzter = None
            last_snapshot = None
            game_state = "Hauptmenü"

        elif game_state == "Hauptmenü":
            # Laeuft ein Spiel, steht "Weiterspielen" ganz oben und ist
            # vorausgewaehlt - Enter bringt einen exakt dorthin zurueck.
            if last_snapshot is not None and "Weiterspielen" not in menu.main_options:
                menu.main_options.insert(0, "Weiterspielen")
                if "Spiel starten" in menu.main_options:
                    i = menu.main_options.index("Spiel starten")
                    menu.main_options[i] = "Neues Spiel"
                menu.current_menu = "main"
                menu.selected_option = 0
            elif last_snapshot is None and "Weiterspielen" in menu.main_options:
                menu.main_options.remove("Weiterspielen")
                if "Neues Spiel" in menu.main_options:
                    i = menu.main_options.index("Neues Spiel")
                    menu.main_options[i] = "Spiel starten"
                menu.selected_option = 0

            menu.draw(screen)
            bild_zeigen()

            for event in ereignisse():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if vollbild_taste(event):
                    continue

                selected = menu.handle_input(event)
                if selected:
                    if selected == "Weiterspielen":
                        # Genau dort weitermachen, wo das Spiel verlassen wurde
                        game_state, last_snapshot = game_loop(
                            background_image, player_sprites, door_sprites,
                            settings, hs_manager,
                            load_state=last_snapshot)

                    elif selected in ("Spiel starten", "Neues Spiel"):
                        game_state, last_snapshot = game_loop(
                            background_image, player_sprites, door_sprites,
                            settings, hs_manager)

                    elif selected in ("Spielstand", "Spielstand laden"):
                        slot = slot_screen(save_manager, "Spielstand laden",
                                           allow_empty=False)
                        if slot is not None:
                            data = save_manager.load_slot(slot)
                            if data is not None:
                                game_state, last_snapshot = game_loop(
                                    background_image, player_sprites, door_sprites,
                                    settings, hs_manager,
                                    load_state=data["state"])

                    elif selected == "Spiel speichern":
                        if last_snapshot is None:
                            info_screen("Kein aktiver Spielstand.\nStarte zuerst ein Spiel.")
                        else:
                            slot = slot_screen(save_manager, "Spiel speichern")
                            if slot is not None:
                                save_manager.save_slot(slot, last_snapshot)
                                info_screen(f"In Slot {slot + 1} gespeichert!")

                    elif selected == "Highscores":
                        highscore_screen(hs_manager)

                    elif selected in ("Spiel beenden", "Spiel verlassen"):
                        pygame.quit()
                        sys.exit()

        elif game_state == "Neustart":
            # Von vorne, ohne Umweg ueber das Menue
            game_state, last_snapshot = game_loop(
                background_image, player_sprites, door_sprites,
                settings, hs_manager)

        elif game_state == "Spiel beenden":
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    main()

