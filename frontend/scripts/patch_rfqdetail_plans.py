from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "RFQDetail.jsx"
t = p.read_text("utf-8")
if "SupplierPlanBadges" in t:
    print("skip")
    raise SystemExit(0)

t = t.replace(
    "import { Badge } from '../components/ui/Badge';\n",
    "import { Badge } from '../components/ui/Badge';\nimport { SupplierPlanBadges } from '../components/SupplierPlanBadges';\n",
    1,
)

old = """                        <span className="block">{(row.company_name || '').trim() || row.seller_name || '—'}</span>
                        {row.verified_supplier && (
                          <Badge variant="success" className="mt-2 text-[10px]">
                            Verified
                          </Badge>
                        )}"""
new = """                        <span className="block">{(row.company_name || '').trim() || row.seller_name || '—'}</span>
                        <div className="mt-1.5">
                          <SupplierPlanBadges
                            plan={row.subscriptionPlan}
                            verified={row.verified_supplier}
                            featured={row.is_featured_supplier}
                            compact
                          />
                        </div>"""
if old not in t:
    # try to locate by partial match
    i = t.find("row.verified_supplier &&")
    if i == -1:
        raise SystemExit("block not found")
    raise SystemExit("exact old block not found; check em-dash character")
t = t.replace(old, new, 1)
p.write_text(t, "utf-8")
print("ok")
