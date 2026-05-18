import logging


logger = logging.getLogger(__name__)


class MapPolicy:
    def choose_action(self, state: dict) -> dict:
        map_state = state.get("map", {})
        nodes = map_state.get("next_options", state.get("next_options", []))
        logger.debug("MapPolicy: choosing action next_options=%d", len(nodes))

        if not nodes:
            action = {
                "type": "proceed"
            }
            logger.debug("MapPolicy: selected action=%s", action)
            return action

        # Go left most node.
        node = nodes[0]
        action = {
            "type": "choose_map_node",
            "index": node.get("index", 0),
        }
        logger.debug(
            "MapPolicy: selected node index=%s type=%s col=%s row=%s",
            node.get("index"),
            node.get("type"),
            node.get("col"),
            node.get("row"),
        )
        logger.debug("MapPolicy: selected action=%s", action)
        return action
