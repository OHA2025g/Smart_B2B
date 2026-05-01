from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "components" / "Navbar.jsx"
t = p.read_text("utf-8")
if "seller/subscription" in t:
    print("skip")
    raise SystemExit(0)
t = t.replace(
    '                    <NavLink to="/seller/rfqs">RFQs</NavLink>\n',
    '                    <NavLink to="/seller/rfqs">RFQs</NavLink>\n                    <NavLink to="/seller/subscription">Subscription</NavLink>\n',
    1,
)
p.write_text(t, "utf-8")
print("ok")
