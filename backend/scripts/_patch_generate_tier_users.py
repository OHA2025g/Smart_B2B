"""
Patch generate_demo_data.py: 3 classroom tier sellers + clear payments + apply_demo args.
Run from repo: python backend/scripts/_patch_generate_tier_users.py
"""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "scripts" / "generate_demo_data.py"
t = p.read_text("utf-8")

if "freesupplier@smartb2b.com" in t:
    print("already patched")
    raise SystemExit(0)

t = t.replace(
    "Preserves: admin@smartb2b.com, seller@example.com, buyer@example.com.\n",
    "Preserves: admin, seller@, buyer@, and classroom tier sellers (free / GO / PRO).\n",
    1,
)
t = t.replace(
    'PRESERVED_EMAILS = {"admin@smartb2b.com", "seller@example.com", "buyer@example.com"}\n',
    'PRESERVED_EMAILS = {\n'
    '    "admin@smartb2b.com",\n'
    '    "seller@example.com",\n'
    '    "buyer@example.com",\n'
    '    "freesupplier@smartb2b.com",\n'
    '    "gosupplier@smartb2b.com",\n'
    '    "prosupplier@smartb2b.com",\n'
    "}\n",
    1,
)

old_ensure = '''async def ensure_preserved_users(db):
    """Ensure admin, seller@example.com, buyer@example.com exist; return their ObjectIds."""
    now = _now()
    users_coll = db.users
    result = {}

    for email, role, name, pwd, verified in [
        ("admin@smartb2b.com", "admin", "Admin User", "Admin@123", False),
        ("seller@example.com", "seller", "Demo Seller", "Seller@123", True),
        ("buyer@example.com", "buyer", "Demo Buyer", "Buyer@123", False),
    ]:
        u = await users_coll.find_one({"email": email})
        if not u:
            doc = {
                "email": email,
                "password": pwd_context.hash(pwd),
                "role": role,
                "name": name,
                "isBanned": False,
                "isVerifiedSupplier": verified,
                "createdAt": now,
            }
            r = await users_coll.insert_one(doc)
            result[email] = r.inserted_id
            print(f"  Created preserved user: {email}")
        else:
            result[email] = u["_id"]
    return result["admin@smartb2b.com"], result["seller@example.com"], result["buyer@example.com"]'''

new_ensure = '''async def ensure_preserved_users(db):
    """Ensure core + classroom Free/GO/PRO supplier accounts; return 6 user ObjectIds."""
    now = _now()
    users_coll = db.users
    result = {}

    for email, role, name, pwd, verified in [
        ("admin@smartb2b.com", "admin", "Admin User", "Admin@123", False),
        ("seller@example.com", "seller", "Demo Seller", "Seller@123", True),
        ("buyer@example.com", "buyer", "Demo Buyer", "Buyer@123", False),
        ("freesupplier@smartb2b.com", "seller", "Classroom Free Supplier", "FreeDemo@123", True),
        ("gosupplier@smartb2b.com", "seller", "Classroom GO Supplier", "GoDemo@123", True),
        ("prosupplier@smartb2b.com", "seller", "Classroom PRO Supplier", "ProDemo@123", True),
    ]:
        u = await users_coll.find_one({"email": email})
        if not u:
            doc = {
                "email": email,
                "password": pwd_context.hash(pwd),
                "role": role,
                "name": name,
                "isBanned": False,
                "isVerifiedSupplier": verified,
                "createdAt": now,
            }
            r = await users_coll.insert_one(doc)
            result[email] = r.inserted_id
            print(f"  Created preserved user: {email}")
        else:
            result[email] = u["_id"]
    return (
        result["admin@smartb2b.com"],
        result["seller@example.com"],
        result["buyer@example.com"],
        result["freesupplier@smartb2b.com"],
        result["gosupplier@smartb2b.com"],
        result["prosupplier@smartb2b.com"],
    )'''

if old_ensure not in t:
    raise SystemExit("ensure_preserved block not found")
t = t.replace(old_ensure, new_ensure, 1)

old_clear = """async def clear_demo_data(db, preserved_user_ids):
    \"\"\"Remove demo-generated data; preserve only the three fixed users and their profiles.\"\"\"
    admin_id, seller_id, buyer_id = preserved_user_ids
    preserved = {admin_id, seller_id, buyer_id}"""
new_clear = """async def clear_demo_data(db, preserved_user_ids):
    \"\"\"Remove demo-generated data; preserve 6 fixed accounts.\"\"\"
    admin_id, seller_id, buyer_id, free_id, go_id, pro_id = preserved_user_ids
    preserved = {admin_id, seller_id, buyer_id, free_id, go_id, pro_id}"""
t = t.replace(old_clear, new_clear, 1)
t = t.replace(
    'print("  Cleared demo data (preserved admin, seller@example.com, buyer@example.com).")',
    'print("  Cleared demo data (preserved 6 core accounts + classroom tier suppliers).")',
    1,
)
# clear payments and subscriptions for clean re-seed
insert_after_notifications = "    await db.notifications.delete_many({})"
if insert_after_notifications in t and "db.payments.delete" not in t:
    t = t.replace(
        insert_after_notifications,
        insert_after_notifications
        + "\n    await db.payments.delete_many({})\n    await db.seller_subscriptions.delete_many({})",
        1,
    )

old_create = """async def create_users(db, admin_id, seller_id, buyer_id):
    \"\"\"Create demo sellers and buyers (counts from COUNTS) with realistic Indian names/emails.\"\"\"
    preserved = {admin_id, seller_id, buyer_id}"""
