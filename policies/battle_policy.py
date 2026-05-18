import logging
import random
from pathlib import Path

import torch
from torch import nn


logger = logging.getLogger(__name__)


class BattleDQN(nn.Module):
    def __init__(self, state_size: int, action_size: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_size),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.net(state)


class BattlePolicy:
    MAX_HAND = 10
    MAX_ENEMIES = 6
    MAX_POTIONS = 5
    RELIC_BUCKETS = 32
    POWER_BUCKETS = 16
    BASE_FEATURES = 16
    ENEMY_FEATURES = 5
    CARD_FEATURES = 9
    POTION_FEATURES = 7
    STATE_SIZE = (
        BASE_FEATURES
        + MAX_ENEMIES * ENEMY_FEATURES
        + MAX_HAND * CARD_FEATURES
        + MAX_POTIONS * POTION_FEATURES
        + RELIC_BUCKETS
        + POWER_BUCKETS * 2
    )
    ACTION_SIZE = MAX_HAND + MAX_POTIONS + 1

    def __init__(
        self,
        epsilon: float = 0.05,
        checkpoint_path: str | None = "battle_dqn.pt",
        device: str | None = None,
    ):
        self.epsilon = epsilon
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = BattleDQN(self.STATE_SIZE, self.ACTION_SIZE).to(self.device)
        self.model.eval()

        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        if self.checkpoint_path and self.checkpoint_path.exists():
            try:
                self.load(self.checkpoint_path)
            except RuntimeError as exc:
                logger.warning(
                    "BattlePolicy: checkpoint %s is incompatible with current DQN shape; "
                    "using randomly initialized model. error=%s",
                    self.checkpoint_path,
                    exc,
                )
        else:
            logger.warning(
                "BattlePolicy: no DQN checkpoint found; using randomly initialized model"
            )

    def choose_action(self, state: dict) -> dict:
        if state.get("state_type") == "hand_select":
            return self._choose_hand_select_action(state)

        battle = state.get("battle", {})
        player = state.get("player", {})
        hand = player.get("hand", state.get("hand", []))
        enemies = battle.get("enemies", state.get("enemies", []))
        potions = player.get("potions", [])
        relics = player.get("relics", [])
        energy = self._parse_int(player.get("energy", state.get("energy", 0)))

        valid_action_indices = self._valid_action_indices(hand, enemies, potions, energy)
        logger.debug(
            "BattlePolicy: choosing action hand=%d enemies=%d potions=%d relics=%d energy=%s valid_actions=%s",
            len(hand),
            len(enemies),
            len(potions),
            len(relics),
            energy,
            valid_action_indices,
        )

        if not valid_action_indices:
            action = {"type": "end_turn"}
            logger.debug("BattlePolicy: selected fallback action=%s", action)
            return action

        action_index = self._choose_dqn_action(state, valid_action_indices)
        action = self._to_game_action(action_index, hand, enemies, potions)
        logger.debug("BattlePolicy: selected action_index=%d action=%s", action_index, action)
        return action

    def _choose_hand_select_action(self, state: dict) -> dict:
        hand_select = state.get("hand_select", {})
        cards = hand_select.get("cards", [])
        selected_cards = hand_select.get("selected_cards", [])
        selected_indices = {
            self._parse_int(card.get("index"))
            for card in selected_cards
        }
        mode = hand_select.get("mode")

        logger.debug(
            "BattlePolicy: choosing hand_select action mode=%s cards=%d selected=%d can_confirm=%s",
            mode,
            len(cards),
            len(selected_cards),
            hand_select.get("can_confirm"),
        )

        if hand_select.get("can_confirm"):
            action = {"type": "combat_confirm_selection"}
            logger.debug("BattlePolicy: selected action=%s", action)
            return action

        card = self._choose_hand_select_card(cards, selected_indices, mode)
        if card is None:
            action = {"type": "combat_confirm_selection"}
            logger.debug("BattlePolicy: selected fallback action=%s", action)
            return action

        action = {
            "type": "combat_select_card",
            "card_index": card.get("index", 0),
        }
        logger.debug(
            "BattlePolicy: selected hand_select card index=%s id=%s name=%s upgraded=%s",
            card.get("index"),
            card.get("id"),
            card.get("name"),
            card.get("is_upgraded"),
        )
        logger.debug("BattlePolicy: selected action=%s", action)
        return action

    def _choose_hand_select_card(
        self,
        cards: list[dict],
        selected_indices: set[int],
        mode: str | None,
    ) -> dict | None:
        available_cards = [
            card for card in cards
            if self._parse_int(card.get("index")) not in selected_indices
        ]

        if not available_cards:
            return None

        if mode == "upgrade_select":
            for card in available_cards:
                if not card.get("is_upgraded", False):
                    return card

        for card_type in ("Status", "Curse"):
            for card in available_cards:
                if card.get("type") == card_type:
                    return card

        return available_cards[0]

    def load(self, checkpoint_path: str | Path) -> None:
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        state_dict = checkpoint.get("model_state_dict", checkpoint)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        logger.info("BattlePolicy: loaded DQN checkpoint from %s", checkpoint_path)

    def save(self, checkpoint_path: str | Path | None = None) -> None:
        path = Path(checkpoint_path) if checkpoint_path else self.checkpoint_path
        if path is None:
            raise ValueError("checkpoint_path is required")
        torch.save({"model_state_dict": self.model.state_dict()}, path)
        logger.info("BattlePolicy: saved DQN checkpoint to %s", path)

    def _choose_dqn_action(self, state: dict, valid_action_indices: list[int]) -> int:
        if random.random() < self.epsilon:
            action_index = random.choice(valid_action_indices)
            logger.debug("BattlePolicy: epsilon selected action_index=%d", action_index)
            return action_index

        encoded_state = self._encode_battle_state(state)
        with torch.no_grad():
            state_tensor = torch.tensor(encoded_state, dtype=torch.float32, device=self.device)
            q_values = self.model(state_tensor.unsqueeze(0)).squeeze(0)
            invalid_mask = torch.ones(self.ACTION_SIZE, dtype=torch.bool, device=self.device)
            invalid_mask[valid_action_indices] = False
            q_values = q_values.masked_fill(invalid_mask, float("-inf"))
            action_index = int(torch.argmax(q_values).item())

        logger.debug(
            "BattlePolicy: dqn selected action_index=%d q_value=%.4f",
            action_index,
            float(q_values[action_index].item()),
        )
        return action_index

    def _to_game_action(
        self,
        action_index: int,
        hand: list[dict],
        enemies: list[dict],
        potions: list[dict],
    ) -> dict:
        if action_index == 0:
            return {"type": "end_turn"}

        if self._is_card_action(action_index):
            return self._to_card_action(action_index, hand, enemies)

        if self._is_potion_action(action_index):
            return self._to_potion_action(action_index, potions, enemies)

        logger.warning("BattlePolicy: unknown action_index=%d", action_index)
        return {"type": "end_turn"}

    def _to_card_action(self, action_index: int, hand: list[dict], enemies: list[dict]) -> dict:
        card_index = action_index - 1
        if card_index >= len(hand):
            logger.warning(
                "BattlePolicy: DQN selected out-of-range card_index=%d hand=%d",
                card_index,
                len(hand),
            )
            return {"type": "end_turn"}

        card = hand[card_index]
        target = None
        if self._requires_enemy_target(card):
            target = self._choose_target(enemies)
            if target is None:
                return {"type": "end_turn"}

        return {
            "type": "play_card",
            "card_index": card_index,
            "target": target,
        }

    def _to_potion_action(
        self,
        action_index: int,
        potions: list[dict],
        enemies: list[dict],
    ) -> dict:
        potion_index = action_index - self._potion_action_start()
        if potion_index >= len(potions):
            logger.warning(
                "BattlePolicy: DQN selected out-of-range potion_index=%d potions=%d",
                potion_index,
                len(potions),
            )
            return {"type": "end_turn"}

        potion = potions[potion_index]
        target = None
        if self._requires_enemy_target(potion):
            target = self._choose_target(enemies)
            if target is None:
                return {"type": "end_turn"}

        action = {
            "type": "use_potion",
            "slot": self._parse_int(potion.get("slot", potion_index)),
            "target": target,
        }
        logger.debug(
            "BattlePolicy: selected potion slot=%s id=%s target=%s",
            action["slot"],
            potion.get("id"),
            target,
        )
        return action

    def _valid_action_indices(
        self,
        hand: list[dict],
        enemies: list[dict],
        potions: list[dict],
        energy: int,
    ) -> list[int]:
        valid_actions = [0]
        has_target = self._choose_target(enemies) is not None

        for card_index, card in enumerate(hand[: self.MAX_HAND]):
            if not card.get("can_play", True):
                continue

            cost = self._parse_cost(card.get("cost", 0), energy)
            if cost > energy:
                continue

            if self._requires_enemy_target(card) and not has_target:
                continue

            valid_actions.append(card_index + 1)

        for potion_index, potion in enumerate(potions[: self.MAX_POTIONS]):
            if not self._can_use_potion(potion):
                continue

            if self._requires_enemy_target(potion) and not has_target:
                continue

            valid_actions.append(self._potion_action_start() + potion_index)

        return valid_actions

    def _encode_battle_state(self, state: dict) -> list[float]:
        battle = state.get("battle", {})
        player = state.get("player", {})
        hand = player.get("hand", state.get("hand", []))
        enemies = battle.get("enemies", state.get("enemies", []))
        potions = player.get("potions", [])
        relics = player.get("relics", [])
        player_status = player.get("status", [])
        enemy_status = [
            power
            for enemy in enemies
            for power in enemy.get("status", [])
        ]

        max_hp = max(1, self._parse_int(player.get("max_hp", 1)))
        hp = self._parse_int(player.get("hp", 0))
        energy = self._parse_int(player.get("energy", 0))
        max_energy = max(1, self._parse_int(player.get("max_energy", 3)))
        max_potion_slots = max(1, self._parse_int(player.get("max_potion_slots", self.MAX_POTIONS)))

        features = [
            self._scale(hp, max_hp),
            self._scale(max_hp, 100),
            self._scale(player.get("block", 0), 100),
            self._scale(energy, max_energy),
            self._scale(max_energy, 10),
            self._scale(len(hand), self.MAX_HAND),
            self._scale(player.get("draw_pile_count", 0), 50),
            self._scale(player.get("discard_pile_count", 0), 50),
            self._scale(player.get("exhaust_pile_count", 0), 50),
            self._scale(len(enemies), self.MAX_ENEMIES),
            self._scale(len(potions), max_potion_slots),
            self._scale(max_potion_slots, 6),
            self._scale(len(relics), 40),
            self._scale(len(player_status), 20),
            self._scale(sum(self._parse_int(power.get("amount", 0)) for power in player_status), 50),
            self._scale(sum(self._intent_damage(enemy) for enemy in enemies), 150),
        ]

        for enemy in enemies[: self.MAX_ENEMIES]:
            enemy_max_hp = max(1, self._parse_int(enemy.get("max_hp", 1)))
            features.extend(
                [
                    self._scale(enemy.get("hp", 0), enemy_max_hp),
                    self._scale(enemy_max_hp, 300),
                    self._scale(enemy.get("block", 0), 100),
                    self._scale(self._intent_damage(enemy), 100),
                    1.0 if self._parse_int(enemy.get("hp", 0)) > 0 else 0.0,
                ]
            )

        while len(features) < self.BASE_FEATURES + self.MAX_ENEMIES * self.ENEMY_FEATURES:
            features.append(0.0)

        for card in hand[: self.MAX_HAND]:
            features.extend(self._encode_card(card, energy))

        while len(features) < (
            self.BASE_FEATURES
            + self.MAX_ENEMIES * self.ENEMY_FEATURES
            + self.MAX_HAND * self.CARD_FEATURES
        ):
            features.append(0.0)

        for potion in potions[: self.MAX_POTIONS]:
            features.extend(self._encode_potion(potion))

        while len(features) < (
            self.BASE_FEATURES
            + self.MAX_ENEMIES * self.ENEMY_FEATURES
            + self.MAX_HAND * self.CARD_FEATURES
            + self.MAX_POTIONS * self.POTION_FEATURES
        ):
            features.append(0.0)

        features.extend(self._encode_bucket_counts(relics, self.RELIC_BUCKETS))
        features.extend(self._encode_bucket_counts(player_status, self.POWER_BUCKETS))
        features.extend(self._encode_bucket_counts(enemy_status, self.POWER_BUCKETS))

        return features[: self.STATE_SIZE]

    def _encode_card(self, card: dict, energy: int) -> list[float]:
        card_type = str(card.get("type", "")).lower()
        target_type = str(card.get("target_type", "")).lower()
        cost = self._parse_cost(card.get("cost", 0), energy)

        return [
            1.0 if card.get("can_play", True) else 0.0,
            self._scale(cost, 5),
            1.0 if card.get("is_upgraded", False) else 0.0,
            1.0 if card_type == "attack" else 0.0,
            1.0 if card_type == "skill" else 0.0,
            1.0 if card_type == "power" else 0.0,
            1.0 if card_type in {"status", "curse"} else 0.0,
            1.0 if "enemy" in target_type else 0.0,
            1.0 if "all" in target_type else 0.0,
        ]

    def _encode_potion(self, potion: dict) -> list[float]:
        target_type = str(potion.get("target_type", "")).lower()

        return [
            1.0,
            1.0 if self._can_use_potion(potion) else 0.0,
            self._scale(potion.get("slot", 0), self.MAX_POTIONS),
            1.0 if "enemy" in target_type else 0.0,
            1.0 if "self" in target_type or target_type == "none" else 0.0,
            1.0 if "ally" in target_type or "player" in target_type else 0.0,
            self._scale(self._stable_bucket(potion.get("id") or potion.get("name"), 100), 100),
        ]

    def _encode_bucket_counts(self, items: list[dict], bucket_count: int) -> list[float]:
        buckets = [0.0 for _ in range(bucket_count)]
        for item in items:
            item_id = item.get("id") or item.get("name")
            bucket = self._stable_bucket(item_id, bucket_count)
            amount = max(1, self._parse_int(item.get("amount", 1)))
            buckets[bucket] += amount

        return [min(value / 10.0, 1.0) for value in buckets]

    def _choose_target(self, enemies: list[dict]) -> str | None:
        alive_enemies = [
            enemy for enemy in enemies
            if self._parse_int(enemy.get("hp", 0)) > 0
        ]

        if not alive_enemies:
            return None

        target_enemy = min(alive_enemies, key=lambda e: self._parse_int(e.get("hp", 0)))
        target = target_enemy.get("entity_id") or target_enemy.get("id")
        logger.debug(
            "BattlePolicy: selected target id=%s hp=%s",
            target,
            target_enemy.get("hp"),
        )
        return target

    def _requires_enemy_target(self, item: dict) -> bool:
        if item.get("requires_target", False):
            return True

        target_type = str(item.get("target_type", ""))
        return target_type in {"AnyEnemy", "Enemy"}

    def _can_use_potion(self, potion: dict) -> bool:
        if not potion:
            return False
        return bool(potion.get("can_use_in_combat", True))

    def _potion_action_start(self) -> int:
        return self.MAX_HAND + 1

    def _is_card_action(self, action_index: int) -> bool:
        return 1 <= action_index < self._potion_action_start()

    def _is_potion_action(self, action_index: int) -> bool:
        return self._potion_action_start() <= action_index < self.ACTION_SIZE

    def _parse_cost(self, cost: object, energy: int) -> int:
        if cost is None:
            return 0
        if isinstance(cost, str) and cost.upper() == "X":
            return energy
        return self._parse_int(cost)

    def _parse_int(self, value: object, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _intent_damage(self, enemy: dict) -> int:
        total = 0
        for intent in enemy.get("intents", []):
            label = str(intent.get("label", ""))
            if label.isdigit():
                total += int(label)
        return total

    def _scale(self, value: object, denominator: int | float) -> float:
        denominator = max(float(denominator), 1.0)
        return max(0.0, min(float(self._parse_int(value)) / denominator, 1.0))

    def _stable_bucket(self, value: object, bucket_count: int) -> int:
        if bucket_count <= 0:
            return 0
        text = str(value or "")
        total = 0
        for character in text:
            total = (total * 31 + ord(character)) % bucket_count
        return total
