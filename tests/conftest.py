import sys
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / ".github" / "skills"
sys.path.insert(0, str(SKILLS / "mcal-reference-s32k358" / "scripts"))
sys.path.insert(0, str(SKILLS / "mcal-pdf-json-extractor" / "scripts"))
sys.path.insert(0, str(SKILLS / "mcal-hardware-pdf-extractor" / "scripts"))
sys.path.insert(0, str(SKILLS / "mcal-graph-loader" / "scripts"))
