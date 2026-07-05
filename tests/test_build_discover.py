from brotato_coach.builders.discover import (
    find_weapon_dirs, find_item_dirs, find_character_dirs, find_set_dirs)


def test_find_weapon_dirs(tmp_path):
    d = tmp_path / "weapons" / "ranged" / "shredder" / "4"
    d.mkdir(parents=True)
    (d / "shredder_4_stats.tres").write_text("stats")
    (d / "shredder_4_data.tres").write_text("data")

    found = find_weapon_dirs(str(tmp_path))
    assert len(found) == 1
    entry = found[0]
    assert entry["weapon_id"] == "weapon_shredder"
    assert entry["tier"] == 4
    assert entry["stats_path"].endswith("shredder_4_stats.tres")
    assert entry["data_path"].endswith("shredder_4_data.tres")


def test_find_item_dirs(tmp_path):
    d = tmp_path / "items" / "all" / "handcuffs"
    d.mkdir(parents=True)
    (d / "handcuffs_data.tres").write_text("data")
    (d / "handcuffs_effect_1.tres").write_text("e1")
    (d / "handcuffs_effect_2.tres").write_text("e2")
    # a dir with no item_data.gd resource at all is skipped
    empty = tmp_path / "items" / "all" / "not_an_item"
    empty.mkdir(parents=True)
    (empty / "not_an_item.png.import").write_text("x")
    # a dir whose only .tres references a different script is also skipped —
    # exercises the fallback loop rejecting a non-item_data.gd resource. Named
    # "unrelated.tres" (not "unrelated_data.tres") so it misses the standard-
    # name fast path and actually reaches the script check.
    unrelated = tmp_path / "items" / "all" / "unrelated"
    unrelated.mkdir(parents=True)
    (unrelated / "unrelated.tres").write_text(
        '[gd_resource type="Resource" load_steps=2 format=2]\n\n'
        '[ext_resource path="res://items/global/some_other.gd" type="Script" id=1]\n\n'
        '[resource]\n'
        'script = ExtResource( 1 )\n'
    )
    found = find_item_dirs(str(tmp_path))
    assert len(found) == 1
    e = found[0]
    assert e["item_id"] == "item_handcuffs"
    assert e["name"] == "Handcuffs"
    assert len(e["effect_paths"]) == 2


def test_find_item_dirs_pet_style_bare_data_file(tmp_path):
    # Pets (and a few other items, e.g. evil_hat) ship their main data file
    # as a bare "{folder}.tres" instead of the usual "{folder}_data.tres".
    d = tmp_path / "items" / "all" / "lootworm"
    d.mkdir(parents=True)
    (d / "lootworm.tres").write_text(
        '[gd_resource type="Resource" load_steps=2 format=2]\n\n'
        '[ext_resource path="res://items/global/item_data.gd" type="Script" id=1]\n\n'
        '[resource]\n'
        'script = ExtResource( 1 )\n'
        'my_id = "item_lootworm"\n'
        'tags = [ "economy", "pickup", "pet" ]\n'
    )
    (d / "lootworm_effect_0.tres").write_text("e0")

    found = find_item_dirs(str(tmp_path))
    assert len(found) == 1
    e = found[0]
    assert e["item_id"] == "item_lootworm"
    assert e["name"] == "Lootworm"
    assert e["data_path"].endswith("lootworm.tres")
    assert len(e["effect_paths"]) == 1


def test_find_item_dirs_folder_name_mismatched_with_file_prefix(tmp_path):
    # eyes_surgery: the folder is plural but its files use the singular
    # "eye_surgery" prefix, so effect discovery can't assume folder == prefix.
    d = tmp_path / "items" / "all" / "eyes_surgery"
    d.mkdir(parents=True)
    (d / "eye_surgery_data.tres").write_text(
        '[gd_resource type="Resource" load_steps=2 format=2]\n\n'
        '[ext_resource path="res://items/global/item_data.gd" type="Script" id=1]\n\n'
        '[resource]\n'
        'script = ExtResource( 1 )\n'
        'my_id = "item_eyes_surgery"\n'
    )
    (d / "eye_surgery_effect_1.tres").write_text("e1")
    (d / "eye_surgery_effect_2.tres").write_text("e2")

    found = find_item_dirs(str(tmp_path))
    assert len(found) == 1
    e = found[0]
    assert e["item_id"] == "item_eyes_surgery"
    assert e["data_path"].endswith("eye_surgery_data.tres")
    assert len(e["effect_paths"]) == 2


def test_find_character_dirs(tmp_path):
    d = tmp_path / "items" / "characters" / "ranger"
    d.mkdir(parents=True)
    (d / "ranger_data.tres").write_text("data")
    (d / "ranger_effect_2.tres").write_text("e2")  # note: starts at _2
    found = find_character_dirs(str(tmp_path))
    assert len(found) == 1
    assert found[0]["char_id"] == "character_ranger"
    assert len(found[0]["effect_paths"]) == 1


