# Projekt Thunfisch

Willkommen beim Quellcode für Pea, Codename Thunfisch.

Zuerst einmal: Es handelt sich bei Pea um einen Discord Bot in Python, der im Großen und Ganzen ein Spiel umfasst, in dem man versucht sein Katzenklo möglichst erfolgreich auszubauen, um möglichst viele verschiedene Katzen zu sammeln.

Für alle, die Interesse daran haben, zu verstehen, was genau eigentlich hinter den Kulissen abgeht, gibt es dafür diese ReadMe Datei sowie den Quellcode, um die Funktionsweise nachzuvollziehen.

## Aufbau

Bevor wir uns den im Repo verhandenen Dateien widmen, gibt es hier erstmal eine Aufzählung von Dateien, die es im Repo NICHT gibt.

Darunter fallen `kk/config.py`, die wahrscheinlich wichtigste, fehlende Datei. In dieser Datei werden quasi alle wichtigen Konstanten definiert, die in sämtlichen Dateien verwendet werden. Aber auch nicht zwingend zu versteckende Dinge, so wie dieses Wörterbuch, lassen sich in dieser Datei finden:

```
CATEGORY_EMOJIS = {
    "Katzenklos": "🎨",
    "Katzenstreu": "🥛",
    "Dekoartikel": "✨",
    "Orte": "📍",
    "Schilder": "🏷️",
    "Schildtexte": "😺",
}
```

Des weiteren fehlen die beiden Ordner `img/` und `data/` in denen jeweils Grafiken bzw. verschiedene Datendateien leben. Während der `img/` Ordner eher uninteressant ist, möchte ich gerne zumindest das Dateiformat von den wichtigsten `data/`-Dateien zeigen, damit man das Zugriffen auf diese Dateien im Code besser nachvollziehen kann.

### `shop.json`

In der Shop-Datei befinden sich die Informationen zu allen im Shop befindlichen Items. Dabei ist die Datei wie folgt strukturiert:

```
{
    "ITEM-KATEGORIE": {
        "ITEM-CODENAME": {
            "name": "NAME",
            "price": PREIS,
            "image": "BILDFPAD",
            "description": "BESCHREIBUNG",
            "purchasable": true/false,
            "group": "ITEM-GRUPPE"
        }
    }
}
```

Dieses json Format sollte ziemlich selbsterklärend sein.

### `cats.json`

Hier befinden sich jegliche Informationen zu den zu sammelnden Katzen.

```
{
    "CODENAME": {
        "name": "NAME",
        "pay_min": X,
        "pay_max": Y,
        "favs": {
            "ITEMKATEGORIE": [
                ITEM-CODENAME(N)
            ]
        },
        "go_anywhere": true/false,
        "group": "GRUPPE"
    }
}
```

Hieraus kann, in Verbindung mit dem Quellcode die grundlegende Funktionsweise der Katzen verstanden werden.

### stats.json

Zuletzt gibt es natürlich die Spielstandsdatei. Sie enthält das Inventar, die Katzen und sonst noch alle relevanten, zu speichernden Informationen.

```
{
    "USER-ID": {
        "owned": {
            "ITEMKATEGORIE": [
                ITEM-CODENAME(N)
            ]
        },
        "equipped": {
            "ITEMKATEGORIE": [
                ITEM-CODENAME(N)
            ]
        },
        "balance": MÜNZEN,
        "cats_seen": {
            "KATZEN-CODENAME": {
                "name": "NAME",
                "pay_min": X,
                "pay_max": Y,
                "matching_favs": {
                    "ITEM-KATEGORIE": [
                        "ITEM-CODENAME(N)"
                    ]
                },
                "visits": BESUCHE
            }
        },
        "dirty": DRECKIG?,
        "occupied": KATZEN-CODENAME / false,
        "summary": [
            "ZUSAMMENFASSUNGSTEXT(E)"
        ]
    }
}
```

Auch hier ist wahrscheinlich die Idee klar.