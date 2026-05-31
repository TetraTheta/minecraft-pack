# Summon charged Creeper to random player
gamerule send_command_feedback false
gamerule command_block_output false
execute in minecraft:overworld as @r[name=!"TetraTheta"] at @s run summon creeper ^ ^ ^-5 {powered:1b}
gamerule send_command_feedback true
gamerule command_block_output true
