from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ITEM_MODEL_PATH = (
    REPO_ROOT / "resource-pack" / "compact-resources-pack" / "assets" / "minecraft" / "items" / "heart_of_the_sea.json"
)
COMPRESSION_SUFFIX_ORDER = {
    "x9": 0,
    "x81": 1,
    "x729": 2,
}

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]
SortToken = tuple[int, int | str]
CaseSortKey = tuple[list[SortToken], int, list[SortToken]]


def split_natural_tokens(value: str) -> list[SortToken]:
    return [(0, int(token)) if token.isdigit() else (1, token) for token in re.split(r"(\d+)", value)]


def build_case_sort_key(case: JsonValue) -> CaseSortKey:
    if not isinstance(case, dict):
        return (
            split_natural_tokens(""),
            len(COMPRESSION_SUFFIX_ORDER),
            split_natural_tokens(""),
        )

    when_value = case.get("when")
    if not isinstance(when_value, str):
        return (
            split_natural_tokens(""),
            len(COMPRESSION_SUFFIX_ORDER),
            split_natural_tokens(""),
        )

    item_name, separator, suffix = when_value.rpartition("/")
    if separator == "":
        return (
            split_natural_tokens(when_value),
            len(COMPRESSION_SUFFIX_ORDER),
            split_natural_tokens(""),
        )

    suffix_order = COMPRESSION_SUFFIX_ORDER.get(suffix, len(COMPRESSION_SUFFIX_ORDER))
    return (split_natural_tokens(item_name), suffix_order, split_natural_tokens(suffix))


def require_json_object(value: object, file_path: Path) -> JsonObject:
    if not isinstance(value, dict):
        raise ValueError(f"JSON 객체 구조가 아닙니다: {file_path}")

    return value


def require_json_list(value: object, file_path: Path) -> list[JsonValue]:
    if not isinstance(value, list):
        raise ValueError(f"JSON 배열 구조가 아닙니다: {file_path}")

    return value


def load_item_model(file_path: Path) -> JsonObject:
    with file_path.open(encoding="utf-8") as file:
        raw_item_model: object = json.load(file)

    return require_json_object(raw_item_model, file_path)


def write_json(file_path: Path, data: JsonValue) -> None:
    with file_path.open("w", encoding="utf-8", newline="\r\n") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def sort_heart_of_the_sea_cases(file_path: Path = ITEM_MODEL_PATH) -> None:
    item_model = load_item_model(file_path)
    model = require_json_object(item_model.get("model"), file_path)
    cases = require_json_list(model.get("cases"), file_path)

    cases.sort(key=build_case_sort_key)
    write_json(file_path, item_model)


if __name__ == "__main__":
    sort_heart_of_the_sea_cases()
    print("heart_of_the_sea.json 정렬 완료!")
