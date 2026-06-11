# CompactResources Pack

CompactResources Pack provides item models for Heart of the Sea based custom items created by the [CompactResources](https://modrinth.com/plugin/compactresources) Paper plugin.

This pack is the companion resource pack for CompactResources and is developed primarily for that plugin. The plugin handles recipes, item metadata, stack-size behavior, and optional server-side pack delivery; this pack supplies the client-side models and textures those items need.

The pack does not add blocks, items, recipes, or gameplay logic by itself.<br>
It only supplies item model definitions used by specific `minecraft:heart_of_the_sea` item stacks.

Related projects:

- CompactResources plugin: <https://modrinth.com/plugin/compactresources>

## Item Model Contract

The resource pack provides item model definitions under:

```text
assets/compactresources/items/item/compressed/<material>_<level>.json
```

The CompactResources plugin sets the `minecraft:item_model` component to values in this format:

```text
compactresources:item/compressed/<material>_<level>
```

Example:

```text
compactresources:item/compressed/cobblestone_x9
compactresources:item/compressed/cobblestone_x81
compactresources:item/compressed/cobblestone_x729
```

Only the item model component is required for this resource pack to display the custom model.<br>
The plugin also writes Persistent Data Container values so it can identify the item on the server.

## Plugin Item Structure

CompactResources creates compressed blocks as `minecraft:heart_of_the_sea` items with three important pieces of metadata:

- `minecraft:item_model`: selects the model in this resource pack.
- Bukkit Persistent Data Container: identifies the compressed material and level.
- `minecraft:item_name`: displays a translated block name followed by the level.

In vanilla item component syntax, a plugin-recognizable Cobblestone x9 item is equivalent to this shape:

```snbt
heart_of_the_sea[
  item_model="compactresources:item/compressed/cobblestone_x9",
  custom_data={PublicBukkitValues:{compactresources:compressed_material:"cobblestone",compactresources:compression_level:"x9"}},
  item_name=[{"translate":"block.minecraft.cobblestone"}," x9"]
]
```

For display-only use with a datapack, command, or loot table, the `minecraft:item_model` component is the key part.<br>
For interoperability with the CompactResources plugin, keep the `PublicBukkitValues` payload as well.

## Example `/give` Command

```mcfunction
/give @s heart_of_the_sea[item_model="compactresources:item/compressed/cobblestone_x9",custom_data={PublicBukkitValues:{compactresources:compressed_material:"cobblestone",compactresources:compression_level:"x9"}},item_name=[{"translate":"block.minecraft.cobblestone"}," x9"]] 1
```

If you only want to test the model visually and do not need the plugin to treat the item as a compressed block, this shorter form is enough:

```mcfunction
/give @s heart_of_the_sea[item_model="compactresources:item/compressed/cobblestone_x9"] 1
```

## Supported Materials

The `<material>` segment must be one of these IDs:

```text
amethyst_block
andesite
basalt
blackstone
calcite
clay
coal_block
cobbled_deepslate
cobblestone
copper_block
deepslate
diamond_block
diorite
dirt
end_stone
gold_block
granite
gravel
iron_block
lapis_block
netherite_block
netherrack
quartz_block
raw_copper_block
raw_gold_block
raw_iron_block
sand
soul_sand
soul_soil
stone
tuff
```

The `<level>` segment must be one of:

```text
x9
x81
x729
```

## Model and Texture Files

Each item definition is stored at:

```text
assets/compactresources/items/item/compressed/<material>_<level>.json
```

Each item definition points to a model stored at:

```text
assets/compactresources/models/item/compressed/<material>_<level>.json
```

Each texture is stored at:

```text
assets/compactresources/textures/item/compressed/<material>_<level>.png
```

For example:

```text
assets/compactresources/items/item/compressed/cobblestone_x9.json
assets/compactresources/models/item/compressed/cobblestone_x9.json
assets/compactresources/textures/item/compressed/cobblestone_x9.png
```

You can replace the PNG files while keeping the same paths and file names.<br>
The item definition and model files are already wired to those locations.

## Server Resource Pack Delivery via CompactResources plugin

When used with the CompactResources plugin, use the download link of this pack in `config.yml`:

```yml
resource-pack:
  enabled: true
  force: true
  url: 'https://cdn.modrinth.com/data/.../versions/.../compact-resources-pack.zip'
  sha1: '<zip sha1>'
  uuid: '9d54b89a-1738-4307-abd8-3f7f9d8613f5'
```