def test_find_set_dirs(tmp_path):
    base = tmp_path / "items" / "sets" / "gun"
    (base / "2").mkdir(parents=True)
    (base / "6").mkdir(parents=True)
    (base / "gun_set_data.tres").write_text("setdata")
    (base / "2" / "set_2_effect_1.tres").write_text("e2")
    (base / "6" / "set_6_effect_1.tres").write_text("e6")
    found = find_set_dirs(str(tmp_path))
    assert len(found) == 1
    e = found[0]
    assert e["set_id"] == "set_gun"
    assert sorted(e["count_effect_paths"].keys()) == [2, 6]


def test_resolve_effect_burning_data_finds_companion_resource(tmp_path):
    from brotato_coach.builders import discover
    wdir = tmp_path / "weapons" / "melee" / "torch" / "1"
    wdir.mkdir(parents=True)
    effect_path = wdir / "torch_effect_1.tres"
    effect_path.write_text(
        '[gd_resource type="Resource" format=2]\n'
        '[ext_resource path="res://effects/weapons/burning_effect.gd" type="Script" id=1]\n'
        '[ext_resource path="res://weapons/melee/torch/1/torch_burning_data.tres" type="Resource" id=2]\n'
        '[resource]\nscript = ExtResource( 1 )\nkey = "effect_burning"\n'
        'burning_data = ExtResource( 2 )\n', encoding="utf-8")
    (wdir / "torch_burning_data.tres").write_text(
        '[gd_resource type="Resource" format=2]\n[resource]\n'
        'chance = 1.0\ndamage = 3\nduration = 3\n', encoding="utf-8")

    result = discover._resolve_effect_burning_data(str(tmp_path), [str(effect_path)])
    assert list(result.keys()) == [str(effect_path)]
    assert result[str(effect_path)].endswith("torch_burning_data.tres")


def test_resolve_effect_burning_data_skips_effects_without_one(tmp_path):
    from brotato_coach.builders import discover
    wdir = tmp_path / "weapons" / "ranged" / "shredder" / "1"
    wdir.mkdir(parents=True)
    effect_path = wdir / "shredder_effect.tres"
    effect_path.write_text(
        '[gd_resource type="Resource" format=2]\n[resource]\n'
        'key = "effect_explode_custom"\nchance = 0.5\n', encoding="utf-8")

    result = discover._resolve_effect_burning_data(str(tmp_path), [str(effect_path)])
    assert result == {}


def test_find_weapon_dirs_includes_burning_data_paths(tmp_path):
    wdir = tmp_path / "weapons" / "melee" / "torch" / "1"
    wdir.mkdir(parents=True)
    (wdir / "torch_stats.tres").write_text("stats")
    effect_path = wdir / "torch_effect_1.tres"
    effect_path.write_text(
        '[gd_resource type="Resource" format=2]\n'
        '[ext_resource path="res://effects/weapons/burning_effect.gd" type="Script" id=1]\n'
        '[ext_resource path="res://weapons/melee/torch/1/torch_burning_data.tres" type="Resource" id=2]\n'
        '[resource]\nscript = ExtResource( 1 )\nkey = "effect_burning"\n'
        'burning_data = ExtResource( 2 )\n', encoding="utf-8")
    (wdir / "torch_burning_data.tres").write_text(
        '[gd_resource type="Resource" format=2]\n[resource]\n'
        'chance = 1.0\ndamage = 3\nduration = 3\n', encoding="utf-8")
    (wdir / "torch_data.tres").write_text(
        '[gd_resource type="Resource" format=2]\n'
        '[ext_resource path="res://weapons/melee/torch/1/torch_effect_1.tres" type="Resource" id=1]\n'
        '[resource]\neffects = [ ExtResource( 1 ) ]\n', encoding="utf-8")

    found = find_weapon_dirs(str(tmp_path))
    assert len(found) == 1
    paths = found[0]["effect_burning_data_paths"]
    assert len(paths) == 1
    assert list(paths.values())[0].endswith("torch_burning_data.tres")


def test_find_weapon_dirs_main_data_glob_skips_burning_data_companion(tmp_path):
    # Regression: a burn weapon's tier dir holds both "{w}_data.tres" and its
    # "{w}_burning_data.tres" companion. The latter also matches "*_data.tres"
    # and sorts first alphabetically, so a naive glob[0] picked the wrong file
    # (its effects/display_name were silently empty). The main-data glob must
    # exclude "*_burning_data.tres".
    wdir = tmp_path / "weapons" / "melee" / "torch" / "1"
    wdir.mkdir(parents=True)
    (wdir / "torch_stats.tres").write_text("stats")
    (wdir / "torch_burning_data.tres").write_text(
        '[gd_resource type="Resource" format=2]\n[resource]\n'
        'chance = 1.0\ndamage = 3\nduration = 3\n', encoding="utf-8")
    (wdir / "torch_data.tres").write_text(
        '[gd_resource type="Resource" format=2]\n[resource]\n'
        'effects = [ ]\n', encoding="utf-8")

    found = find_weapon_dirs(str(tmp_path))
    assert len(found) == 1
    assert found[0]["data_path"].endswith("torch_data.tres")
    assert not found[0]["data_path"].endswith("torch_burning_data.tres")
