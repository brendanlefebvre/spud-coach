# Extraction setup

Project goal: datamine Brotato (Godot 3.7.0 game) to extract its rules/algorithms. The release `game_files/Brotato.pck` is an unencrypted Godot 3.x PCK (pack format v1, 7416 files). `game_files/` itself is not checked into this repo (copyrighted game binaries) — copy it from your own Steam install.

Two extraction outputs exist in the repo root (both gitignored — regenerate them rather than committing):
- `extracted/` — produced by `unpack_pck.py` (stdlib Python PCK unpacker). Raw files; the ~2,985 `.tres` are plaintext text-resources = the DATA layer (item/weapon/enemy/character/wave stats).
- `recovered/` — produced by gdre_tools (`gdsdecomp`) via `--headless --recover=...`. Decompiled the 445 `.gdc` files, yielding 476 readable `.gd` files = the CODE/algorithm layer. Decompiled translations live at `recovered/.assets/resources/translations/translations.csv`.

Key data locations: `items/all/<item>/` (items), `items/characters/<char>/` (characters), `weapons/{melee,ranged}/<w>/<tier>/` (weapons, tiers 1-4), `items/sets/<class>/` (weapon class set bonuses), `entities/structures/` (turrets/landmines). For weapons, the `*_data.tres` `effects` array matters as much as `*_stats.tres` — e.g. Wrench's effect spawns a turret, Screwdriver's spawns landmines.

Note: as Brotato releases updates, re-copy `game_files/Brotato.pck` from a current install and re-run the extraction to regenerate `extracted/`/`recovered/` rather than relying on stale checked-in output.
