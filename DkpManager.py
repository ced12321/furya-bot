import json

DKP_JSON_FILE_NAME = "dkp.json"
DKP_CACHE_WEEKLY_KEY = "weekly_dkp"
DKP_CACHE_DKP_KEY = "dkp"


class DkpManager:
    def __init__(self):
        self.dkp_cache = []

    def _import_dkp(self):
        with open(DKP_JSON_FILE_NAME, "r") as file:
            self.dkp_cache = json.load(file)

    def export_dkp(self):
        with open(DKP_JSON_FILE_NAME, "w") as file:
            json.dump(self.dkp_cache, file, indent=4)

    def import_data_if_empty(self):
        if not self.dkp_cache:
            self._import_dkp()

    def find_by_id(self, user_id):
        for dkp in self.dkp_cache:
            if dkp["id"] == str(user_id):
                return dkp
        return None

    def add_dkp(self, user_id, amount):
        self._set_by_id(user_id, amount, weekly=False)

    def add_weekly(self, user_id, amount):
        self._set_by_id(user_id, amount, weekly=True)

    def compute_end_of_week(self, reputation):
        for dkp in self.dkp_cache:
            dkp[DKP_CACHE_WEEKLY_KEY] += reputation.get(dkp["id"], 0)
            dkp[DKP_CACHE_DKP_KEY] += dkp[DKP_CACHE_WEEKLY_KEY] if dkp[DKP_CACHE_WEEKLY_KEY] <= 60 else 60
            dkp[DKP_CACHE_DKP_KEY] = int(dkp[DKP_CACHE_DKP_KEY])
            dkp[DKP_CACHE_WEEKLY_KEY] = 0

    def _set_by_id(self, user_id, dkp, weekly: bool):
        if self.find_by_id(user_id) is None:
            self.dkp_cache.append(
                {"id": str(user_id), DKP_CACHE_WEEKLY_KEY: dkp,
                 DKP_CACHE_DKP_KEY: 0}) if weekly else self.dkp_cache.append(
                {"id": str(user_id), DKP_CACHE_WEEKLY_KEY: 0, DKP_CACHE_DKP_KEY: dkp})
        else:
            entry_key = DKP_CACHE_WEEKLY_KEY if weekly else DKP_CACHE_DKP_KEY
            for dkp_entry in self.dkp_cache:
                if dkp_entry["id"] == str(user_id):
                    dkp_entry[entry_key] = dkp_entry[entry_key] + dkp
