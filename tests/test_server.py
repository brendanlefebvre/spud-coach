import asyncio

from brotato_coach.server import build_server

DS = {
    "schema_version": 1, "game_version": "dev", "generated_at": "t",
    "weapons": [{"id": "weapon_minigun", "name": "Minigun", "tier": 4,
                 "dps_at_zero_rd": 55.5556, "dps_slope_per_rd": 8.3333, "scaling_stats": []}],
    "items": [], "characters": [], "sets": [], "stat_mechanics": {},
}


async def _call(server, tool_name, **kwargs):
    # FastMCP's call_tool returns a (content, structured) tuple when the tool's
    # return-type annotation carries an output schema (e.g. dict[str, Any]);
    # otherwise it returns just the unstructured content list.
    result = await server.call_tool(tool_name, kwargs)
    structured = result[1] if isinstance(result, tuple) else result
    return structured


def test_server_registers_tools():
    server = build_server(DS)

    async def _list_names():
        tools = await server.list_tools()
        return {t.name for t in tools}

    tool_names = asyncio.run(_list_names())
    assert {"get_weapon", "weapon_dps", "evaluate_item_for_build",
            "check_dataset_version"} <= tool_names


def test_check_dataset_version_tool():
    server = build_server(DS)
    result = asyncio.run(_call(server, "check_dataset_version"))
    assert result["game_version"] == "dev"


def test_weapon_dps_tool():
    server = build_server(DS)
    result = asyncio.run(_call(server, "weapon_dps", name="Minigun", tier=4,
                               stats={"ranged_damage": 10}))
    assert round(result["dps"]) == round(55.5556 + 8.3333 * 10)
