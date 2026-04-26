from pathlib import Path

p = Path(__file__).resolve().parents[2] / "frontend/src/pages/RFQDetail.jsx"
t = p.read_text(encoding="utf-8")
a = "import { Link } from 'react-router-dom';\nimport { useParams } from 'react-router-dom';"
b = "import { Link, useParams } from 'react-router-dom';"
if a in t:
    p.write_text(t.replace(a, b), encoding="utf-8")
    print("merged")
else:
    print("skip")
