"""
Production-style demo data generation for SmartB2B mid-term demo.

Populates: users, companyprofiles, categories, products, wishlistitems,
cartitems, rfqs, quotes, orders, supplier_scores, adminactionlogs.

Preserves: admin@smartb2b.com, seller@example.com, buyer@example.com.

Run: python -m scripts.generate_demo_data
"""
import asyncio
import os
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

try:
    from faker import Faker
    fake = Faker("en_IN")
except ImportError:
    fake = None

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/smartb2b")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PRESERVED_EMAILS = {"admin@smartb2b.com", "seller@example.com", "buyer@example.com"}

COUNTS = {
    "categories": 12,
    "sellers": 25,
    "buyers": 90,
    "products": 600,
    "wishlist_items": 300,
    "cart_items": 180,
    "rfqs": 120,
    "quotes": 260,
    "orders": 70,
}

RFQ_STATUSES = ["sent", "quoted", "accepted", "closed"]
RFQ_STATUS_WEIGHTS = [0.20, 0.22, 0.50, 0.08]  # ~50% accepted RFQs to source 70 orders from quotes
ORDER_STATUSES = ["created", "confirmed", "processing", "shipped", "delivered"]

TRUST_LEVELS = [(85, 100, "Highly Trusted"), (70, 85, "Trusted"), (50, 70, "Moderate"), (0, 50, "Low Trust")]


def _db_name():
    path = urlparse(MONGODB_URI).path
    name = (path or "/").strip("/").split("/")[0].split("?")[0]
    return name or "smartb2b"


def slug(s):
    return re.sub(r"[^a-z0-9-]", "", s.lower().replace(" ", "-"))


def _trust_level(score):
    for low, high, label in TRUST_LEVELS:
        if low <= score < high or (high == 100 and score == 100):
            return label
    return "Low Trust"


# ----- Static Indian B2B data -----
INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad",
    "Surat", "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam",
    "Ludhiana", "Coimbatore", "Kochi", "Guwahati", "Chandigarh", "Nashik", "Vadodara", "Rajkot",
]

COMPANY_NAMES = [
    "Tata Steel Ltd", "Reliance Industries Ltd", "JSW Steel Ltd", "Hindalco Industries Ltd",
    "Vedanta Ltd", "Aditya Birla Group", "Larsen & Toubro Ltd", "Bharat Forge Ltd",
    "Usha Martin Ltd", "Jindal Steel & Power Ltd", "SAIL", "Essar Steel",
    "Supreme Industries Ltd", "Asian Paints Ltd", "Grasim Industries Ltd", "ITC Ltd",
    "Godrej Industries Ltd", "Maruti Suzuki India Ltd", "Bajaj Auto Ltd", "Mahindra & Mahindra Ltd",
    "Sun Pharma Ltd", "Dr. Reddy's Laboratories", "Lupin Ltd", "Aurobindo Pharma Ltd",
    "Dabur India Ltd", "Emami Ltd", "Britannia Industries Ltd", "Nestle India Ltd",
]

CATEGORY_PRODUCTS = {
    "Industrial": ["Steel pipes", "MS angles", "Wire rods", "Cold rolled coils", "Galvanized sheets", "Stainless steel plates", "Industrial fasteners", "Bearings", "Conveyor belts", "Hydraulic cylinders"],
    "Textiles": ["Cotton yarn", "Polyester fabric", "Denim cloth", "Woolen yarn", "Silk fabric", "Technical textiles", "Home textiles", "Industrial fabric", "Cotton waste", "Spun yarn"],
    "Electronics": ["PCB boards", "LED components", "Semiconductors", "Power adapters", "Cables and connectors", "Sensors", "Display modules", "Batteries", "Relays", "Transformers"],
    "Agriculture": ["Fertilizers", "Seeds", "Pesticides", "Irrigation equipment", "Tractors parts", "Harvesting tools", "Grain storage bags", "Organic manure", "Spray pumps", "Greenhouse film"],
    "Chemicals": ["Caustic soda", "Sulphuric acid", "Hydrogen peroxide", "Industrial salts", "Solvents", "Pigments", "Resins", "Surfactants", "Pharma intermediates", "Cleaning chemicals"],
    "Machinery": ["CNC machines", "Lathe machines", "Drilling machines", "Grinding wheels", "Cutting tools", "Pumps and motors", "Gearboxes", "Compressors", "Boilers", "Material handling equipment"],
    "Construction": ["Cement", "TMT bars", "Bricks", "Sand", "Ready mix concrete", "Roofing sheets", "Plywood", "Paint", "Tiles", "Structural steel"],
    "Automotive": ["Auto components", "Engine parts", "Brake pads", "Filters", "Tyres", "Batteries", "Gaskets", "Clutch plates", "Suspension parts", "Electrical parts"],
    "Pharmaceuticals": ["API", "Tablets", "Capsules", "Syrups", "Injectables", "Excipients", "Packaging materials", "Lab equipment", "Clean room supplies", "Clinical trial materials"],
    "Food & Beverage": ["Wheat flour", "Rice", "Sugar", "Edible oil", "Spices", "Pulses", "Packaged foods", "Beverage concentrates", "Dairy products", "Frozen foods"],
    "Plastics": ["HDPE pipes", "PVC granules", "Plastic sheets", "Injection moulded parts", "Packaging film", "PET bottles", "Plastic containers", "LDPE film", "Polycarbonate sheets", "Nylon components"],
    "Paper": ["Kraft paper", "Tissue paper", "Corrugated boxes", "Paper boards", "Recycled paper", "Coated paper", "Pulp", "Paper bags", "Labels", "Printing paper"],
}


