import json
import os


class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config_cache = {
            "roles": {},
            "events": [],
            "server": {
                "name": "",
                "id": 0,
                "name_prefix": "",
                "name_postfix": "",
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

    def add_server(self, name, server_id):
        """Fügt einen Server hinzu."""
        self.config_cache["server"].append(
            {"name": name, "id": server_id, "channel": {"pvp": [], "pve": []}, "name_prefix": "", "name_postfix": ""})
        self.save_config()

    def delete_server(self, server_id):
        """Löscht einen Server aus der Konfiguration."""
        self.config_cache["server"] = [server for server in self.config_cache["server"] if
                                       server["id"] != server_id]
        self.save_config()

    def set_prefix(self, server_id: int, prefix: str):
        for server in self.config_cache["server"]:
            if server["id"] == server_id:
                server["name_prefix"] = prefix
                self.save_config()
                return
    def set_postfix(self, server_id: int, postfix: str):
        for server in self.config_cache["server"]:
            if server["id"] == server_id:
                server["name_prefix"] = postfix
                self.save_config()
                return

    def add_channel(self, server_id, channel_id, is_pvp=True):
        """Fügt einen Channel zu einem bestimmten Server hinzu."""
        channel_type = "pvp" if is_pvp else "pve"
        for server in self.config_cache["server"]:
            if server["id"] == server_id:
                if channel_id not in server["channel"][channel_type]:
                    server["channel"][channel_type].append(channel_id)
                self.save_config()
                return

    def delete_channel(self, server_id, channel_id):
        """Löscht einen Channel aus einem bestimmten Server."""
        for server in self.config_cache["server"]:
            if server["id"] == server_id:
                if channel_id in server["channel"]["pvp"]:
                    server["channel"]["pvp"].remove(channel_id)
                if channel_id in server["channel"]["pve"]:
                    server["channel"]["pve"].remove(channel_id)
                self.save_config()
                return

    def add_event(self, event_id, name, reward, weekly):
        """Fügt ein Event zur Konfiguration hinzu."""
        event = {"id": event_id, "name": name, "reward": reward, "weekly": weekly}
        self.config_cache["events"].append(event)
        self.save_config()

    def delete_event(self, event_id):
        """Löscht ein Event aus der Konfiguration."""
        self.config_cache["events"] = [event for event in self.config_cache["events"] if event["id"] != event_id]
        self.save_config()

    def get_event_by_id(self, event_id):
        """Gibt das Event mit der angegebenen ID zurück oder None, falls nicht gefunden."""
        return next((event for event in self.config_cache.get("events", []) if event.get("id") == event_id), None)


# Beispiel-Nutzung
if __name__ == "__main__":
    config = ConfigManager()
    config.add_server("Polaris-Main", 395072012181045260)
    config.add_channel(395072012181045260, 1289970145002913802, is_pvp=True)
    print(config.get_event_by_id(2))
