# Battle Agent DQN
## State information:

```
1. Current Round Number
2. Valid action mask
3. Player INFO:
{

Max HP, Current HP, Current Block, Current Energy, Current Orb slot, Current buffs, Current hand deck, Current draw deck, Current Exhaust pile, Current Discard pile, Current Gold

For cards in hand:[1. Card ID 2. Card index 3. Cost of Energy 4.Cost of stars 5. Type 6. Is Upgarded 7. Is Playable 8. Target type]

For draw deck/discard deck/exhausted deck, we use a deck vector detailed below

For potions, each potion slot uses a one-hot potion id vector plus slot index and can-use flag.

For relics, we use a relic id presence vector.
}

4. Enimies INFO:
For each *Enemy* [max 5]:
{
    Enemy ID, Max HP, Current HP, Attack Intent, Support Intent, Buffs, Attack Damage, Attack Hit Count, Block
}
```
For enemy id encode: runtime monster ids can appear as `MONSTER_ID_n`, where `n` is the instance number for repeated monsters. The encoder strips the trailing `_<number>` and maps only `MONSTER_ID` through `data/monsters.json`.

For attack intents with labels like `6x2`, the first number is encoded as attack damage and the second number is encoded as attack hit count.

For enemy intent encode: each enemy can have up to 2 visible intents. Attack-like intent is encoded in the attack intent slot. Non-attack intent, such as Buff, Debuff, Defend, Heal, Summon, etc., is encoded in the support intent slot. Intent values use the ids from `data/intents.json`, for example `ATTACK`, `BUFF`, `DEBUFF`, `DEFEND`.

For deck encode: we use a double array for representing. Deck[card_id:int]=[i_1,i_2], i_1 is the number of unupgraded card, i_2 is the number of upgraded card. So the size will be len(cards)\*2=576\*2=1152

For relic encode: Relics[relic_id:int] = 1 if the player has the relic, otherwise 0. So the size is len(relics)=293.

For potion encode: each potion slot has [exists, one_hot_potion_id, slot_index, can_use_in_combat]. The potion id vector size is len(potions)=63.

##

## Total battle actions:
1. End turn
2. Play a specific card against a specific enemy target
3. Play a specific self/no-target card
4. Use a specific potion against a specific enemy target
5. Use a specific self/no-target potion
6. Select/confirm cards during combat hand selection
```
Actions map
{
0 = end_turn
1-50 = play_card_{hand_index}_target_{enemy_index}; hand_index 0-9, enemy_index 0-4
51-60 = play_card_{hand_index}_self; hand_index 0-9
61-110 = use_potion_{slot}_target_{enemy_index}; slot 0-9, enemy_index 0-4
111-120 = use_potion_{slot}_self; slot 0-9
121-130 = combat_select_card_{hand_select_index}; hand_select_index 0-9
131 = combat_confirm_selection
}
```

Targeted actions use enemy slot indices from the encoded battle state. When executing an
action, the agent maps `enemy_index` to the live enemy's runtime `entity_id`.

## Battle reward

Terminal battle reward remains the main signal:

```
+100 for winning a battle
0 for losing a battle
-1 for each HP lost from battle start to battle end
-5 for each potion used
```

Per-step shaping is added to make learning less sparse:

```
+0.2 for each enemy HP removed this step
+10 for each enemy killed this step
-0.1 for each unspent energy when ending the turn
-1 for action errors
```
