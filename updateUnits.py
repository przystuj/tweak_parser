#!/usr/bin/python
# -*- coding: utf-8 -*-
import json, os
from slpp import slpp as lua

units_folder_path = "S:\\VSprojects\\Beyond-All-Reason\\units"


def load_lua_files(folder):
    lua_files = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".lua"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as lua_file:
                    lua_files.append(lua_file.read())

    return lua_files


def save_string_to_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)


def ensure_dict(value):
    if isinstance(value, dict):
        return value
    return {i + 1: v for i, v in enumerate(value)}


unitDefinitions = {}
weaponNames = {}


for unitLua in load_lua_files(units_folder_path):
    if "local unitsTable = {}" in unitLua: #some special definitions for evo com
        continue
    if "local lootboxesDefs = {}" in unitLua: #dunno what is that
        continue
    unitLua = unitLua.split("return ")[1]
    unit_json = lua.decode(unitLua)
    for unitId in unit_json:
        unit = unit_json.get(unitId)
        if "buildoptions" in unit:
            unit["buildoptions"] = ensure_dict(unit["buildoptions"])
        unitDefinitions[unitId] = unit
        if "weapondefs" in unit:
            for weapondefId, weapondef in unit["weapondefs"].items():
                weaponNames[weapondefId] = weapondef.get("name")


save_string_to_file('unitDefs.json', json.dumps(unitDefinitions, indent=4))
save_string_to_file('weaponNames.json', json.dumps(weaponNames, indent=4))
