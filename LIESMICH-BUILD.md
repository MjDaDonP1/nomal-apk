# nomal → APK

Fertig zum Hochladen. Was noch fehlt, steht ganz unten.

## Eine Datei statt elf

`main.py`, 5.570 Zeilen. Reihenfolge der Abschnitte:

```
konfig · texte · verse · labyrinth · raum1 · raum1_moebel
figuren · landschaft · Dialogfenster · Spielmenu · Spielkern
```

Jeder Abschnitt steht unter einer Überschrift mit seinem alten
Dateinamen. Übersetzt ohne Fehler, keine doppelt vergebenen Namen.

## Musik ist raus

Entfernt: die Klasse `MusicManager`, alle sechs Aufrufe, der Parameter
`music_manager` aus `game_loop()` und dem Menü, die Einträge
`music_enabled`, `volume` und `music_interval` aus den Einstellungen.
Der Ordner `music/` wird nicht mehr angefasst.

Im Einstellungsmenü blieb danach nur „Zurück" übrig. Dort steht jetzt
**Vollbild Ein/Aus** — am Rechner dasselbe wie F11, am Handy ohne
Wirkung, weil dort ohnehin immer Vollbild ist.

## Bedienung auf dem Bildschirm

Das war der eigentliche Brocken: das Spiel kennt nur Tastatur. Statt
die Spiellogik umzubauen, legt sich jetzt eine Schicht davor. Sie
nimmt Fingertipper entgegen und übersetzt sie in genau die Tasten, die
auch eine Tastatur schicken würde — gehaltene Tasten über
`tastenstand()`, kurze Drücke als echte `KEYDOWN`/`KEYUP`-Ereignisse.
Der Spielkern merkt von alldem nichts.

Aufteilung: vier Pfeiltasten links unten, im Kreuz angeordnet wie auf
der Tastatur — jede eine eigene eckige Taste. Rechts unten der große
Knopf **A** (Leertaste), daneben **OK** (Enter) und **Lauf** (Shift
zum Sprinten, gehalten). Oben rechts vier kleine für **Menü**,
**Zeug**, **Uhr**, **Licht**.

Drei Dinge, die den Unterschied machen:

**Mehrere Finger gleichzeitig.** Laufen und gleichzeitig A drücken
geht, weil jeder Finger einzeln verfolgt wird.

**Unsichtbarer Rand.** Jede Pfeiltaste nimmt noch eine viertel
Tastenbreite über ihren Rand hinaus an. Auf Glas trifft der Daumen
selten genau, und ein Schritt, der nicht kommt, fällt mehr auf als
einer, der eine Spur zu früh kommt. In der Mitte des Kreuzes liegt
nichts — wer dort tippt, läuft nicht los.

**Die Tasten liegen im schwarzen Rand, nicht im Bild.** Dafür zeichnet
das Spiel auf dem Handy in eine eigene Fläche von 1024×1024 und wird
erst beim Anzeigen aufs Display gerechnet. Mit `pygame.SCALED` säßen
die Tasten mitten im Spielbild. Am Rechner ändert sich nichts.

Vom Pfeil auf den nächsten rutschen geht, ohne abzusetzen; wer den
Finger daneben zieht, lässt los.

Getestet mit einem durchlaufenden Spiel im Android-Modus: Intro
weggeklickt, mit der Pfeiltaste nach rechts gelaufen — der Spieler
kommt von x=512 auf x=672, zwanzig Schritte, dann geht wie vorgesehen
der Zimmer-Dialog auf und lässt sich mit den Pfeiltasten
durchblättern. Ein zweiter Finger auf A erzeugt Leertaste, während der
Pfeil weiter hält.

**Am Rechner ausprobieren:** F2 schaltet die Bedienung ein, dann geht
sie mit der Maus. F2 nochmal schaltet sie aus.

Dazu zwei Kleinigkeiten: die Zurück-Taste des Handys wirkt wie Escape,
und während die Bildschirmtastatur im Finale offen ist, verschwindet
die Bedienung — sie läge sonst unter den Tasten.

## Weitere Änderungen fürs Handy

