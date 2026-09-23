"""Create the Windows icon from the mark used by frontend/public/favicon.svg."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "desktop-assets" / "Estimate2.ico"
SCALE = 12
SIDE = 48 * SCALE


def point(x: int, y: int) -> tuple[int, int]:
    return x * SCALE, y * SCALE


canvas = Image.new("RGBA", (SIDE, SIDE), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)
draw.rounded_rectangle(
    (0, 0, SIDE - 1, SIDE - 1), radius=14 * SCALE, fill="#176b58"
)
draw.polygon(
    [
        point(12, 32), point(12, 17), point(18, 17), point(18, 23),
        point(24, 17), point(30, 17), point(30, 23), point(36, 17),
        point(36, 32), point(30, 32), point(30, 24), point(24, 30),
        point(24, 24), point(18, 30), point(18, 32),
    ],
    fill="#ffffff",
)

DESTINATION.parent.mkdir(parents=True, exist_ok=True)
canvas.resize((512, 512), Image.Resampling.LANCZOS).save(
    DESTINATION.with_name("Estimate2-preview.png")
)
canvas.save(
    DESTINATION,
    format="ICO",
    sizes=[(size, size) for size in (16, 24, 32, 48, 64, 128, 256)],
)
print(f"Created {DESTINATION}")
