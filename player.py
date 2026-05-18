from data import DataStore, DataIdMap, CardInstance, load_card


CHARACTER_MAP = {
    0: "IRONCLAD",
    1: "SILENT",
    2: "REGENT",
    3: "NECROBINDER",
    4: "DEFECT",
}


class Player:
    def __init__(self, character: int = 0):
        if character not in CHARACTER_MAP:
            raise ValueError(f"Invalid character index: {character}")

        self.character: int = character
        self.character_id: str = CHARACTER_MAP[character]

        character_data = DataStore.get("characters", self.character_id)

        self.max_hp: int = character_data.get("starting_hp", 0)
        self.current_hp: int = self.max_hp

        self.gold: int = character_data.get("starting_gold", 0)

        self.max_energy: int = character_data.get("max_energy", 3)
        self.current_energy: int = self.max_energy

        self.current_deck: list[CardInstance] = []
        self.current_relic: list[int] = []
        self.potion: list[int] = []

        # Defect's orb slots
        self.orb_slot: list[int] = []

        self.buffs: dict[int, int] = {}
        self.block: int = 0

        self.load_starting_deck(character_data)
        self.load_starting_relics(character_data)
        self.load_orb_slots(character_data)

    def load_starting_deck(self, character_data: dict) -> None:
        starting_deck = character_data.get("starting_deck", [])

        for card_id in starting_deck:
            card_data = DataStore.get("cards", card_id)
            card_instance = load_card(card_data)
            self.current_deck.append(card_instance)

    def load_starting_relics(self, character_data: dict) -> None:
        starting_relics = character_data.get("starting_relics", [])

        for relic_id in starting_relics:
            relic_index = DataIdMap.get_index("relics", relic_id)
            self.current_relic.append(relic_index)

    def load_orb_slots(self, character_data: dict) -> None:
        orb_slots = character_data.get("orb_slots")

        if orb_slots is None:
            self.orb_slot = []
        else:
            self.orb_slot = [0 for _ in range(orb_slots)]

    def add_card(self, card_id: str) -> None:
        card_data = DataStore.get("cards", card_id)
        card_instance = load_card(card_data)
        self.current_deck.append(card_instance)

    def add_relic(self, relic_id: str) -> None:
        relic_index = DataIdMap.get_index("relics", relic_id)
        self.current_relic.append(relic_index)

    def add_potion(self, potion_id: str) -> None:
        potion_index = DataIdMap.get_index("potions", potion_id)
        self.potion.append(potion_index)

    def take_damage(self, amount: int) -> None:
        damage_after_block = max(0, amount - self.block)
        self.block = max(0, self.block - amount)
        self.current_hp = max(0, self.current_hp - damage_after_block)

    def heal(self, amount: int) -> None:
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def gain_block(self, amount: int) -> None:
        self.block += amount

    def reset_block(self) -> None:
        self.block = 0

    def reset_energy(self) -> None:
        self.current_energy = self.max_energy

    def spend_energy(self, amount: int) -> bool:
        if self.current_energy < amount:
            return False

        self.current_energy -= amount
        return True

    def add_buff(self, buff_id: int, amount: int) -> None:
        self.buffs[buff_id] = self.buffs.get(buff_id, 0) + amount

    def remove_buff(self, buff_id: int) -> None:
        if buff_id in self.buffs:
            del self.buffs[buff_id]

    def is_dead(self) -> bool:
        return self.current_hp <= 0