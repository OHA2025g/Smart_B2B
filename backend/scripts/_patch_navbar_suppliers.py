from pathlib import Path

p = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "components" / "Navbar.jsx"
t = p.read_text(encoding="utf-8")
if "to=\"/suppliers\"" in t:
    print("skip")
    raise SystemExit(0)
t = t.replace(
    '            <NavLink to="/products">Products</NavLink>\n',
    '            <NavLink to="/products">Products</NavLink>\n            <NavLink to="/suppliers">Suppliers</NavLink>\n',
    1,
)
p.write_text(t, encoding="utf-8")
print("navbar ok")
