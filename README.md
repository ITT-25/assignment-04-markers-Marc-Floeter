[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/-leASaOw)

# 4.1: Perspective Transformation

## Installation und Start
- Navigiere in Ordner ```perspective_transformation```
- Aktiviere Virtual Environment mit ```venv\scripts\activate```
- Installiere ggf. Abhängigkeiten mit ```pip install -r requirements.txt```
- Starte Anwendung mit ```python image_extractor.py {Input-Bild Pfad} {Output-Bild Pfad} {Gewünschte Breite} {Gewünschte Höhe}```

## Anwendung
- Wähle die vier Eckpunkte des Bereiches, den du auf den beim Start angegebenen Bereich zerren möchtest (Reihenfolge: Uhrzeigersinn von oben links)
- Nach Auswahl des vierten Punktes öffnet sich automatisch ein zweites Fenster mit dem Ergebnis
    - Drücke "S", um das gezerrte Bild am angegebenen Pfad zu sichern und zur Auswahl zurückzukehren
    - Drücke "ESC", um das gezerrte Bild zu verwerfen und zur Auswahl zurückzukehren
- Drücke "ESC", um die Bisher gewählten Transformationspunkte zu verwerfen
- Drücke "Q", um die Anwendung zu schließen


# 4.2: AR Game

## Installation und Start
- Navigiere in Ordner ```ar_game```
- Aktiviere Virtual Environment mit ```venv\scripts\activate```
- Installiere ggf. Abhängigkeiten mit ```pip install -r requirements.txt```
- Starte Anwendung mit ```python AR_game.py```

## Ingame
- Halte das Blatt mit den 4 Markern in der Anweisung entsprechend in die Kamera, dann startet das Spiel
- Es spawnen Mücken und Ballons. Die Aufgabe dürfte klar sein: Töte die Mücken durch Berührung mit dem Finger von unten (höchste y-Koordinate der Umrisse der Hand) und ernte dafür Punkte! Aber lass die Ballons in Ruhe, sonst bekommst du ein Leben abgezogen
- Entferne das Blatt oder decke einen Marker ab, um zu pausieren
- Während der Pause oder bei Game Over (0 Leben) kann das Spiel mit R neu gestartet werden
- Beenden der Anwendung ist mit Q jederzeit möglich

## Optionales, wofür mal wieder die Zeit nicht gereicht hat (äußere Umstände, Technik lief diesmal prima!)
- Erkennung der Fingerspitze nicht durch y-Wert, sondern durch größtes lokales Extrem im Konturverlauf
- Anpassung der Spielschwierigkeit mit steigenden Punkten oder fortschreitender Zeit (einfach mehr Ballons? Schnellere Mücken? Sowas eben)


# 4.3: AR-Game - now 3D

## Installation und Start
- Navigiere in Ordner ```ar_game_3d```
- Aktiviere Virtual Environment mit ```venv\scripts\activate```
- Installiere ggf. Abhängigkeiten mit ```pip install -r requirements.txt```
- Starte Anwendung mit ```python AR_sample_3d.py```

# Anwendung
- Marker IDs habe ich zu 1 und 2 geändert, da ich 4 und 5 verlegt hatte... gerne bei Bedarf ändern
- Enton wird auf beiden Markern angezeigt, wenn diese erkannt werden (ein 3D-Modell, das auch laden wollte, habe ich auf die paar Minuten, die mir für diese Aufgabe geblieben sind, nicht gefunden)
- Die Modelle werden nur dann angezeigt, wenn der Marker auch erkannt wurde
- Sind beide Entons sichtbar, drehen sie sich beide
- War zuletzt nicht mehr testbar, weil die Kamera bei dieser Rechenauslastung versagt hat...? ("can't grab frame")