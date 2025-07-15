# Summons Lightning Bolt to random player
gamerule sendCommandFeedback false
gamerule commandBlockOutput false
execute in minecraft:overworld as @r[name=!"TetraTheta"] at @s run summon minecraft:lightning_bolt ~ ~ ~
gamerule sendCommandFeedback true
gamerule commandBlockOutput true
