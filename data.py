from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class CardInstance:
    card_id: str
    regular_cost: int = 0
    star_cost: int = 0
    upgraded: bool = False

    def upgrade(self) -> None:
        self.upgraded = True

    def update_regular_cost(self, new_cost: int) -> None:
        self.regular_cost = new_cost

    def update_star_cost(self, new_star_cost: int) -> None:
        self.star_cost = new_star_cost

class DataStore:
    data_dir = Path("data")
    data: dict[str, dict[str, dict]] = {}
    loaded = False

    @classmethod
    def load_all(cls, data_dir: str = "data") -> None:
        cls.data_dir = Path(data_dir)
        cls.data.clear()

        for file_path in cls.data_dir.glob("*.json"):
            data_type = file_path.stem

            with file_path.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                continue

            cls.data[data_type] = {}

            for obj in raw_data:
                if isinstance(obj, dict) and "id" in obj:
                    cls.data[data_type][obj["id"]] = obj

        cls.loaded = True

    @classmethod
    def ensure_loaded(cls) -> None:
        if not cls.loaded:
            cls.load_all()

    @classmethod
    def get(cls, data_type: str, item_id: str) -> dict:
        cls.ensure_loaded()

        if data_type not in cls.data:
            raise KeyError(f"Unknown data type: {data_type}")

        if item_id not in cls.data[data_type]:
            raise KeyError(f"Unknown id '{item_id}' in {data_type}")

        return cls.data[data_type][item_id]


class DataIdMap:
    data_dir = Path("data")
    id_maps: dict[str, dict[str, int]] = {}
    loaded = False

    @classmethod
    def load_all(cls, data_dir: str = "data") -> None:
        cls.data_dir = Path(data_dir)
        cls.id_maps.clear()

        for file_path in cls.data_dir.glob("*.json"):
            data_type = file_path.stem

            with file_path.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                continue

            id_map = {}

            for obj in raw_data:
                if isinstance(obj, dict) and "id" in obj:
                    item_id = obj["id"]

                    if item_id not in id_map:
                        id_map[item_id] = len(id_map)

            cls.id_maps[data_type] = id_map

        cls.loaded = True

    @classmethod
    def ensure_loaded(cls) -> None:
        if not cls.loaded:
            cls.load_all()

    @classmethod
    def get_index(cls, data_type: str, item_id: str) -> int:
        cls.ensure_loaded()
        return cls.id_maps[data_type][item_id]

    @classmethod
    def get_id_map(cls, data_type: str) -> dict[str, int]:
        cls.ensure_loaded()
        return cls.id_maps[data_type]
    

def load_card(card: dict) -> CardInstance:
    card_id = card.get("id")
    upgraded = card.get("is_upgraded", False)

    regular_cost = card.get("cost", 0)
    star_cost = card.get("star_cost", 0)

    return CardInstance(
        card_id=card_id,
        regular_cost=regular_cost,
        star_cost=star_cost,
        upgraded=upgraded,
    )
# data_map = DataIdMap()

# cards_map = data_map.get_id_map("cards")
# relics_map = data_map.get_id_map("relics")
# enchancements_map = data_map.get_id_map("enchantments")

# print("Cards map(len:{}):".format(len(cards_map)), cards_map)
# print("\nRelics map(len:{}):".format(len(relics_map)), relics_map)
# print("\nEnchantments map(len:{}):".format(len(enchancements_map)), enchancements_map)
# print(data_map.get_index("cards", "strike"))