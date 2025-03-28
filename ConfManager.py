import json
import os


class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config_cache = {
            "roles": {},
            "name_prefix": "",
            "name_postfix": "",
            "events": [],
            "server": {
                "name": "",
                "id": 0,
                "channel": {
                    "pvp": [],
                    "pve": []
                }
            }
        }
        self.load_config()

    def load_config(self):
        """Lädt die Konfiguration aus der Datei in den Cache."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    self.config_cache = json.load(file)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Fehler beim Laden der Konfiguration: {e}")

    def save_config(self):
        """Speichert den aktuellen Cache in die Datei."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(self.config_cache, file, indent=4)
        except IOError as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")

    def get(self, key, default=None):
        """Gibt den Wert eines Konfigurationsschlüssels zurück oder den Standardwert."""
        return self.config_cache.get(key, default)

    def set(self, key, value):
        """Setzt einen Wert in der Konfiguration und speichert ihn direkt."""
        self.config_cache[key] = value
        self.save_config()

    def delete(self, key):
        """Löscht einen Schlüssel aus der Konfiguration und speichert die Änderung."""
        if key in self.config_cache:
            del self.config_cache[key]
            self.save_config()


# Beispiel-Nutzung
if __name__ == "__main__":
    config = ConfigManager()
    config.set("roles", {"manager": 1307003061369045032, "member": 638795102361354260})
    print(config.get("roles"))  # Gibt die Rollen aus
    config.delete("roles")
    print(config.get("roles", "Nicht gefunden"))  # Gibt "Nicht gefunden" aus
    config.set("roles", {"manager": 1307003061369045032, "member": 638795102361354260})
    event = next(
        (event for event in config.config_cache.get("events", []) if event.get("id") == 2),
        None)
    print(event)
    print(event.get("name"))
    print(event.get("reward"))
    print(event.get("weekly"))
