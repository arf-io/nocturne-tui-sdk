# Nullification

The items below are hidden by the contract in `native/contract/NULLIFICATION.json`. A hidden catalogue effect is omitted from the [component catalogue](Catalogue.md) pages, and the Gallery omits every recipe and study that uses it, attract mode included. A hidden recipe is omitted from the Gallery.

The core still accepts and renders a hidden effect, and [components.json](components.json) still describes it. The parameter tables of the catalogue pages state the engine's domains, which include it, and the Gallery's effect picker, which lists the native catalogue, still offers it.

## Catalogue identities

| Identity | Name | Recipes omitted | Reason |
|---|---|---|---|
| `weather/silver-squall` | Silver Squall | `rain`, `weather-authoring`, `surface-lab` | Added on 2026-09-25 for 1.0.0-rc.4 with no source in the original explorations |
| `weather/snowglobe` | Snowglobe | `snow` | Added on 2026-09-25 for 1.0.0-rc.4 with no source in the original explorations |

Recipes omitted are those of `native/recipes.json`. The Gallery studies generated from the catalogue that use the identity are omitted by the same rule when the Gallery is built.
