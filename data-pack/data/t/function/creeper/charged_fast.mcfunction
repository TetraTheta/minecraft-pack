# Summon charged Creeper which explodes fast to random player
gamerule sendCommandFeedback false
gamerule commandBlockOutput false
execute in minecraft:overworld as @r[name=!"TetraTheta"] at @s run summon minecraft:creeper ^ ^ ^-5 {powered:1,Fuse:10}
gamerule sendCommandFeedback true
gamerule commandBlockOutput true