def _now():
    return datetime.utcnow()


async def ensure_preserved_users(db):
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
    return result["admin@smartb2b.com"], result["seller@example.com"], result["buyer@example.com"]


async def clear_demo_data(db, preserved_user_ids):
    """Remove demo-generated data; preserve only the three fixed users and their profiles."""
    admin_id, seller_id, buyer_id = preserved_user_ids
    preserved = {admin_id, seller_id, buyer_id}

    # Order matters: dependents first
    await db.adminactionlogs.delete_many({})
    await db.orders.delete_many({})
    await db.quotes.delete_many({})
    await db.rfqs.delete_many({})
    await db.cartitems.delete_many({})
    await db.wishlistitems.delete_many({})
    await db.supplier_scores.delete_many({})
    await db.products.delete_many({})
    await db.inquiries.delete_many({})
    await db.messagethreads.delete_many({})
    # companyprofiles: delete those not for preserved users
    await db.companyprofiles.delete_many({"user": {"$nin": list(preserved)}})
    await db.categories.delete_many({})
    # users: delete anyone not in preserved
    await db.users.delete_many({"_id": {"$nin": list(preserved)}})
    print("  Cleared demo data (preserved admin, seller@example.com, buyer@example.com).")


def _product_title(category, product_list):
    base = random.choice(product_list)
    if fake:
        adj = fake.word() if random.random() > 0.6 else ""
        return f"{adj} {base}".strip() if adj else base
    return base


async def create_categories(db):
    """Create 12 categories with realistic names."""
    names = list(CATEGORY_PRODUCTS.keys())[: COUNTS["categories"]]
    now = _now()
    for name in names:
        await db.categories.insert_one({
            "name": name,
            "slug": slug(name),
            "isActive": True,
            "createdAt": now,
        })
    return names


async def create_users(db, admin_id, seller_id, buyer_id):
    """Create 25 sellers and 90 buyers with realistic Indian names/emails."""
    preserved = {admin_id, seller_id, buyer_id}
    now = _now()
    sellers, buyers = [], []

    def _email(role, i):
        if fake:
            name = fake.first_name().lower() + str(i)
            return f"{name}@{'seller' if role == 'seller' else 'buyer'}.demo.in"
        return f"{role}{i}@demo.in"

    for i in range(1, COUNTS["sellers"] + 1):
        email = _email("seller", i)
        if email in PRESERVED_EMAILS:
            continue
        name = fake.company() if fake else f"Seller {i}"
        doc = {
            "email": email,
            "password": pwd_context.hash("Demo@123"),
            "role": "seller",
            "name": name[:80],
            "isBanned": False,
            "isVerifiedSupplier": random.random() < 0.35,
            "createdAt": now,
        }
        r = await db.users.insert_one(doc)
        sellers.append(r.inserted_id)

    for i in range(1, COUNTS["buyers"] + 1):
        email = _email("buyer", i)
        if email in PRESERVED_EMAILS:
            continue
        name = fake.company() if fake else f"Buyer {i}"
        doc = {
            "email": email,
            "password": pwd_context.hash("Demo@123"),
            "role": "buyer",
            "name": name[:80],
            "isBanned": False,
            "isVerifiedSupplier": False,
            "createdAt": now,
        }
        r = await db.users.insert_one(doc)
        buyers.append(r.inserted_id)

    # Include preserved seller/buyer in the lists we return for generating data
    all_sellers = [seller_id] + sellers
    all_buyers = [buyer_id] + buyers
    return all_sellers, all_buyers


