# Battle Agent DQN
## State information:

```
1. Current Round Number
2. Valid action mask
3. Player INFO:
{

Max HP, Current HP, Current Block, Current Potions, Current Relics, Current Energy, Current Orb slot, Current buffs, Current hand deck, Current draw deck, Current Exhaust pile, Current Discard pile, Current Gold

For cards in hand:[1. Card ID 2. Card index 3. Cost of Energy 4.Cost of stars 5. Type 6. Is Upgarded 7. Is Playable 8. Target type]

For draw deck/discard deck/exhausted deck, we use a deck vector detailed below
}

4. Enimies INFO:
For each *Enemy* [max 5]:
{
    Enemy ID, Max HP, Current HP, Intent, Buffs, Damage, Block
}
```
For deck encode: we use a double array for representing. Deck[card_id:int]=[i_1,i_2], i_1 is the number of unupgraded card, i_2 is the number of upgraded card. So the size will be len(cards)\*2=576\*2=1152

##

## Total actions: 
1. Proceed
2. Play a specific card
3. Use a potion
```
Actions map
{
0 = end_turn
1-10 = play card at hand index 0-9
11-15 = use potion slot 0-4
}
```