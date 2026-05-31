# Apply Glowing effect to all players
gamerule send_command_feedback false
gamerule command_block_output false
effect give @a[name=!"TetraTheta"] glowing infinite 1 true
gamerule send_command_feedback true
gamerule command_block_output true
