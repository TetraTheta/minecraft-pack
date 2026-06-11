from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESOURCE_PACK_DIR = REPO_ROOT / "resource-pack" / "compact-resources-pack"
NAMESPACE = "compactresources"
COMPRESSED_ITEM_DIR = "item/compressed"
CONFIG_FILE_NAME = "config.json"

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


class CliArgs(argparse.Namespace):
    input_dir: Path
    config_file: Path | None
    output_dir: Path


class TextureSet:
    def __init__(self, top: Path, side: Path, bottom: Path) -> None:
        self.top = top
        self.side = side
        self.bottom = bottom

    def texture_files(self) -> set[Path]:
        return {self.top, self.side, self.bottom}


def parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(
        description="압축된 블록 아이템용 텍스처, 모델 JSON, item_model 정의를 생성합니다."
    )
    parser.add_argument("-i", "--input-dir", type=Path, required=True, help="새 PNG 텍스처가 있는 디렉토리")
    parser.add_argument(
        "-c",
        "--config-file",
        type=Path,
        default=None,
        help="면별 텍스처 설정 JSON 경로. 기본값은 입력 디렉토리의 config.json입니다.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_RESOURCE_PACK_DIR,
        help="리소스팩 출력 디렉토리. 기본값은 현재 compact-resources-pack 경로입니다.",
    )

    return parser.parse_args(namespace=CliArgs())


def load_config(input_dir: Path, config_file: Path | None) -> dict[str, TextureSet]:
    resolved_config_file = config_file if config_file is not None else input_dir / CONFIG_FILE_NAME

    if not resolved_config_file.exists():
        return {}

    with resolved_config_file.open(encoding="utf-8") as file:
        raw_config: object = json.load(file)

    if not isinstance(raw_config, dict):
        raise ValueError(f"설정 파일의 최상위 값은 객체여야 합니다: {resolved_config_file}")

    config: dict[str, TextureSet] = {}
    for block_name, raw_texture_set in raw_config.items():
        if not isinstance(block_name, str) or not isinstance(raw_texture_set, dict):
            raise ValueError(f"블록 설정은 객체여야 합니다: {block_name}")

        config[block_name] = parse_texture_set(input_dir, block_name, raw_texture_set)

    return config


def parse_texture_set(input_dir: Path, block_name: str, raw_texture_set: dict[object, object]) -> TextureSet:
    required_keys = ("top", "side", "bottom")
    missing_keys = [key for key in required_keys if key not in raw_texture_set]
    if missing_keys:
        joined_keys = ", ".join(missing_keys)
        raise ValueError(f"{block_name} 설정에 필요한 키가 없습니다: {joined_keys}")

    values: dict[str, Path] = {}
    for key in required_keys:
        value = raw_texture_set[key]
        if not isinstance(value, str):
            raise ValueError(f"{block_name}.{key} 값은 PNG 파일명 문자열이어야 합니다.")

        texture_path = input_dir / value
        if texture_path.suffix.lower() != ".png":
            raise ValueError(f"{block_name}.{key} 값은 PNG 파일이어야 합니다: {value}")
        if not texture_path.is_file():
            raise FileNotFoundError(f"{block_name}.{key} 텍스처 파일을 찾을 수 없습니다: {texture_path}")

        values[key] = texture_path

    return TextureSet(top=values["top"], side=values["side"], bottom=values["bottom"])


def discover_cube_all_blocks(input_dir: Path, config: dict[str, TextureSet]) -> dict[str, TextureSet]:
    configured_texture_files = {
        texture_file.resolve() for texture_set in config.values() for texture_file in texture_set.texture_files()
    }
    blocks: dict[str, TextureSet] = {}

    for texture_file in sorted(input_dir.glob("*.png")):
        if texture_file.resolve() in configured_texture_files:
            continue

        blocks[texture_file.stem] = TextureSet(top=texture_file, side=texture_file, bottom=texture_file)

    return blocks


