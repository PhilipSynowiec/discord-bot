# Discord XP & Rickroll Bot

Ein Discord-Bot, der ein XP-System, automatische Rollenvergabe und eine Rickroll-Funktionalität bietet. Dieser Bot wurde entwickelt, um die Programmierfortschritte zu demonstrieren und kann einfach angepasst und erweitert werden.

## Inhaltsverzeichnis

- [Funktionen](#funktionen)
- [Anforderungen](#anforderungen)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Verwendung](#verwendung)
- [Befehle](#befehle)
- [Mitwirkende](#mitwirkende)
- [Lizenz](#lizenz)

## Funktionen

- **XP-System**: Mitglieder erhalten XP durch Nachrichten und Sprachaktivitäten.
- **Automatische Rollenvergabe**: Rollen werden automatisch basierend auf dem XP-Wert eines Mitglieds vergeben.
- **Prefix-Anpassung**: Ändere das Server-Prefix dynamisch.
- **Rickroll-System**: Markiere Mitglieder oder Rollen, die bei Sprachbeitritten gerickrollt werden sollen.
- **Statistiken & Ranglisten**: Überprüfe XP-Statistiken einzelner Mitglieder oder sieh dir eine serverweite Rangliste an.

## Anforderungen

- **Python 3.8 oder 3.9**: Empfohlen, da ältere Versionen von `discord.py` möglicherweise nicht mit neueren Python-Versionen kompatibel sind.
- **discord.py 1.7.3**: Installiere eine ältere Version von `discord.py`, um Kompatibilitätsprobleme zu vermeiden.
- **TinyDB**: Eine einfache JSON-basierte Datenbank zur Speicherung von Bot-Daten.

## Installation

1. **Repository klonen:**

   ```bash
   git clone https://github.com/DEIN_GITHUB_REPO/discord-xp-rickroll-bot.git
   cd discord-xp-rickroll-bot
   ```

2. **Virtuelle Umgebung erstellen und aktivieren (optional, aber empfohlen):**

   ```bash
   python3.9 -m venv bot_env
   source bot_env/bin/activate  # Auf Linux/Mac
   # Oder auf Windows:
   # bot_env\Scripts\activate
   ```

3. **Benötigte Pakete installieren:**

   ```bash
   pip install discord.py==1.7.3 tinydb
   ```

## Konfiguration

1. **Bot-Token einrichten:**

   - Erstelle eine `.env` Datei im Hauptverzeichnis oder verwende Umgebungsvariablen, um deinen Discord-Bot-Token sicher zu speichern.
   - Beispiel `.env` Datei:

     ```env
     TOKEN=DEIN_DISCORD_BOT_TOKEN_HIER
     ```

   - Passe `main.py` an, um den Token aus der `.env` Datei zu laden:

     ```python
     # main.py

     import os
     from dotenv import load_dotenv

     load_dotenv()
     TOKEN = os.getenv('TOKEN')
     ```

2. **Datenbank initialisieren:**

   - Beim ersten Start des Bots wird automatisch eine `bot.json` Datei erstellt, die alle notwendigen Daten für Server und Mitglieder speichert.

## Verwendung

1. **Bot starten:**

   ```bash
   python main.py
   ```

2. **Befehle im Discord-Server verwenden:**

   - **Prefix ändern:**
     - `!prefix set <neues_prefix>`
     - Beispiel: `!prefix set ?`

   - **XP verwalten:**
     - `!xp add @Mitglied 50`  
       Fügt dem genannten Mitglied 50 XP hinzu.  
     - `!xp set @Mitglied 200`  
       Setzt die XP des genannten Mitglieds auf 200.  

   - **Statistiken abrufen:**
     - `!stats @Mitglied`  
       Zeigt die XP-Statistiken des genannten Mitglieds an.  
     - `!stats`  
       Zeigt deine eigenen XP-Statistiken an.

   - **Rangliste anzeigen:**
     - `!ranklist`  
       Zeigt eine Rangliste aller Mitglieder nach XP an.

   - **Rickroll-Ziele verwalten:**
     - `!rickroll add @Mitglied oder @Rolle`  
       Fügt ein Mitglied oder eine Rolle zu den Rickroll-Zielen hinzu.  
     - `!rickroll remove @Mitglied oder @Rolle`  
       Entfernt ein Mitglied oder eine Rolle von den Rickroll-Zielen.  
     - `!rickroll get`  
       Zeigt die aktuellen Rickroll-Ziele an.

   - **Automatische Rollen verwalten:**
     - `!autoroles set <XP> @Rolle <XP> @Rolle ...`  
       Definiert automatische Rollen, die Mitglieder basierend auf ihrem XP-Wert erhalten.  
       Beispiel: `!autoroles set 100 @Beginner 200 @Advanced`  
     - `!autoroles get`  
       Zeigt die konfigurierten automatischen Rollen und die erforderlichen XP-Werte an.

   - **Hilfe anzeigen:**
     - `!help`  
       Zeigt das Hauptmenü der verfügbaren Befehle an.  
     - `!help <Befehl>`  
       Zeigt detaillierte Informationen zu einem spezifischen Befehl an.  
       Beispiel: `!help xp add`

3. **Berechtigungen:**

   - Einige Befehle erfordern Administratorrechte. Stelle sicher, dass das ausführende Mitglied die entsprechenden Berechtigungen hat.

## Mitwirkende

- **Dein Name** - [Dein GitHub Profil](https://github.com/DEIN_GITHUB_PROFIL)

## Lizenz

Dieser Bot ist unter der [MIT License](LICENSE) lizenziert.

# discord-bot
