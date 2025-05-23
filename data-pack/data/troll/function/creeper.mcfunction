gamerule sendCommandFeedback false
gamerule commandBlockOutput false
execute as @r[name=!"TetraTheta",nbt={Dimension:"minecraft:overworld"}] run summon minecraft:creeper ^ ^ ^-5
gamerule sendCommandFeedback true
gamerule commandBlockOutput true
