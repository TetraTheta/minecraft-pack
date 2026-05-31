# Put this file in Prism Launcher's 'instances' directory and run
# Requirements:
#   - 1.21/minecraft/saves/TEST/datapacks
#   - <version>/minecraft/saves/TEST
import ctypes
import shutil
import sys
from pathlib import Path


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0  # pyright: ignore[reportAny]
    except AttributeError:
        return False


def elevate_privileges():
    already_tried_elevation = "--elevated" in sys.argv

    if not is_admin():
        if already_tried_elevation:
            print("[ERROR] Administrator privileges were denied or failed to apply.")
            print("This script requires admin rights to create symbolic links.")
            _ = input("\nPress Enter to exit...")
            sys.exit(1)
        print("Requesting administrative privileges...")
        script_path = sys.argv[0]
        other_args = [arg for arg in sys.argv[1:] if arg != "--elevated"]
        params = f'"{script_path}" --elevated ' + " ".join(other_args)
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)  # pyright: ignore[reportAny]
        if int(result) <= 32:  # pyright: ignore[reportAny]
            print(f"[ERROR] Failed to launch elevated process. Error code: {result}")
            _ = input("\nPress Enter to exit...")
            sys.exit(1)

        sys.exit(0)


def main():
    base_dir = Path.cwd()

    source_intance = "1.21"
    sub_path = Path("minecraft/saves/TEST")
    datapacks_name = "datapacks"

    source_datapacks = base_dir / source_intance / sub_path / datapacks_name

    if not source_datapacks.exists():
        print(f"Error: Base datapacks directory not found at:\n  {source_datapacks}")
        print("Please ensure you are running this script in the correct directory.")
        return

    print(f"Source datapacks found: {source_datapacks}\n")

    target_directories = [
        "1.21.1",
        "1.21.2",
        "1.21.3",
        "1.21.4",
        "1.21.5",
        "1.21.6",
        "1.21.7",
        "1.21.8",
        "1.21.9",
        "1.21.10",
        "1.21.11",
        "26.1",
        "26.1.1",
        "26.1.2",
    ]

    for target_name in target_directories:
        instance_dir = base_dir / target_name

        if not instance_dir.is_dir():
            print(f"Skipping: '{target_name}' (Directory does not exist in current path)")
            continue

        test_dir = instance_dir / sub_path
        datapacks_dir = test_dir / datapacks_name

        if test_dir.is_dir():
            print(f"Processing: {instance_dir.name}")
            if datapacks_dir.exists() or datapacks_dir.is_symlink():
                print(f"  -> Removing existing '{datapacks_name}'...")
                try:
                    if datapacks_dir.is_dir() and not datapacks_dir.is_symlink():
                        shutil.rmtree(datapacks_dir)
                    else:
                        datapacks_dir.unlink()
                except Exception as e:
                    print(f"  [ERROR] Failed to remove {datapacks_dir}: {e}")
                    continue

            try:
                datapacks_dir.symlink_to(source_datapacks, target_is_directory=True)
                print("  -> Successfully linked to 1.21 datapacks.")
            except Exception as e:
                print(f"  [ERROR] Failed to create symlink: {e}")


if __name__ == "__main__":
    elevate_privileges()
    main()
    _ = input("\nProcess finished. Press Enter to exit...")