new_create = """async def create_users(db, admin_id, seller_id, buyer_id, free_id, go_id, pro_id):
    \"\"\"Create demo sellers and buyers (counts from COUNTS) with realistic Indian names/emails.\"\"\"
    preserved = {admin_id, seller_id, buyer_id, free_id, go_id, pro_id}"""
t = t.replace(old_create, new_create, 1)
t = t.replace(
    "    all_sellers = [seller_id] + sellers\n    all_buyers = [buyer_id] + buyers",
    "    all_sellers = [seller_id, free_id, go_id, pro_id] + sellers\n    all_buyers = [buyer_id] + buyers",
    1,
)

# run()
t = t.replace(
    "    print(\"1. Ensuring preserved users...\")\n    admin_id, seller_id, buyer_id = await ensure_preserved_users(db)\n    preserved = (admin_id, seller_id, buyer_id)",
    "    print(\"1. Ensuring preserved users...\")\n    admin_id, seller_id, buyer_id, free_id, go_id, pro_id = await ensure_preserved_users(db)\n    preserved = (admin_id, seller_id, buyer_id, free_id, go_id, pro_id)",
    1,
)
t = t.replace(
    "    all_sellers, all_buyers = await create_users(db, admin_id, seller_id, buyer_id)",
    "    all_sellers, all_buyers = await create_users(db, admin_id, seller_id, buyer_id, free_id, go_id, pro_id)",
    1,
)

# showcase company names + 1 product each
showcase_fn = r'''

async def apply_classroom_tier_showcase(db, free_id, go_id, pro_id, category_names):
    """Distinct company names + one obvious listing per classroom tier (for teacher demo)."""
    now = _now()
    cat0 = category_names[0] if category_names else "Industrial"
    await db.companyprofiles.update_one(
        {"user": free_id},
        {
            "$set": {
                "user": free_id,
                "companyName": "Classroom FREE — Standard Supplier",
                "description": "Free plan: standard listing, limited RFQ visibility (demo).",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "phone": "+91 9000000001",
            }
        },
        upsert=True,
    )
    await db.companyprofiles.update_one(
        {"user": go_id},
        {
            "$set": {
                "user": go_id,
                "companyName": "Classroom GO — RFQ+ Analytics",
                "description": "GO plan: unlimited RFQ viewing and quote replies, basic analytics (demo).",
                "city": "Bengaluru",
                "state": "Karnataka",
                "country": "India",
                "phone": "+91 9000000002",
            }
        },
        upsert=True,
    )
    await db.companyprofiles.update_one(
        {"user": pro_id},
        {
            "$set": {
                "user": pro_id,
                "companyName": "Classroom PRO — Featured + Boost",
                "description": "PRO plan: search boost, featured badge, priority discovery (demo).",
                "city": "New Delhi",
                "state": "Delhi",
                "country": "India",
                "phone": "+91 9000000003",
            }
        },
        upsert=True,
    )
    await db.products.insert_many(
        [
            {
                "seller": free_id,
                "title": "[FREE tier] MS angles — standard listing",
                "description": "Demo product for Free supplier account.",
                "category": cat0,
                "price": 199.0,
                "unit": "kg",
                "minOrderQuantity": 10,
                "city": "Mumbai",
                "isActive": True,
                "createdAt": now,
            },
            {
                "seller": go_id,
                "title": "[GO tier] Steel pipes — full RFQ access",
                "description": "Demo product for GO supplier account.",
                "category": cat0,
                "price": 449.0,
                "unit": "meter",
                "minOrderQuantity": 50,
                "city": "Bengaluru",
                "isActive": True,
                "createdAt": now,
            },
            {
                "seller": pro_id,
                "title": "[PRO tier] Industrial fasteners — featured + boost",
                "description": "Demo product for PRO supplier account (featured in listings).",
                "category": cat0,
                "price": 899.0,
                "unit": "box",
                "minOrderQuantity": 5,
                "city": "New Delhi",
                "isActive": True,
                "createdAt": now,
            },
        ]
    )
    print("  Applied classroom FREE/GO/PRO showcase companies + products.")
'''
# insert before async def run()
if "apply_classroom_tier_showcase" not in t:
    t = t.replace("async def run():\n", showcase_fn + "\nasync def run():\n", 1)

t = t.replace(
    "    print(\"5. Creating company profiles...\")\n    await create_company_profiles(db, all_sellers)",
    "    print(\"5. Creating company profiles...\")\n    await create_company_profiles(db, all_sellers)\n    await apply_classroom_tier_showcase(db, free_id, go_id, pro_id, category_names)",
    1,
)

t = t.replace(
    "    await apply_demo_plans_payments(db, all_sellers, seller_id, buyer_id)",
    "    await apply_demo_plans_payments(db, all_sellers, seller_id, buyer_id, free_id, go_id, pro_id)",
    1,
)

t = t.replace(
    '    print("\\nPreserved credentials: admin@smartb2b.com / Admin@123, seller@example.com / Seller@123, buyer@example.com / Buyer@123")',
    '    print("\\nPreserved logins (passwords):")\n    print("  admin@smartb2b.com  / Admin@123")\n    print("  buyer@example.com   / Buyer@123")\n    print("  seller@example.com  / Seller@123  (general free seller)")\n    print("  freesupplier@smartb2b.com  / FreeDemo@123  — Free tier classroom")\n    print("  gosupplier@smartb2b.com   / GoDemo@123   — GO tier classroom")\n    print("  prosupplier@smartb2b.com  / ProDemo@123  — PRO tier classroom")',
    1,
)

p.write_text(t, "utf-8")
print("ok")
