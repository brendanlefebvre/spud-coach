# spud-coach — Roadmap

Coarse, high-level next steps — a shared backlog, not committed timelines.

1. **Incorporate enemy data** — build a bestiary layer from the extracted
   `entities/units/enemies/` tree so the coach can give threat- and wave-aware
   advice (what's coming at a given wave / danger level), not just build-only
   reasoning.
2. **Factor procs into DPS** — `weapon_dps` currently computes only the
   guaranteed base-damage line and ignores on-hit chance effects. (A *proc* =
   "programmed random occurrence" — e.g. the Shredder's 50% exploding
   projectile.) Model the expected proc contribution (roughly
   chance × effect damage × enemies hit) so proc/AoE weapons rank honestly.
3. **Fill `explain_stat` gaps** — only 9 stats currently have mechanics encoded;
   add `stat_ranged_damage` and the other vanilla stats.
4. **Resolve localization / descriptions** — `text_key` fields are unresolved
   pointers, so records carry no human-readable names/descriptions. Wire the
   localization strings so the coach can speak in real in-game item text.
5. **Set-bonus awareness** — weapons now carry class membership (`sets`); add
   loadout set-progress reasoning (e.g. "3 Gun weapons → +20 range at 4
   equipped") and surface active/next set bonuses.
6. **Ship it** — publish to PyPI (`uvx spudcoach`), stand up the spudcoach.fyi
   install page, and list in the official MCP registry + awesome-mcp-servers.
