from pathlib import Path
from urllib.request import urlretrieve
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

target = Path(__file__).resolve().parents[1] / "backend/assets"
target.mkdir(parents=True, exist_ok=True)
if not (target / "NotoSansJP.ttf").exists():
    urlretrieve(
        "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf",
        target / "NotoSansJP-variable.ttf",
    )
    font = instantiateVariableFont(
        TTFont(target / "NotoSansJP-variable.ttf"), {"wght": 400}, inplace=True
    )
    font.save(target / "NotoSansJP.ttf")
    (target / "NotoSansJP-variable.ttf").unlink()
    urlretrieve(
        "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/OFL.txt",
        target / "OFL.txt",
    )
print("Japanese PDF font ready.")
