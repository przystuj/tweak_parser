#!/usr/bin/python
# -*- coding: utf-8 -*-
import json, os
import re
from slpp import slpp as lua
from deepdiff import DeepDiff


def load_map_from_json(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)


def replace_json_keys_and_values(data, map):
    if isinstance(data, dict):
        return {
            map.get(k, k): replace_json_keys_and_values(v, map)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [
            replace_json_keys_and_values(item, map)
            for item in data
        ]
    else:
        return map.get(data, data)


def load_file_as_string(file_path):
    with open(file_path, 'r') as file:
        return file.read()


def save_string_to_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)


def cleanup_key(rootkey):
    return rootkey.replace("']['", ".")


def is_float(element: any) -> bool:
    if element is None:
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False


def process_value_diffs(input_string, weapon_names):
    pattern = r"Value of root\['(.*)'] changed from (.*) to (.*)\."

    def replace_match(match):
        root_key = cleanup_key(match.group(1))
        from_value_string = match.group(2).replace("\"", "")
        to_value_string = match.group(3).replace("\"", "")
        root_key_string = f"**{root_key}**"

        if root_key.startswith("weapondefs."):
            split = root_key.split(".")
            weapon_name = weapon_names.get(split[1])
            if len(split) > 2:
                params = '.'.join(split[2:])
                root_key_string = f"{weapon_name} ({split[1]}): **{params}**"
        if is_float(from_value_string) and is_float(to_value_string):
            to_value = float(to_value_string)
            from_value = float(from_value_string)
            difference = round(to_value - from_value, 2)
            sign = '' if difference < 0 else '+'
            diff_string = sign + str(difference)
            if from_value != 0:
                percent = str(round(difference / from_value * 100, 2))
                diff_string += " / " + sign + percent + "%"

            return f"{root_key_string} changed from **{round(from_value, 2)}** to **{round(to_value, 2)}**. ({diff_string})"
        else:
            if "yardmap" in root_key:
                return f"**{root_key}** changed."
            return f"{root_key_string} changed from **{from_value_string}** to **{to_value_string}**."

    return re.sub(pattern, replace_match, input_string)


def process_dict_additions(input_string, weapon_names):
    pattern = r"Item root\['(.*)'](?:\[\d*\])? \((.*)\) added to dictionary."

    def replace_match(match):
        root_key = cleanup_key(match.group(1))
        value = match.group(2)

        if root_key.startswith("weapondefs."):
            split = root_key.split(".")
            weapon_name = weapon_names.get(split[1])
            if len(split) > 2:
                params = '.'.join(split[2:])
                return f"{weapon_name}: Added **{params}** with value **{value}**"
            else:
                return f"Added weapon **'{weapon_name}'** ({split[1]}) with value **{value}**"
        return f"Added **{root_key}** with value **{value}**"

    return re.sub(pattern, replace_match, input_string)


def post_process(result, weapon_names):
    for key, value in namesMap.items():
        result = result.replace("\"" + key + "\"", "\"" + value + "\"")
    result = re.sub(r"Item root\['buildoptions']\[.*] \(\"(.*)\"\) added to dictionary\.", r"**\1** added to build options", result)
    result = process_dict_additions(result, weapon_names)
    result = process_value_diffs(result, weapon_names)
    return result


changes = load_file_as_string('changes.txt')
namesMap = load_map_from_json('units.json')["units"]["names"]
unitDefs = load_map_from_json('unitDefs.json')
weapon_names = load_map_from_json('weaponNames.json')

changesAsJson = lua.decode(changes)
result = ""

for unit, change in changesAsJson.items():
    unitDef = dict(unitDefs.get(unit))
    dict.update(unitDef, change)

    diff = DeepDiff(unitDefs.get(unit), unitDef, verbose_level=2, ignore_numeric_type_changes=True)
    diff.pop("dictionary_item_removed", None)
    diff.tree.pop("dictionary_item_removed", None)

    result += "### " + namesMap.get(unit) + ":\n"
    result += diff.pretty().replace("\n", "  \n")
    result += "\n\n\n"

outputString = post_process(result, weapon_names)
save_string_to_file('output.md', outputString)
