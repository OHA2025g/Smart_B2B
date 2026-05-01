from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "SupplierProfile.jsx"
t = p.read_text("utf-8")
if "SupplierPlanBadges" in t:
    print("skip")
    raise SystemExit(0)

t = t.replace(
    "import { Badge } from '../components/ui/Badge';\n",
    "import { Badge } from '../components/ui/Badge';\nimport { SupplierPlanBadges } from '../components/SupplierPlanBadges';\n",
    1,
)

t = t.replace(
    """                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{displayName}</h1>
                  {profile.verified && (
                    <Badge variant="success" className="gap-1 font-semibold !bg-emerald-500/20 !text-emerald-100 !ring-emerald-400/40">
                      <CheckCircle className="h-3.5 w-3.5" /> Verified supplier
                    </Badge>
                  )}
                </div>""",
    """                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{displayName}</h1>
                </div>
                <div className="mb-2">
                  <SupplierPlanBadges
                    plan={profile.subscriptionPlan}
                    verified={profile.verified}
                    featured={profile.isFeaturedSupplier}
                    searchBoost={profile.searchBoostLabel}
                  />
                </div>""",
    1,
)

p.write_text(t, "utf-8")
print("ok")
