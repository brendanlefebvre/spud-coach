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
    # a dir with no _data.tres is skipped
    pet = tmp_path / "items" / "all" / "lootworm"
    pet.mkdir(parents=True)
    (pet / "lootworm.png.import").write_text("x")
    found = find_item_dirs(str(tmp_path))
    assert len(found) == 1
    e = found[0]
    assert e["item_id"] == "item_handcuffs"
    assert e["name"] == "Handcuffs"
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
