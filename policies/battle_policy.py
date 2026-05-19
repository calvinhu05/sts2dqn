import logging


logger = logging.getLogger(__name__)


class BattlePolicy:
    """
    Minimal rule-based combat policy for engine smoke testing.

    This intentionally avoids learning, scoring, potions, and complex card text.
    It only tries to produce valid combat actions so the game loop can be tested.
    """

    def __init__(self, *args, **kwargs):
        pass

    def choose_action(self, state: dict) -> dict:
        if state.get("state_type") == "hand_select":
            return self._choose_hand_select_action(state)

        player = state.get("player", {})
        battle = state.get("battle", {})
        hand = player.get("hand", state.get("hand", []))
        enemies = battle.get("enemies", state.get("enemies", []))
        energy = self._parse_int(player.get("energy", state.get("energy", 0)))

        logger.debug(
            "BattlePolicy: choosing simple action hand=%d enemies=%d energy=%s",
            len(hand),
            len(enemies),
            energy,
        )

        target = self._first_alive_enemy_id(enemies)
        for card_index, card in enumerate(hand):
            if not self._is_playable_card(card, energy):
                continue

            if self._requires_enemy_target(card) and target is None:
                continue

            action = {
                "type": "play_card",
                "card_index": card_index,
                "target": target if self._requires_enemy_target(card) else None,
            }
            logger.debug(
                "BattlePolicy: selected card index=%s id=%s name=%s action=%s",
                card_index,
                card.get("id"),
                card.get("name"),
                action,
            )
            return action

        action = {"type": "end_turn"}
        logger.debug("BattlePolicy: no playable card; selected action=%s", action)
        return action

    def _choose_hand_select_action(self, state: dict) -> dict:
        hand_select = state.get("hand_select", {})
        if hand_select.get("can_confirm"):
            action = {"type": "combat_confirm_selection"}
            logger.debug("BattlePolicy: hand_select can confirm; selected action=%s", action)
            return action

        selected_indices = {
            self._parse_int(card.get("index"))
            for card in hand_select.get("selected_cards", [])
        }
        for card in hand_select.get("cards", []):
            card_index = self._parse_int(card.get("index"))
            if card_index not in selected_indices:
                action = {
                    "type": "combat_select_card",
                    "card_index": card_index,
                }
                logger.debug("BattlePolicy: selected hand_select action=%s", action)
                return action

        action = {"type": "combat_confirm_selection"}
        logger.debug("BattlePolicy: hand_select fallback action=%s", action)
        return action

    def _is_playable_card(self, card: dict, energy: int) -> bool:
        if not card.get("can_play", True):
            return False

        if str(card.get("type", "")).lower() in {"status", "curse"}:
            return False

        return self._parse_cost(card.get("cost", 0), energy) <= energy

    def _requires_enemy_target(self, item: dict) -> bool:
        if item.get("requires_target", False):
            return True

        target_type = str(item.get("target_type", "")).lower()
        return target_type in {"anyenemy", "enemy"}

    def _first_alive_enemy_id(self, enemies: list[dict]) -> str | None:
        for enemy in enemies:
            if self._parse_int(enemy.get("hp", 0)) > 0:
                return enemy.get("entity_id") or enemy.get("id")
        return None

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
