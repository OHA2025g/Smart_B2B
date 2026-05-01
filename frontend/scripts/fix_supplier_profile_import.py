from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "SupplierProfile.jsx"
t = p.read_text("utf-8")
line = "import { formatDateTimeIst } from '../lib/istTime';\n"
if line not in t:
    t = t.replace(
        "import { getCategoryImage } from '../utils/getCategoryImage';\n",
        "import { getCategoryImage } from '../utils/getCategoryImage';\n" + line,
        1,
    )
p.write_text(t, "utf-8")
print("ok")