async def create_company_profiles(db, seller_ids):
    """One company profile per seller; skip if profile already exists (e.g. preserved user)."""
    now = _now()
    for sid in seller_ids:
        existing = await db.companyprofiles.find_one({"user": sid})
        if existing:
            continue
        company = random.choice(COMPANY_NAMES)
        city = random.choice(INDIAN_CITIES)
        await db.companyprofiles.insert_one({
            "user": sid,
            "companyName": company,
            "description": "B2B supplier" if fake else None,
            "city": city,
            "state": "Maharashtra" if city == "Mumbai" else "Karnataka" if city == "Bangalore" else "Gujarat",
            "country": "India",
            "phone": f"+91 {random.randint(9000000000, 9999999999)}" if random.random() > 0.2 else None,
            "website": None,
            "gstNumber": f"27AABCU{random.randint(1000, 9999)}Z{random.randint(1, 9)}Z" if random.random() > 0.3 else None,
            "createdAt": now,
        })


async def create_products(db, seller_ids, category_names):
    """600 products across sellers and categories."""
    now = _now()
    products = []
    units = ["unit", "kg", "meter", "piece", "tonne", "litre", "box", "set"]
    for _ in range(COUNTS["products"]):
        cat = random.choice(category_names)
        seller = random.choice(seller_ids)
        product_list = CATEGORY_PRODUCTS.get(cat, ["Product"])
        title = _product_title(cat, product_list)
        price = round(random.uniform(50, 50000), 2)
        min_qty = random.choice([1, 10, 50, 100, 500, 1000])
        doc = {
            "seller": seller,
            "title": title[:120],
            "description": f"B2B {title} - bulk supply" if random.random() > 0.5 else None,
            "category": cat,
            "price": price,
            "unit": random.choice(units),
            "minOrderQuantity": min_qty,
            "city": random.choice(INDIAN_CITIES),
            "isActive": True,
            "createdAt": now,
        }
        r = await db.products.insert_one(doc)
        products.append({"_id": r.inserted_id, "seller": seller, "category": cat, "price": price, "minOrderQuantity": min_qty})
    return products


async def create_wishlist_and_cart(db, buyer_ids, product_ids):
    """300 wishlist items, 180 cart items; no duplicate (buyer, product) for wishlist/cart."""
    now = _now()
    wishlist_pairs = set()
    cart_pairs = set()
    for _ in range(COUNTS["wishlist_items"]):
        b = random.choice(buyer_ids)
        p = random.choice(product_ids)
        if (b, p) in wishlist_pairs:
            continue
        wishlist_pairs.add((b, p))
        await db.wishlistitems.insert_one({"buyerId": b, "productId": p, "createdAt": now})
    for _ in range(COUNTS["cart_items"]):
        b = random.choice(buyer_ids)
        p = random.choice(product_ids)
        if (b, p) in cart_pairs:
            continue
        cart_pairs.add((b, p))
        await db.cartitems.insert_one({
            "buyerId": b,
            "productId": p,
            "quantity": max(1, random.randint(1, 500)),
            "notes": "Sample note" if random.random() > 0.7 else "",
            "createdAt": now,
        })


def _build_products_by_seller(products):
    by_seller = {}
    for p in products:
        sid = p["seller"]
        if sid not in by_seller:
            by_seller[sid] = []
        by_seller[sid].append(p)
    return by_seller


