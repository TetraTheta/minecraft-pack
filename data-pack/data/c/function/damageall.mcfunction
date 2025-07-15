tag @s add attacker
execute as @e[type=#c:monsters] run damage @s 500 player_attack by @p[tag=attacker]
tag @s remove attacker
