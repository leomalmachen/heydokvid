# 🖥️ Bildschirmfreigabe (Screen Sharing) - HeyDok Video

## Übersicht

Die HeyDok Video Platform unterstützt jetzt vollständige Bildschirmfreigabe sowohl für Ärzte als auch für Patienten. Diese Funktion ermöglicht es, Bildschirminhalte, Anwendungen oder Browser-Tabs in Echtzeit zu teilen.

## ✨ Funktionen

### Für Ärzte
- **Medizinische Aufklärung**: Teilen von Diagnoseergebnissen, Röntgenbildern oder medizinischen Informationen
- **Dokumentenerklärung**: Gemeinsame Durchsicht von Behandlungsplänen oder Formularen
- **Software-Demonstration**: Zeigen von medizinischen Anwendungen oder Portalen

### Für Patienten
- **Symptom-Dokumentation**: Teilen von Apps oder Websites mit Symptomtagebüchern
- **Unterlagen zeigen**: Präsentation von bereits vorhandenen medizinischen Dokumenten
- **Technische Unterstützung**: Hilfe bei der Nutzung medizinischer Apps oder Portale

## 🚀 Verwendung

### Bildschirmfreigabe starten
1. Klicken Sie auf das **Bildschirm teilen** Symbol (🖥️) in der Kontrollleiste
2. Wählen Sie aus:
   - **Gesamter Bildschirm**: Teilt den kompletten Desktop
   - **Anwendungsfenster**: Teilt nur eine bestimmte Anwendung
   - **Browser-Tab**: Teilt nur einen spezifischen Browser-Tab
3. Klicken Sie auf "Teilen" zur Bestätigung

### Bildschirmfreigabe beenden
- Klicken Sie erneut auf das **Bildschirm teilen** Symbol
- Oder verwenden Sie die Browser-Benachrichtigung "Freigabe beenden"

## 🔧 Technische Details

### Browser-Unterstützung
- ✅ Chrome 72+
- ✅ Firefox 67+
- ✅ Safari 13+
- ✅ Edge 79+

### Systemanforderungen
- **Audio-Freigabe**: Optional, automatisch erkannt
- **Berechtigungen**: Browser fragt automatisch nach Bildschirmzugriff
- **Qualität**: Automatische Anpassung je nach Verbindungsgeschwindigkeit

### Sicherheit
- **DSGVO-konform**: Alle Streams sind Ende-zu-Ende verschlüsselt
- **Keine Aufzeichnung**: Bildschirmfreigaben werden nicht gespeichert
- **Nutzer-Kontrolle**: Jederzeit sofort beendbar

## 🎯 Anwendungsfälle

### Medizinische Sprechstunde
```
Arzt teilt Bildschirm → Zeigt Befunde → Patient versteht besser
```

### Patientenberatung
```
Patient teilt App → Arzt sieht Problem → Direkte Anleitung möglich
```

### Telemedizin-Workflow
```
1. Normale Video-Sprechstunde beginnen
2. Bei Bedarf Bildschirm teilen
3. Gemeinsame Dokumentendurchsicht
4. Bildschirmfreigabe beenden
5. Normale Gesprächsfortsetzung
```

## 🛠️ API-Integration

Die Bildschirmfreigabe funktioniert automatisch mit den bestehenden Meeting-Endpoints:

```bash
# Meeting erstellen
POST /api/external/create-meeting-link
{
  "doctor_name": "Dr. Schmidt",
  "external_id": "TERMIN-001"
}

# Response enthält Links mit Screen-Share-Berechtigung
{
  "doctor_join_url": "https://heyvid.../meeting/xyz?role=doctor",
  "patient_join_url": "https://heyvid.../patient-setup?meeting=xyz"
}
```

## 🔍 Fehlerbehebung

### Häufige Probleme

**"Bildschirmfreigabe nicht verfügbar"**
- Browser aktualisieren auf neueste Version
- HTTPS-Verbindung prüfen (HTTP wird nicht unterstützt)
- Pop-up-Blocker deaktivieren

**"Berechtigung verweigert"**
- Browser-Berechtigungen überprüfen
- Seite neu laden und erneut versuchen
- In Browser-Einstellungen Kamera/Mikrofon erlauben

**"Schlechte Qualität"**
- Netzwerkverbindung prüfen
- Andere Anwendungen schließen
- Kleineres Fenster statt ganzen Bildschirm teilen

### Debug-Informationen
Im Browser-Entwicklertools (F12) nach folgenden Logs suchen:
```
🖥️ Screen share started successfully
🖥️ Screen share track published to LiveKit
✅ Screen sharing started successfully
```

## 💡 Best Practices

### Für Ärzte
- **Vorbereitung**: Dokumente im Voraus öffnen
- **Qualität**: Großen Text und klare Bilder verwenden
- **Datenschutz**: Persönliche Bereiche des Bildschirms abdecken
- **Browser-Tab**: Nur spezifische Tabs teilen statt ganzen Bildschirm

### Für Patienten
- **Unterstützung**: Bei Problemen um Hilfe bitten
- **Privatsphäre**: Persönliche Informationen ausblenden
- **Einfachheit**: Nur das teilen, was relevant ist

## 📞 Support

Bei Fragen oder Problemen:
- **E-Mail**: support@heydok.com
- **Dokumentation**: Vollständige API-Docs verfügbar
- **Technischer Support**: 24/7 verfügbar für medizinische Einrichtungen 