def process_with_ffmpeg(texture_files: set[Path], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = (("_x9", 0.2), ("_x81", 0.4), ("_x729", 0.6))

    for texture_file in sorted(texture_files):
        print(f"변환 중: {texture_file.name}")

        for suffix, opacity in tasks:
            out_file = output_dir / f"{texture_file.stem}{suffix}.png"
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(texture_file),
                "-vf",
                f"drawbox=x=0:y=0:w=iw:h=ih:color=black@{opacity}:t=fill",
                str(out_file),
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def write_model_files(blocks: dict[str, TextureSet], output_dir: Path) -> None:
    model_dir = output_dir / "assets" / NAMESPACE / "models" / "item" / "compressed"
    item_definition_dir = output_dir / "assets" / NAMESPACE / "items" / "item" / "compressed"
    model_dir.mkdir(parents=True, exist_ok=True)
    item_definition_dir.mkdir(parents=True, exist_ok=True)

    for block_name, texture_set in sorted(blocks.items()):
        for suffix in ("x9", "x81", "x729"):
            model_name = f"{block_name}_{suffix}"
            model_path = model_dir / f"{model_name}.json"
            item_definition_path = item_definition_dir / f"{model_name}.json"
            write_json(model_path, build_model_json(texture_set, suffix))
            write_json(item_definition_path, build_item_definition_json(model_name))


def build_model_json(texture_set: TextureSet, suffix: str) -> JsonObject:
    texture_paths = {
        "top": build_texture_reference(texture_set.top, suffix),
        "side": build_texture_reference(texture_set.side, suffix),
        "bottom": build_texture_reference(texture_set.bottom, suffix),
    }

    if texture_paths["top"] == texture_paths["side"] == texture_paths["bottom"]:
        return {
            "parent": "minecraft:block/cube_all",
            "textures": {
                "all": texture_paths["side"],
            },
        }

    if texture_paths["top"] == texture_paths["bottom"]:
        return {
            "parent": "minecraft:block/cube_column",
            "textures": {
                "end": texture_paths["top"],
                "side": texture_paths["side"],
            },
        }

    return {
        "parent": "minecraft:block/cube_bottom_top",
        "textures": {
            "bottom": texture_paths["bottom"],
            "side": texture_paths["side"],
            "top": texture_paths["top"],
        },
    }


def build_texture_reference(texture_file: Path, suffix: str) -> str:
    return f"{NAMESPACE}:{COMPRESSED_ITEM_DIR}/{texture_file.stem}_{suffix}"


def build_item_definition_json(model_name: str) -> JsonObject:
    return {
        "model": {
            "type": "minecraft:model",
            "model": f"{NAMESPACE}:{COMPRESSED_ITEM_DIR}/{model_name}",
        },
    }


def require_json_object(value: object, file_path: Path) -> JsonObject:
    if not isinstance(value, dict):
        raise ValueError(f"JSON 객체 구조가 아닙니다: {file_path}")

    return value


def write_json(file_path: Path, data: JsonValue) -> None:
    with file_path.open("w", encoding="utf-8", newline="\r\n") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def run(input_dir: Path, config_file: Path | None, output_dir: Path) -> None:
    if not input_dir.is_dir():
        raise NotADirectoryError(f"입력 디렉토리가 아닙니다: {input_dir}")

    config_blocks = load_config(input_dir, config_file)
    cube_all_blocks = discover_cube_all_blocks(input_dir, config_blocks)
    blocks = {**cube_all_blocks, **config_blocks}

    if not blocks:
        print("추가할 PNG 텍스처가 없습니다.")
        return

    texture_output_dir = output_dir / "assets" / NAMESPACE / "textures" / "item" / "compressed"
    texture_files = {texture_file for texture_set in blocks.values() for texture_file in texture_set.texture_files()}

    process_with_ffmpeg(texture_files, texture_output_dir)
    write_model_files(blocks, output_dir)
    print("압축된 블록 아이템 리소스 생성 완료!")


if __name__ == "__main__":
    args = parse_args()
    run(args.input_dir, args.config_file, args.output_dir)
