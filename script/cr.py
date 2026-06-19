from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
RESOURCE_PACK_DIR = REPO_ROOT / "resource-pack" / "compact-resources-pack"
OVERLAY_DIR = SCRIPT_DIR / "cr_overlay"
DEFAULT_CONFIG = SCRIPT_DIR / "config.json"

NAMESPACE = "compactresources"
COMPRESSED_ITEM_DIR = "item/compressed"
TEXTURE_OUTPUT_DIR = RESOURCE_PACK_DIR / "assets" / NAMESPACE / "textures" / "item" / "compressed"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SUPPORTED_TEXTURE_SIZES = {(16, 16), (32, 32)}
COMPRESSION_LEVELS = (("x9", 0.2), ("x81", 0.4), ("x729", 0.6))

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


class CliArgs(argparse.Namespace):
    command: str
    input: Path
    output: Path
    config: Path | None


class TextureSet:
    def __init__(self, top: Path, side: Path, bottom: Path) -> None:
        self.top = top
        self.side = side
        self.bottom = bottom

    def texture_files(self) -> set[Path]:
        return {self.top, self.side, self.bottom}


def parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(description="CompactResources 리소스팩 관리 스크립트입니다.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser(
        "convert",
        description="PNG 텍스처에 압축 단계별 검은 오버레이와 외곽선 템플릿을 적용합니다.",
        help="PNG 텍스처를 압축 단계별 이미지로 변환합니다.",
    )
    add_input_argument(convert_parser)
    convert_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=TEXTURE_OUTPUT_DIR,
        help="변환된 PNG 출력 디렉토리입니다. 기본값은 리소스팩의 압축 아이템 텍스처 디렉토리입니다.",
    )

    new_parser = subparsers.add_parser(
        "new",
        description="압축 아이템용 PNG, model JSON, item JSON을 함께 생성합니다.",
        help="PNG 변환과 JSON 생성을 한 번에 실행합니다.",
    )
    add_input_argument(new_parser)
    new_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=RESOURCE_PACK_DIR,
        help="리소스팩 루트 출력 디렉토리입니다. 기본값은 compact-resources-pack입니다.",
    )
    new_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="면별 텍스처 설정 JSON 경로입니다. 기본값은 script/config.json입니다.",
    )

    return parser.parse_args(namespace=CliArgs())


def add_input_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="입력 PNG 파일들이 있는 디렉토리입니다.",
    )


def read_png_size(file_path: Path) -> tuple[int, int]:
    with file_path.open("rb") as file:
        signature = file.read(8)
        header = file.read(24)

    has_valid_signature = signature == PNG_SIGNATURE
    has_ihdr_header = header[:4] == b"\x00\x00\x00\r" and header[4:8] == b"IHDR"
    if not has_valid_signature or not has_ihdr_header:
        raise ValueError(f"PNG 파일 구조가 아닙니다: {file_path}")

    return struct.unpack(">II", header[8:16])


def require_input_dir(input_dir: Path) -> None:
    if not input_dir.is_dir():
        raise NotADirectoryError(f"입력 디렉토리가 아닙니다: {input_dir}")


def discover_png_files(input_dir: Path) -> list[Path]:
    png_files = sorted(input_dir.glob("*.png"))
    if not png_files:
        print("처리할 PNG 파일이 없습니다.")

    return png_files


def get_overlay_file(texture_file: Path) -> Path:
    width, height = read_png_size(texture_file)
    if (width, height) not in SUPPORTED_TEXTURE_SIZES:
        supported_sizes = ", ".join(f"{size[0]}x{size[1]}" for size in sorted(SUPPORTED_TEXTURE_SIZES))
        raise ValueError(f"지원하지 않는 PNG 크기입니다: {texture_file} ({width}x{height}, 지원: {supported_sizes})")

    overlay_file = OVERLAY_DIR / f"{width}.png"
    if not overlay_file.is_file():
        raise FileNotFoundError(f"외곽선 템플릿 파일을 찾을 수 없습니다: {overlay_file}")

    overlay_size = read_png_size(overlay_file)
    if overlay_size != (width, height):
        raise ValueError(
            f"외곽선 템플릿 크기가 입력 PNG와 다릅니다: {overlay_file} ({overlay_size[0]}x{overlay_size[1]})"
        )

    return overlay_file