async def create_rfqs(db, buyer_ids, products, products_by_seller):
    """120 RFQs: each buyer creates RFQs with 1-4 products; status sent/quoted/accepted/closed."""
    now = _now()
    rfqs = []
    for i in range(COUNTS["rfqs"]):
        buyer_id = random.choice(buyer_ids)
        n_items = random.randint(1, min(4, len(products)))
        chosen = random.sample(products, n_items)
        items = [
            {"productId": p["_id"], "quantity": p.get("minOrderQuantity", 10), "notes": "RFQ note" if random.random() > 0.6 else ""}
            for p in chosen
        ]
        status = random.choices(RFQ_STATUSES, weights=RFQ_STATUS_WEIGHTS)[0]
        doc = {
            "buyerId": buyer_id,
            "items": items,
            "status": status,
            "createdAt": now - timedelta(days=random.randint(0, 60)),
            "updated_at": now,
        }
        r = await db.rfqs.insert_one(doc)
        rfqs.append({
            "_id": r.inserted_id,
            "buyerId": buyer_id,
            "items": items,
            "status": status,
            "product_ids": [p["_id"] for p in chosen],
            "sellers_in_rfq": list({p["seller"] for p in chosen}),
        })
    return rfqs


async def create_quotes_and_orders_final(db, rfqs, products_by_seller, all_products_map):
    """Create 260 quotes; for accepted ones create up to 70 orders. One quote per (rfq, seller) that has products in RFQ."""
    now = _now()
    used = set()
    quotes_created = 0
    orders_to_create = []  # list of (quote_id, order_doc)

    for rfq in rfqs:
        for seller_id in rfq["sellers_in_rfq"]:
            if quotes_created >= COUNTS["quotes"]:
                break
            key = (str(rfq["_id"]), str(seller_id))
            if key in used:
                continue
            used.add(key)
            quote_items = []
            for it in rfq["items"]:
                pid = it["productId"]
                p = all_products_map.get(pid)
                if not p or p["seller"] != seller_id:
                    continue
                unit_price = round(p["price"] * random.uniform(0.92, 1.12), 2)
                qty = it["quantity"] + random.randint(0, 20)
                quote_items.append({"productId": pid, "unitPrice": unit_price, "availableQty": qty, "deliveryDays": random.randint(3, 14)})
            if not quote_items:
                continue
            status = "submitted"
            if rfq["status"] == "accepted" and len(orders_to_create) < COUNTS["orders"] and random.random() < 0.55:
                status = "accepted"
            elif random.random() < 0.12:
                status = "rejected"
            r = await db.quotes.insert_one({
                "rfqId": rfq["_id"],
                "sellerId": seller_id,
                "items": quote_items,
                "message": "Competitive quote." if random.random() > 0.6 else "",
                "status": status,
                "createdAt": now - timedelta(days=random.randint(0, 40)),
            })
            quotes_created += 1
            if status == "accepted" and len(orders_to_create) < COUNTS["orders"] and random.random() < 0.65:
                total = sum(it["unitPrice"] * it["availableQty"] for it in quote_items)
                order_items = [{"productId": it["productId"], "quantity": it["availableQty"], "agreedUnitPrice": it["unitPrice"]} for it in quote_items]
                orders_to_create.append({
                    "rfqId": rfq["_id"],
                    "quoteId": r.inserted_id,
                    "buyerId": rfq["buyerId"],
                    "sellerId": seller_id,
                    "items": order_items,
                    "totalAmount": round(total, 2),
                })
    for o in orders_to_create[: COUNTS["orders"]]:
        await db.orders.insert_one({
            "rfqId": o["rfqId"],
            "quoteId": o["quoteId"],
            "buyerId": o["buyerId"],
            "sellerId": o["sellerId"],
            "items": o["items"],
            "totalAmount": o["totalAmount"],
            "status": random.choice(ORDER_STATUSES),
            "createdAt": now - timedelta(days=random.randint(0, 25)),
        })
    return quotes_created, min(len(orders_to_create), COUNTS["orders"])


