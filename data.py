from dataclasses import dataclass
from pathlib import Path
import json


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"


DATA_TYPE_ALIASES = {
    "act": "acts",
    "ascension": "ascensions",
    "card": "cards",
    "character": "characters",
    "enchantment": "enchantments",
    "encounter": "encounters",
    "event": "events",
    "intent": "intents",
    "keyword": "keywords",
    "modifier": "modifiers",
    "monster": "monsters",
    "orb": "orbs",
    "potion": "potions",
    "power": "powers",
    "relic": "relics",
}


def normalize_data_type(data_type: str) -> str:
    normalized = data_type.strip().lower()
    return DATA_TYPE_ALIASES.get(normalized, normalized)


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
    data_dir = DEFAULT_DATA_DIR
    data: dict[str, dict[str, dict]] = {}
    loaded = False

    @classmethod
    def load_all(cls, data_dir: str | Path = DEFAULT_DATA_DIR) -> None:
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
        data_type = normalize_data_type(data_type)

        if data_type not in cls.data:
            raise KeyError(f"Unknown data type: {data_type}")

        if item_id not in cls.data[data_type]:
            raise KeyError(f"Unknown id '{item_id}' in {data_type}")

        return cls.data[data_type][item_id]


class DataIdMap:
    data_dir = DEFAULT_DATA_DIR
    id_maps: dict[str, dict[str, int]] = {}
    lookup_maps: dict[str, dict[str, int]] = {}
    reverse_id_maps: dict[str, dict[int, str]] = {}
    loaded = False

    @classmethod
    def load_all(cls, data_dir: str | Path = DEFAULT_DATA_DIR) -> None:
        cls.data_dir = Path(data_dir)
        cls.id_maps.clear()
        cls.lookup_maps.clear()
        cls.reverse_id_maps.clear()

        for file_path in cls.data_dir.glob("*.json"):
            data_type = file_path.stem

            with file_path.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                continue

            id_map = {}
            lookup_map = {}

            for obj in raw_data:
                if isinstance(obj, dict) and "id" in obj:
                    item_id = str(obj["id"])

                    if item_id not in id_map:
                        id_map[item_id] = len(id_map)

                    item_index = id_map[item_id]
                    cls._add_lookup_key(lookup_map, item_id, item_index)
                    cls._add_lookup_key(lookup_map, obj.get("name"), item_index)

            cls.id_maps[data_type] = id_map
            cls.lookup_maps[data_type] = lookup_map
            cls.reverse_id_maps[data_type] = {
                index: item_id for item_id, index in id_map.items()
            }

        cls.loaded = True

    @classmethod
    def ensure_loaded(cls) -> None:
        if not cls.loaded:
            cls.load_all()

    @classmethod
    def get_index(cls, data_type: str, item_id: str) -> int:
        cls.ensure_loaded()
        data_type = normalize_data_type(data_type)
        if item_id in cls.id_maps[data_type]:
            return cls.id_maps[data_type][item_id]
        return cls.lookup_maps[data_type][cls._lookup_key(item_id)]

    @classmethod
    def get_index_or_default(
        cls,
        data_type: str,
        item_id: str | None,
        default: int = -1,
    ) -> int:
        cls.ensure_loaded()
        data_type = normalize_data_type(data_type)
        if item_id is None:
            return default
        if item_id in cls.id_maps.get(data_type, {}):
            return cls.id_maps[data_type][item_id]
        return cls.lookup_maps.get(data_type, {}).get(cls._lookup_key(item_id), default)

    @classmethod
    def get_id_map(cls, data_type: str) -> dict[str, int]:
        cls.ensure_loaded()
        data_type = normalize_data_type(data_type)
        return cls.id_maps[data_type]

    @classmethod
    def get_reverse_id_map(cls, data_type: str) -> dict[int, str]:
        cls.ensure_loaded()
        data_type = normalize_data_type(data_type)
        return cls.reverse_id_maps[data_type]

    @classmethod
    def get_id(cls, data_type: str, index: int) -> str:
        cls.ensure_loaded()
        data_type = normalize_data_type(data_type)
        return cls.reverse_id_maps[data_type][index]

    @classmethod
    def get_size(cls, data_type: str) -> int:
        cls.ensure_loaded()
        data_type = normalize_data_type(data_type)
        return len(cls.id_maps[data_type])

    @classmethod
    def get_all_maps(cls) -> dict[str, dict[str, int]]:
        cls.ensure_loaded()
        return cls.id_maps

    @classmethod
    def _add_lookup_key(
        cls,
        lookup_map: dict[str, int],
        key: object,
        index: int,
    ) -> None:
        if key is None:
            return
        lookup_map.setdefault(cls._lookup_key(str(key)), index)

    @staticmethod
    def _lookup_key(value: str) -> str:
        return value.strip().replace(" ", "_").replace("-", "_").upper()


def get_data_map(data_type: str) -> dict[str, int]:
    return DataIdMap.get_id_map(data_type)


def get_data_index(data_type: str, item_id: str) -> int:
    return DataIdMap.get_index(data_type, item_id)


def get_data_index_or_default(
    data_type: str,
    item_id: str | None,
    default: int = -1,
) -> int:
    return DataIdMap.get_index_or_default(data_type, item_id, default)


def get_data_map_size(data_type: str) -> int:
    return DataIdMap.get_size(data_type)


def get_card_index(card_id: str | None, default: int = -1) -> int:
    return get_data_index_or_default("cards", card_id, default)


def get_power_index(power_id: str | None, default: int = -1) -> int:
    return get_data_index_or_default("powers", power_id, default)


def get_intent_index(intent_id: str | None, default: int = -1) -> int:
    return get_data_index_or_default("intents", intent_id, default)


def get_relic_index(relic_id: str | None, default: int = -1) -> int:
    return get_data_index_or_default("relics", relic_id, default)


def get_potion_index(potion_id: str | None, default: int = -1) -> int:
    return get_data_index_or_default("potions", potion_id, default)
    

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
