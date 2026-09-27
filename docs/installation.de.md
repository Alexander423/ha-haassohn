# Installation mit HACS

Voraussetzung: Home Assistant **2026.9 oder neuer**, HACS und ein unterstütztes
älteres HAAS+SOHN-WLAN-Modul mit KS01/status.cgi. APP V1.2.5 allein bestätigt die
Kompatibilität nicht. Die Integration wurde bisher mit Emulatoren getestet.

1. In HACS das Menü und **Benutzerdefinierte Repositories** öffnen.
2. `https://github.com/Alexander423/ha-haassohn` eintragen und **Integration** wählen.
3. **HAAS+SOHN Local** suchen und herunterladen. Für Vorabversionen gegebenenfalls
   **Beta-Versionen anzeigen** aktivieren; alternativ den Standardbranch wählen.
4. Home Assistant vollständig neu starten.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen → HAAS+SOHN**.
6. Lokale IP-Adresse ohne `http://` und die vierstellige APP-PIN eingeben.
   Führende Nullen gehören zur PIN.

Die Einrichtung liest ausschließlich. Eine falsche PIN wird erst durch einen
abgewiesenen Steuerbefehl erkannt. Zuerst Temperatur und Status mit dem Display
vergleichen. Die erste Bedienung beaufsichtigt direkt am Ofen testen. Unbekannte
Controller-Firmware bleibt absichtlich nur lesbar.

## Updates und Fehler

Updates werden über HACS installiert; anschließend Home Assistant neu starten.
IP und PIN lassen sich über **Neu konfigurieren** ändern. Bei Problemen zunächst
Netzwerk, HA-Version und Controller-Firmware prüfen. Fehlerberichte über GitHub
mit der Vorlage und ausschließlich bereinigten Diagnosedaten erstellen.

Keine PIN, IP-Adresse, Seriennummer oder rohe HTTP-Antwort veröffentlichen.

## Manuelle Alternative

Das Integrations-ZIP aus einem Release im HA-Konfigurationsordner entpacken,
neben `configuration.yaml`. Danach muss
`custom_components/haassohn/manifest.json` vorhanden sein; `_vendor` mitkopieren.
Bei Home Assistant Container ist dies der Host-Ordner, der nach `/config`
eingebunden ist. Danach neu starten und die Integration wie oben hinzufügen.