def convert_textures(texture_files: set[Path] | list[Path], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for texture_file in sorted(texture_files):
        overlay_file = get_overlay_file(texture_file)
        print(f"변환 중: {texture_file.name}")

        for suffix, opacity in COMPRESSION_LEVELS:
            output_file = output_dir / f"{texture_file.stem}_{suffix}.png"
            run_ffmpeg(texture_file, overlay_file, output_file, opacity)


def run_ffmpeg(
    input_file: Path,
    overlay_file: Path,
    output_file: Path,
    opacity: float,
) -> None:
    filter_complex = (
        f"[0:v]format=rgba,drawbox=x=0:y=0:w=iw:h=ih:color=black@{opacity}:t=fill[base];"
        "[1:v]format=rgba[border];"
        "[base][border]overlay=0:0:format=auto"
    )
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-i",
        str(overlay_file),
        "-filter_complex",
        filter_complex,
        "-frames:v",
        "1",
        str(output_file),
    ]
    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def load_config(input_dir: Path, config_file: Path | None) -> dict[str, TextureSet]:
    resolved_config_file = config_file if config_file is not None else DEFAULT_CONFIG
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


def parse_texture_set(
    input_dir: Path,
    block_name: str,
    raw_texture_set: dict[object, object],
) -> TextureSet:
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


def discover_cube_all_blocks(
    input_dir: Path,
    config: dict[str, TextureSet],
) -> dict[str, TextureSet]:
    configured_texture_files = {
        texture_file.resolve() for texture_set in config.values() for texture_file in texture_set.texture_files()
    }
    blocks: dict[str, TextureSet] = {}

    for texture_file in discover_png_files(input_dir):
        if texture_file.resolve() in configured_texture_files:
            continue

        blocks[texture_file.stem] = TextureSet(
            top=texture_file,
            side=texture_file,
            bottom=texture_file,
        )

    return blocks


def write_model_files(blocks: dict[str, TextureSet], output_dir: Path) -> None:
    model_dir = output_dir / "assets" / NAMESPACE / "models" / "item" / "compressed"
    item_definition_dir = output_dir / "assets" / NAMESPACE / "items" / "item" / "compressed"
    model_dir.mkdir(parents=True, exist_ok=True)
    item_definition_dir.mkdir(parents=True, exist_ok=True)

    for block_name, texture_set in sorted(blocks.items()):
        for suffix, _opacity in COMPRESSION_LEVELS:
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


def write_json(file_path: Path, data: JsonValue) -> None:
    with file_path.open("w", encoding="utf-8", newline="\r\n") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def run_convert(input_dir: Path, output_dir: Path) -> None:
    require_input_dir(input_dir)
    png_files = discover_png_files(input_dir)
    if not png_files:
        return

    convert_textures(png_files, output_dir)
    print("텍스처 변환이 완료되었습니다.")


def run_new(input_dir: Path, config_file: Path | None, output_dir: Path) -> None:
    require_input_dir(input_dir)
    config_blocks = load_config(input_dir, config_file)
    cube_all_blocks = discover_cube_all_blocks(input_dir, config_blocks)
    blocks = {**cube_all_blocks, **config_blocks}

    if not blocks:
        print("추가할 PNG 텍스처가 없습니다.")
        return

    texture_output_dir = output_dir / "assets" / NAMESPACE / "textures" / "item" / "compressed"
    texture_files = {texture_file for texture_set in blocks.values() for texture_file in texture_set.texture_files()}

    convert_textures(texture_files, texture_output_dir)
    write_model_files(blocks, output_dir)
    print("압축 아이템 리소스 생성이 완료되었습니다.")


def main() -> int:
    args = parse_args()

    try:
        if args.command == "convert":
            run_convert(args.input, args.output)
        elif args.command == "new":
            run_new(args.input, args.config, args.output)
        else:
            raise ValueError(f"알 수 없는 명령입니다: {args.command}")
    except (
        FileNotFoundError,
        NotADirectoryError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"오류: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