**Pfade.** Bilder und Schrift werden relativ zum Ort der `main.py`
gesucht, nicht zum Arbeitsverzeichnis. Auf Android ist das nie der
App-Ordner — ohne das findet das Spiel kein einziges Bild.

**Schreiben.** `saves.json`, `settings.json` und `highscores.json`
gehen in die private Ablage der App; der App-Ordner selbst ist
schreibgeschützt. Am Rechner liegen sie weiter neben dem Spiel.

**Texteingabe.** Das Finale am Rechner ließ sich nur mit `KEYDOWN`
tippen — die Bildschirmtastatur schickt aber `TEXTINPUT`, und sie geht
überhaupt nur auf, wenn das Spiel sie anfordert. Beides ist drin.

**Menü-Hintergrund.** Wurde in *jedem einzelnen Bild* neu von der
Platte geladen. Jetzt einmal.

## Bilder

20 Dateien, 5,1 MB, dazu `fonts/graffiti.ttf`. Genau die, die das
Spiel auch aufruft — nachgezählt: keine Datei im Ordner, die nirgends
vorkommt, und die Landschaft vermisst keine.

Nicht dabei und gelöscht: `wald_baum_b`, `wald_baum_c`,
`wald_baum_gross`, `wald_baum_klein`, `wald_baum_nacht`,
`wald_gras_1`, `wald_ast`, `Frau_Sprites.png` und
`WildStyle_ttf.otf`. Die Bildtabelle steht unverändert auf drei Bäumen
und zwei Gräsern.

## Fünf Bilder fehlen noch

Kein Absturz, für jedes gibt es einen gezeichneten Notbehelf. Aber es
sieht anders aus als gedacht:

| fehlt | Notbehelf |
|---|---|
| `Papier.png` | weißes Rechteck — betrifft alle zehn Rilke-Blätter in Welt 2 |
| `Uhr.png` | gezeichnetes Handgelenk mit Armbanduhr |
| `background3.png` | prozedurale Steintextur (Steinwelt) |
| `lava.png` | einfarbig orange Kachel (Welt 5) |
| `himmel.png` | einfarbig hellblaue Kachel (Welt 6) |

`npc.png` fehlt auch, wird aber nicht gebraucht: die Frau kommt aus
`Frau.png`.

## Bauen, ohne etwas zu installieren

`.github/workflows/apk.yml` ist fertig. Der Bau läuft auf GitHubs
Rechnern.

1. Neues Repository anlegen (privat reicht).
2. Den ganzen Ordner hochladen: `main.py`, `buildozer.spec`,
   `images/`, `fonts/`, `.github/`.
3. Reiter **Actions** öffnen. Der Lauf startet von selbst.
4. Nach 30–60 Minuten unten auf der Seite des Laufs unter
   **Artifacts** die `nomal-apk` herunterladen, entpacken, aufs Handy
   schieben, installieren (Installation aus unbekannter Quelle muss
   einmal erlaubt werden).

Jeder weitere Lauf dauert nur Minuten, weil SDK und NDK aus dem Cache
kommen. Geht etwas schief, steht der Grund im Protokoll des Laufs —
schick mir die letzten Zeilen.

## Oder auf eigenem Rechner

Braucht Linux, unter Windows WSL2, und lädt beim ersten Mal rund 2 GB.

```bash
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config zlib1g-dev libncurses-dev \
    cmake libffi-dev libssl-dev
pip install --user buildozer "cython<3"

cd nomal_apk
buildozer -v android debug
```

Fertig liegt die APK in `bin/nomal-0.1-arm64-v8a-debug.apk`. Aufs
Handy mit `buildozer android deploy run logcat` — `logcat` ist
wichtig, stürzt die App ab, steht der Grund nur dort.

## Noch offen

- Die fünf Bilder oben.
- Ein Symbol, 512×512 PNG. Bis dahin nimmt Android das Standardsymbol.
- Ob `online.coldfrogames.nomal` als App-ID passt.
- Hochkant oder quer. Steht auf hochkant; quer macht das Spielbild
  größer, rückt die Knöpfe aber dichter ans Bild.
