import time
from pathlib import Path

import mss
import mss.tools


def main():
    output_dir = Path(__file__).resolve().parent / "captures"
    output_dir.mkdir(exist_ok=True)

    print("Switch to the game within 5 seconds...")
    time.sleep(5)

    with mss.mss() as capture:
        for index, monitor in enumerate(capture.monitors[1:], start=1):
            screenshot = capture.grab(monitor)
            output_path = output_dir / f"monitor_{index}.png"

            mss.tools.to_png(
                screenshot.rgb,
                screenshot.size,
                output=str(output_path),
            )

            print(
                f"Monitor {index}: "
                f"{screenshot.width}x{screenshot.height} "
                f"-> {output_path}"
            )

    print("Capture complete.")


if __name__ == "__main__":
    main()