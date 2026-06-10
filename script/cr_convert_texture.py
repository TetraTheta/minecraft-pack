import argparse
import subprocess
from pathlib import Path


class CliArgs(argparse.Namespace):
    input_dir: Path
    output_dir: Path | None


def parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(description="PNG 파일에 FFmpeg로 검은색 오버레이를 적용합니다.")
    parser.add_argument("-i", "--input-dir", type=Path, required=True, help="입력 PNG 파일들이 있는 디렉토리")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="출력 디렉토리. 기본값은 입력 디렉토리의 out 하위 디렉토리입니다.",
    )

    return parser.parse_args(namespace=CliArgs())


def process_with_ffmpeg(input_dir: str | Path, output_dir: str | Path | None = None) -> None:
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir is not None else input_path / "out"

    if not input_path.is_dir():
        raise NotADirectoryError(f"입력 디렉토리가 아닙니다: {input_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    tasks = [("_x9", 0.2), ("_x81", 0.4), ("_x729", 0.6)]
    png_files = sorted(input_path.glob("*.png"))

    if not png_files:
        print("처리할 PNG 파일이 없습니다.")
        return

    for img_file in png_files:
        print(f"변환 중: {img_file.name}")

        for suffix, opacity in tasks:
            out_file = output_path / f"{img_file.stem}{suffix}.png"

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(img_file),
                "-vf",
                f"drawbox=x=0:y=0:w=iw:h=ih:color=black@{opacity}:t=fill",
                str(out_file),
            ]

            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print("FFmpeg 배치 작업 완료!")


if __name__ == "__main__":
    args = parse_args()
    process_with_ffmpeg(args.input_dir, args.output_dir)
