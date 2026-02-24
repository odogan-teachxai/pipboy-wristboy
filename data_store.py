"""Data persistence layer for the wrist device."""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

DATA_FILE = "watch_data.json"


class DataStore:
    """Manages persistent storage of device data."""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load data from JSON file or create defaults."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_data()

    def _default_data(self) -> Dict[str, Any]:
        """Return default data structure."""
        return {
            "stats": {
                "hydration": 75,
                "energy": 80,
                "urination": 30,
                "stress": 25
            },
            "inventory": [
                {
                    "name": "Phone",
                    "category": "Electronics",
                    "quantity": 1,
                    "weight": 0.2
                },
                {
                    "name": "Wallet",
                    "category": "Essentials",
                    "quantity": 1,
                    "weight": 0.1
                },
                {
                    "name": "Keys",
                    "category": "Essentials",
                    "quantity": 1,
                    "weight": 0.05
                }
            ],
            "settings": {
                "device_name": "WristComp v1.0",
                "auto_save": True,
                "compact_mode": False
            },
            "last_updated": datetime.now().isoformat()
        }

    def save(self) -> None:
        """Save current data to JSON file."""
        self._data["last_updated"] = datetime.now().isoformat()
        with open(self.filepath, 'w') as f:
            json.dump(self._data, f, indent=2)

    # Stats accessors
    @property
    def stats(self) -> Dict[str, int]:
        return self._data.get("stats", {})

    def get_stat(self, name: str) -> int:
        return self.stats.get(name, 0)

    def set_stat(self, name: str, value: int) -> None:
        self._data["stats"][name] = max(0, min(100, value))
        if self._data["settings"].get("auto_save", True):
            self.save()

    def update_stat(self, name: str, delta: int) -> None:
        current = self.get_stat(name)
        self.set_stat(name, current + delta)

    # Inventory accessors
    @property
    def inventory(self) -> List[Dict[str, Any]]:
        return self._data.get("inventory", [])

    def add_item(self, name: str, category: str, quantity: int, weight: float) -> None:
        """Add a new EDC item or update an existing one."""
        for item in self._data["inventory"]:
            if item["name"].lower() == name.lower():
                item["category"] = category
                item["quantity"] = quantity
                item["weight"] = weight
                if self._data["settings"].get("auto_save", True):
                    self.save()
                return
        self._data["inventory"].append({
            "name": name,
            "category": category,
            "quantity": quantity,
            "weight": weight
        })
        if self._data["settings"].get("auto_save", True):
            self.save()

    def update_item(self, original_name: str, name: str, category: str, quantity: int, weight: float) -> bool:
        """Update an existing item by name."""
        for item in self._data["inventory"]:
            if item["name"] == original_name:
                item["name"] = name
                item["category"] = category
                item["quantity"] = quantity
                item["weight"] = weight
                if self._data["settings"].get("auto_save", True):
                    self.save()
                return True
        return False

    def remove_item(self, name: str) -> bool:
        """Remove an item by name."""
        for item in self._data["inventory"]:
            if item["name"] == name:
                self._data["inventory"].remove(item)
                if self._data["settings"].get("auto_save", True):
                    self.save()
                return True
        return False

    def get_item(self, name: str) -> Optional[Dict[str, Any]]:
        """Get an item by name."""
        for item in self._data["inventory"]:
            if item["name"] == name:
                return item
        return None

    # Settings accessors
    @property
    def settings(self) -> Dict[str, Any]:
        return self._data.get("settings", {})

    def get_setting(self, key: str) -> Any:
        return self.settings.get(key)

    def set_setting(self, key: str, value: Any) -> None:
        self._data["settings"][key] = value
        if self._data["settings"].get("auto_save", True):
            self.save()

    def reset_stats(self) -> None:
        """Reset all stats to default values."""
        self._data["stats"] = {
            "hydration": 75,
            "energy": 80,
            "urination": 30,
            "stress": 25
        }
        self.save()

    def reset_all(self) -> None:
        """Reset everything to defaults."""
        self._data = self._default_data()
        self.save()