async def create_supplier_scores(db, seller_ids):
    """Compute and store trust score for each seller using the formula."""
    now = _now()
    for sid in seller_ids:
        profile = await db.companyprofiles.find_one({"user": sid})
        profile_score = 0.0
        if profile:
            fields = ["companyName", "description", "city", "state", "country", "phone", "website", "gstNumber"]
            filled = sum(1 for f in fields if profile.get(f))
            profile_score = min(100, (filled / len(fields)) * 100) if fields else 0
        user = await db.users.find_one({"_id": sid})
        verified_status = 100.0 if user and user.get("isVerifiedSupplier") else 0.0
        quotes_c = await db.quotes.count_documents({"sellerId": sid})
        my_prod_ids = [p["_id"] for p in await db.products.find({"seller": sid}, {"_id": 1}).to_list(None)]
        rfqs_c = await db.rfqs.count_documents({"items.productId": {"$in": my_prod_ids}}) if my_prod_ids else 0
        response_rate = min(100, (quotes_c / rfqs_c) * 100) if rfqs_c else 80.0
        products_c = await db.products.count_documents({"seller": sid, "isActive": True})
        product_strength = min(100, products_c * 10)
        buyer_rating = 70.0
        total = (
            0.30 * profile_score + 0.20 * response_rate + 0.20 * product_strength
            + 0.15 * buyer_rating + 0.15 * verified_status
        )
        total = round(min(100, max(0, total)), 1)
        trust_level = _trust_level(total)
        await db.supplier_scores.update_one(
            {"seller_id": sid},
            {"$set": {
                "profile_completeness": round(profile_score, 1),
                "response_rate": round(response_rate, 1),
                "product_strength": round(product_strength, 1),
                "buyer_rating": buyer_rating,
                "verified_status": verified_status,
                "total_score": total,
                "trust_level": trust_level,
                "updated_at": now,
            }},
            upsert=True,
        )


async def create_admin_logs(db, admin_id, seller_ids):
    """Admin logs for verification, user creation, score recalc."""
    now = _now()
    for sid in random.sample(seller_ids, min(15, len(seller_ids))):
        await db.adminactionlogs.insert_one({
            "adminId": admin_id,
            "actionType": "VERIFY_SUPPLIER",
            "targetId": sid,
            "details": {"verified": True},
            "createdAt": now - timedelta(days=random.randint(1, 90)),
        })
    for _ in range(5):
        await db.adminactionlogs.insert_one({
            "adminId": admin_id,
            "actionType": "RECALCULATE_SCORE",
            "targetId": random.choice(seller_ids),
            "details": {},
            "createdAt": now - timedelta(days=random.randint(1, 30)),
        })
    await db.adminactionlogs.insert_one({
        "adminId": admin_id,
        "actionType": "USER_CREATED",
        "targetId": None,
        "details": {"message": "Demo data generation completed"},
        "createdAt": now,
    })


async def run():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[_db_name()]
    print("Connected to MongoDB")

    print("1. Ensuring preserved users...")
    admin_id, seller_id, buyer_id = await ensure_preserved_users(db)
    preserved = (admin_id, seller_id, buyer_id)

    print("2. Clearing demo data...")
    await clear_demo_data(db, preserved)

    print("3. Creating categories...")
    category_names = await create_categories(db)

    print("4. Creating users (sellers + buyers)...")
    all_sellers, all_buyers = await create_users(db, admin_id, seller_id, buyer_id)

    print("5. Creating company profiles...")
    await create_company_profiles(db, all_sellers)

    print("6. Creating products...")
    products = await create_products(db, all_sellers, category_names)
    product_ids = [p["_id"] for p in products]
    products_by_seller = _build_products_by_seller(products)
    all_products_map = {p["_id"]: p for p in products}

    print("7. Creating wishlist and cart items...")
    await create_wishlist_and_cart(db, all_buyers, product_ids)

    print("8. Creating RFQs...")
    rfqs = await create_rfqs(db, all_buyers, products, products_by_seller)

    print("9. Creating quotes and orders...")
    n_quotes, n_orders = await create_quotes_and_orders_final(db, rfqs, products_by_seller, all_products_map)

    print("10. Creating supplier scores...")
    await create_supplier_scores(db, all_sellers)

    print("11. Creating admin logs...")
    await create_admin_logs(db, admin_id, all_sellers)

    # Summary
    print("\n--- Summary ---")
    for name, coll in [
        ("users", db.users),
        ("companyprofiles", db.companyprofiles),
        ("categories", db.categories),
        ("products", db.products),
        ("wishlistitems", db.wishlistitems),
        ("cartitems", db.cartitems),
        ("rfqs", db.rfqs),
        ("quotes", db.quotes),
        ("orders", db.orders),
        ("supplier_scores", db.supplier_scores),
        ("adminactionlogs", db.adminactionlogs),
    ]:
        c = await coll.count_documents({})
        print(f"  {name}: {c}")
    print("\nPreserved credentials: admin@smartb2b.com / Admin@123, seller@example.com / Seller@123, buyer@example.com / Buyer@123")
    print("Demo users (sellers/buyers): password Demo@123")
    client.close()


if __name__ == "__main__":
    asyncio.run(run())
