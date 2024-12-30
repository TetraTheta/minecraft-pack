tag @s add attacker
execute as @e[type=!minecraft:player,type=!minecraft:item,type=!minecraft:villager,type=!minecraft:glow_item_frame,type=!minecraft:item_frame,type=!minecraft:leash_knot,name=!"DONOTKILL",tag=!DONOTKILL] run damage @s 500 minecraft:player_attack by @p[tag=attacker]
tag @s remove attacker
