"""
Production-style demo data generation for B2Bभारत mid-term demo.

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

# Target scale: hundreds of core entities + rich RFQ/order pipeline (12 categories, 3 preserved users).
# Tuned for a realistic B2B demo: busy listings, RFQ pipeline, orders, admin activity.
COUNTS = {
    "categories": 12,
    "sellers": 260,
    "buyers": 340,
    "products": 820,
    "wishlist_items": 620,
    "cart_items": 480,
    "rfqs": 680,
    "quotes": 1280,
    "orders": 520,
}

RFQ_STATUSES = ["sent", "quoted", "accepted", "closed"]
RFQ_STATUS_WEIGHTS = [0.12, 0.18, 0.62, 0.08]  # bias accepted RFQs for orders / realistic pipeline
# Full lifecycle (matches app / order updates) so fulfillment charts show a rich mix, not 1–2 random slices.
ORDER_STATUSES = ["created", "confirmed", "processing", "shipped", "delivered", "cancelled"]
# Skewed toward mid/late fulfillment (not equal sixths — strict round-robin made every slice ~16.7%).
ORDER_STATUS_SEED_WEIGHTS = [0.06, 0.09, 0.16, 0.26, 0.34, 0.09]
ORDER_STATUS_JITTER_UNIFORM = 0.14  # occasional flat pick so counts never stay perfectly periodic


def reset_order_status_sequence():
    """No-op placeholder (kept so run() does not need churn); status picks are stateless."""
    return


def next_demo_order_status_for_seller(_seller_id) -> str:
    """Weighted lifecycle mix + light jitter so pie charts look like real ops data, not placeholders."""
    if random.random() < ORDER_STATUS_JITTER_UNIFORM:
        return random.choice(ORDER_STATUSES)
    return random.choices(ORDER_STATUSES, weights=ORDER_STATUS_SEED_WEIGHTS, k=1)[0]


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
    await db.workflow_events.delete_many({})
    await db.notifications.delete_many({})
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
    """Create demo sellers and buyers (counts from COUNTS) with realistic Indian names/emails."""
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
    """Many products across sellers and categories (batched insert_many)."""
    now = _now()
    products = []
    units = ["unit", "kg", "meter", "piece", "tonne", "litre", "box", "set"]
    batch_docs = []
    batch_meta = []
    batch_size = 200

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
        batch_docs.append(doc)
        batch_meta.append({"seller": seller, "category": cat, "price": price, "minOrderQuantity": min_qty})
        if len(batch_docs) >= batch_size:
            res = await db.products.insert_many(batch_docs)
            for meta, oid in zip(batch_meta, res.inserted_ids):
                products.append({"_id": oid, **meta})
            batch_docs, batch_meta = [], []

    if batch_docs:
        res = await db.products.insert_many(batch_docs)
        for meta, oid in zip(batch_meta, res.inserted_ids):
            products.append({"_id": oid, **meta})
    return products


async def create_wishlist_and_cart(db, buyer_ids, product_ids):
    """Wishlist / cart rows; unique (buyer, product) per collection; batched inserts."""
    now = _now()
    wishlist_pairs = set()
    cart_pairs = set()
    wl_batch = []
    max_attempts = COUNTS["wishlist_items"] * 8
    attempts = 0
    while len(wishlist_pairs) < COUNTS["wishlist_items"] and attempts < max_attempts:
        attempts += 1
        b = random.choice(buyer_ids)
        p = random.choice(product_ids)
        if (b, p) in wishlist_pairs:
            continue
        wishlist_pairs.add((b, p))
        wl_batch.append({"buyerId": b, "productId": p, "createdAt": now})
        if len(wl_batch) >= 400:
            await db.wishlistitems.insert_many(wl_batch)
            wl_batch = []
    if wl_batch:
        await db.wishlistitems.insert_many(wl_batch)

    cart_batch = []
    max_c = COUNTS["cart_items"] * 8
    c_attempts = 0
    while len(cart_pairs) < COUNTS["cart_items"] and c_attempts < max_c:
        c_attempts += 1
        b = random.choice(buyer_ids)
        p = random.choice(product_ids)
        if (b, p) in cart_pairs:
            continue
        cart_pairs.add((b, p))
        cart_batch.append({
            "buyerId": b,
            "productId": p,
            "quantity": max(1, random.randint(1, 500)),
            "notes": "Sample note" if random.random() > 0.7 else "",
            "createdAt": now,
        })
        if len(cart_batch) >= 400:
            await db.cartitems.insert_many(cart_batch)
            cart_batch = []
    if cart_batch:
        await db.cartitems.insert_many(cart_batch)


def _build_products_by_seller(products):
    by_seller = {}
    for p in products:
        sid = p["seller"]
        if sid not in by_seller:
            by_seller[sid] = []
        by_seller[sid].append(p)
    return by_seller


async def create_rfqs(db, buyer_ids, products, products_by_seller):
    """RFQs with 1-4 products; status sent/quoted/accepted/closed (batched insert_many)."""
    now = _now()
    rfqs = []
    docs = []
    metas = []
    batch_size = 150
    for i in range(COUNTS["rfqs"]):
        buyer_id = random.choice(buyer_ids)
        n_items = random.randint(1, min(4, len(products)))
        chosen = random.sample(products, n_items)
        items = [
            {"productId": p["_id"], "quantity": p.get("minOrderQuantity", 10), "notes": "RFQ note" if random.random() > 0.6 else ""}
            for p in chosen
        ]
        status = random.choices(RFQ_STATUSES, weights=RFQ_STATUS_WEIGHTS)[0]
        created_at = now - timedelta(days=random.randint(0, 60))
        req_by = created_at + timedelta(days=random.randint(10, 50))
        doc = {
            "buyerId": buyer_id,
            "items": items,
            "status": status,
            "createdAt": created_at,
            "validUntil": created_at + timedelta(days=7),
            "deliveryLocation": random.choice(
                [
                    "Distribution Center North, Chicago, IL",
                    "Plant 2, Houston, TX",
                    "Warehouse B, Newark, NJ",
                    "Site 7, Phoenix, AZ",
                ]
            ),
            "requiredByDate": req_by,
            "buyerNotes": "Please confirm lead time and packaging."
            if random.random() > 0.5
            else None,
            "priority": random.choice(["normal", "urgent"]),
            "updated_at": now,
        }
        docs.append(doc)
        metas.append({
            "buyerId": buyer_id,
            "items": items,
            "status": status,
            "product_ids": [p["_id"] for p in chosen],
            "sellers_in_rfq": list({p["seller"] for p in chosen}),
        })
        if len(docs) >= batch_size:
            res = await db.rfqs.insert_many(docs)
            for oid, m in zip(res.inserted_ids, metas):
                rfqs.append({"_id": oid, **m})
            docs, metas = [], []

    if docs:
        res = await db.rfqs.insert_many(docs)
        for oid, m in zip(res.inserted_ids, metas):
            rfqs.append({"_id": oid, **m})
    return rfqs


async def create_quotes_and_orders_final(
    db,
    rfqs,
    all_products_map,
    *,
    quote_cap: int | None = None,
    order_cap: int | None = None,
    run_order_backfill: bool = True,
    quote_accept_if_rfq_accepted: float | None = None,
    quote_accept_if_rfq_quoted: float | None = None,
    order_if_quote_accepted: float | None = None,
):
    """Quotes: one per (rfq, seller) with line items; orders from accepted quotes; optional global backfill."""
    qc = COUNTS["quotes"] if quote_cap is None else quote_cap
    oc = COUNTS["orders"] if order_cap is None else order_cap
    p_q_when_accepted = 0.68 if quote_accept_if_rfq_accepted is None else quote_accept_if_rfq_accepted
    p_q_when_quoted = quote_accept_if_rfq_quoted
    p_order = 0.82 if order_if_quote_accepted is None else order_if_quote_accepted
    now = _now()
    used = set()
    quotes_created = 0
    orders_to_create = []
    quotes_done = False

    for rfq in rfqs:
        if quotes_done:
            break
        for seller_id in rfq["sellers_in_rfq"]:
            if quotes_created >= qc:
                quotes_done = True
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
            if rfq["status"] == "accepted" and len(orders_to_create) < oc and random.random() < p_q_when_accepted:
                status = "accepted"
            elif (
                p_q_when_quoted is not None
                and rfq["status"] == "quoted"
                and len(orders_to_create) < oc
                and random.random() < p_q_when_quoted
            ):
                status = "accepted"
            elif random.random() < 0.12:
                status = "rejected"
            q_created = now - timedelta(days=random.randint(0, 40))
            r = await db.quotes.insert_one({
                "rfqId": rfq["_id"],
                "sellerId": seller_id,
                "items": quote_items,
                "message": "Competitive quote." if random.random() > 0.6 else "",
                "status": status,
                "createdAt": q_created,
                "quoteValidUntil": q_created + timedelta(days=5),
            })
            quotes_created += 1
            if status == "accepted" and len(orders_to_create) < oc and random.random() < p_order:
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

    to_insert = orders_to_create[:oc]
    for o in to_insert:
        await db.orders.insert_one({
            "rfqId": o["rfqId"],
            "quoteId": o["quoteId"],
            "buyerId": o["buyerId"],
            "sellerId": o["sellerId"],
            "items": o["items"],
            "totalAmount": o["totalAmount"],
            "status": next_demo_order_status_for_seller(o["sellerId"]),
            "createdAt": now - timedelta(days=random.randint(0, 25)),
            "paymentStatus": random.choice(
                ["payment_pending", "escrow_held", "released", "payment_pending", "escrow_held", "refunded"]
            ),
        })

    if run_order_backfill:
        order_count = await db.orders.count_documents({})
        if order_count < COUNTS["orders"]:
            need = COUNTS["orders"] - order_count
            used_quote_ids = {o["quoteId"] for o in to_insert}
            async for qd in db.quotes.find({"status": "accepted"}):
                if need <= 0:
                    break
                qid = qd["_id"]
                if qid in used_quote_ids:
                    continue
                if await db.orders.find_one({"quoteId": qid}):
                    continue
                rfq_doc = await db.rfqs.find_one({"_id": qd["rfqId"]})
                if not rfq_doc:
                    continue
                quote_items = qd.get("items") or []
                if not quote_items:
                    continue
                total = sum(it["unitPrice"] * it["availableQty"] for it in quote_items)
                order_items = [{"productId": it["productId"], "quantity": it["availableQty"], "agreedUnitPrice": it["unitPrice"]} for it in quote_items]
                await db.orders.insert_one({
                    "rfqId": qd["rfqId"],
                    "quoteId": qid,
                    "buyerId": rfq_doc["buyerId"],
                    "sellerId": qd["sellerId"],
                    "items": order_items,
                    "totalAmount": round(total, 2),
                    "status": next_demo_order_status_for_seller(qd["sellerId"]),
                    "createdAt": now - timedelta(days=random.randint(0, 25)),
                    "paymentStatus": random.choice(
                        ["payment_pending", "escrow_held", "released", "payment_pending", "escrow_held", "refunded"]
                    ),
                })
                used_quote_ids.add(qid)
                need -= 1

    inserted_orders = len(to_insert)
    final_orders = await db.orders.count_documents({})
    if run_order_backfill:
        return quotes_created, min(final_orders, COUNTS["orders"])
    return quotes_created, inserted_orders


async def create_supplier_scores(db, seller_ids):
    """Store trust scores using the same service as the API (weighted formula)."""
    from app.services.supplier_score import recalculate_supplier_score

    for sid in seller_ids:
        try:
            await recalculate_supplier_score(sid)
        except Exception:
            continue



async def create_workflow_events_and_notifications(db, rfqs, admin_id, seller_ids, buyer_ids):
    """Add sample workflow_events and notifications for timeline/notifications UI."""
    now = _now()
    rfq_list = list(rfqs) if hasattr(rfqs, "__anext__") else rfqs
    n_rfq_events = min(len(rfq_list), max(280, min(COUNTS["rfqs"], 520)))
    for rfq in rfq_list[:n_rfq_events]:
        await db.workflow_events.insert_one({
            "entity_type": "rfq",
            "entity_id": rfq["_id"],
            "actor_id": rfq["buyerId"],
            "actor_role": "buyer",
            "event_type": "RFQ_CREATED",
            "event_label": "RFQ created",
            "metadata": {},
            "created_at": rfq.get("createdAt", now) - timedelta(hours=random.randint(0, 48)),
        })
    quote_evt_limit = min(650, max(160, COUNTS["quotes"] // 2))
    cursor = db.quotes.find({}).limit(quote_evt_limit)
    async for q in cursor:
        await db.workflow_events.insert_one({
            "entity_type": "rfq",
            "entity_id": q["rfqId"],
            "actor_id": q["sellerId"],
            "actor_role": "seller",
            "event_type": "QUOTE_SUBMITTED",
            "event_label": "Quote submitted",
            "metadata": {"quoteId": str(q["_id"])},
            "created_at": q.get("createdAt", now),
        })
        rfq_doc = await db.rfqs.find_one({"_id": q["rfqId"]})
        buyer_id = rfq_doc["buyerId"] if rfq_doc else (buyer_ids[0] if buyer_ids else None)
        if buyer_id:
            await db.notifications.insert_one({
                "user_id": buyer_id,
                "title": "New Quote",
                "message": "A supplier submitted a quote for your RFQ.",
                "type": "quote_submitted",
                "related_entity_type": "rfq",
                "related_entity_id": str(q["rfqId"]),
                "is_read": random.random() < 0.5,
                "created_at": q.get("createdAt", now),
            })
    order_evt_limit = min(480, max(100, COUNTS["orders"]))
    cursor_o = db.orders.find({}).limit(order_evt_limit)
    async for o in cursor_o:
        await db.workflow_events.insert_one({
            "entity_type": "order",
            "entity_id": o["_id"],
            "actor_id": o["buyerId"],
            "actor_role": "buyer",
            "event_type": "ORDER_CREATED",
            "event_label": "Order created",
            "metadata": {"rfqId": str(o.get("rfqId"))},
            "created_at": o.get("createdAt", now),
        })
        await db.notifications.insert_one({
            "user_id": o["sellerId"],
            "title": "New Order",
            "message": "You received a new order.",
            "type": "order_created",
            "related_entity_type": "order",
            "related_entity_id": str(o["_id"]),
            "is_read": random.random() < 0.4,
            "created_at": o.get("createdAt", now),
        })
    n_verified_notes = min(45, len(seller_ids))
    for sid in (random.sample(seller_ids, n_verified_notes) if seller_ids else []):
        await db.notifications.insert_one({
            "user_id": sid,
            "title": "Supplier verified",
            "message": "Your account has been verified as a supplier.",
            "type": "supplier_verified",
            "related_entity_type": "user",
            "related_entity_id": str(sid),
            "is_read": random.random() < 0.6,
            "created_at": now - timedelta(days=random.randint(1, 30)),
        })


async def create_admin_logs(db, admin_id, seller_ids):
    """Admin logs for verification, user creation, score recalc."""
    now = _now()
    n_verify = min(max(90, len(seller_ids) // 3), len(seller_ids))
    for sid in (random.sample(seller_ids, n_verify) if seller_ids else []):
        await db.adminactionlogs.insert_one({
            "adminId": admin_id,
            "actionType": "VERIFY_SUPPLIER",
            "targetId": sid,
            "details": {"verified": True},
            "createdAt": now - timedelta(days=random.randint(1, 90)),
        })
    n_recalc = min(160, max(40, len(seller_ids) // 2))
    for _ in range(n_recalc):
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


# Preserved seller@ / buyer@ — two-digit volumes (~30–80) with strong seller-side pipeline (solo-supplier RFQs).
HERO_EXTRA_PRODUCTS = 55
HERO_INQUIRIES = 48
HERO_BUYER_WISHLIST = 42
HERO_BUYER_CART = 36
# RFQs where every line item is from the demo seller → quotes & orders stay on that seller.
HERO_SOLO_RFQS = 72
HERO_QUOTE_CAP = 78
HERO_ORDER_CAP = 54


async def boost_preserved_demo_accounts(db, seller_id, buyer_id, admin_id, category_names, all_buyers):
    now = _now()
    units = ["unit", "kg", "meter", "piece", "tonne", "litre", "box", "set"]
    batch_docs = []
    batch_size = 120
    for i in range(HERO_EXTRA_PRODUCTS):
        cat = random.choice(category_names)
        product_list = CATEGORY_PRODUCTS.get(cat, ["Product"])
        title = (_product_title(cat, product_list) + f" — Hero SKU {i + 1}")[:120]
        price = round(random.uniform(120, 20000), 2)
        min_qty = random.choice([1, 10, 50, 100, 250, 500])
        batch_docs.append({
            "seller": seller_id,
            "title": title,
            "description": f"B2B {title} — stocked for demo.",
            "category": cat,
            "price": price,
            "unit": random.choice(units),
            "minOrderQuantity": min_qty,
            "city": random.choice(INDIAN_CITIES),
            "isActive": True,
            "createdAt": now,
        })
        if len(batch_docs) >= batch_size:
            await db.products.insert_many(batch_docs)
            batch_docs = []
    if batch_docs:
        await db.products.insert_many(batch_docs)

    plist = await db.products.find(
        {},
        {"_id": 1, "seller": 1, "price": 1, "minOrderQuantity": 1, "title": 1, "category": 1},
    ).to_list(15000)
    pmap = {p["_id"]: p for p in plist}
    mine = [p for p in plist if p.get("seller") == seller_id]
    mine_ids = [p["_id"] for p in mine]
    if not mine_ids:
        print("  (hero boost skipped: no products for demo seller)")
        return

    all_pids = [p["_id"] for p in plist]

    for _ in range(HERO_INQUIRIES):
        buyer = buyer_id if random.random() < 0.75 else random.choice(all_buyers)
        pid = random.choice(mine_ids)
        await db.inquiries.insert_one({
            "buyer": buyer,
            "product": pid,
            "seller": seller_id,
            "message": random.choice([
                "Requesting bulk quote and lead time.",
                "MOQ and annual pricing?",
                "Sample shipment possible?",
            ]),
            "quantity": random.randint(12, 96),
            "status": random.choices(["pending", "pending", "responded", "closed"], weights=[0.45, 0.25, 0.2, 0.1])[0],
            "createdAt": now - timedelta(days=random.randint(0, 120)),
        })

    wl_pairs = set()
    attempts = 0
    while len(wl_pairs) < HERO_BUYER_WISHLIST and attempts < HERO_BUYER_WISHLIST * 20:
        attempts += 1
        p = random.choice(all_pids)
        if (buyer_id, p) in wl_pairs:
            continue
        wl_pairs.add((buyer_id, p))
        await db.wishlistitems.insert_one({"buyerId": buyer_id, "productId": p, "createdAt": now})

    cart_pairs = set()
    attempts = 0
    while len(cart_pairs) < HERO_BUYER_CART and attempts < HERO_BUYER_CART * 20:
        attempts += 1
        p = random.choice(all_pids)
        if (buyer_id, p) in cart_pairs:
            continue
        cart_pairs.add((buyer_id, p))
        await db.cartitems.insert_one({
            "buyerId": buyer_id,
            "productId": p,
            "quantity": max(1, random.randint(12, 80)),
            "notes": "",
            "createdAt": now,
        })

    # Mix of accepted (orders) + sent/quoted (active pipeline) for both buyer & seller dashboards.
    hero_solo_weights = [0.14, 0.22, 0.52, 0.12]
    hero_rfqs = []
    for _ in range(HERO_SOLO_RFQS):
        cap = min(4, len(mine))
        n_items = random.randint(2, cap) if cap >= 2 else 1
        n_pick = min(n_items, len(mine))
        chosen = random.sample(mine, n_pick) if len(mine) >= n_pick else list(mine)
        if len(chosen) < 1:
            continue
        items = [
            {"productId": p["_id"], "quantity": p.get("minOrderQuantity", 10) + random.randint(0, 40), "notes": ""}
            for p in chosen
        ]
        status = random.choices(RFQ_STATUSES, weights=hero_solo_weights)[0]
        created_at = now - timedelta(days=random.randint(0, 75))
        doc = {
            "buyerId": buyer_id,
            "items": items,
            "status": status,
            "createdAt": created_at,
            "validUntil": created_at + timedelta(days=7),
            "updated_at": now,
        }
        r = await db.rfqs.insert_one(doc)
        hero_rfqs.append({
            "_id": r.inserted_id,
            "buyerId": buyer_id,
            "items": items,
            "status": status,
            "sellers_in_rfq": list({p["seller"] for p in chosen}),
        })

    await create_quotes_and_orders_final(
        db,
        hero_rfqs,
        pmap,
        quote_cap=HERO_QUOTE_CAP,
        order_cap=HERO_ORDER_CAP,
        run_order_backfill=False,
        quote_accept_if_rfq_accepted=0.9,
        quote_accept_if_rfq_quoted=0.48,
        order_if_quote_accepted=0.93,
    )

    # Deterministic top-up: random order sampling often undershoots — pair remaining accepted quotes with orders.
    hero_rfq_ids = [r["_id"] for r in hero_rfqs]
    have = await db.orders.count_documents({"sellerId": seller_id})
    need_orders = max(0, HERO_ORDER_CAP - have)
    if need_orders > 0 and hero_rfq_ids:
        async for qd in db.quotes.find(
            {"sellerId": seller_id, "status": "accepted", "rfqId": {"$in": hero_rfq_ids}},
            sort=[("createdAt", 1)],
        ):
            if need_orders <= 0:
                break
            if await db.orders.find_one({"quoteId": qd["_id"]}):
                continue
            rfq_doc = await db.rfqs.find_one({"_id": qd["rfqId"]})
            if not rfq_doc:
                continue
            q_items = qd.get("items") or []
            if not q_items:
                continue
            total = sum(it["unitPrice"] * it["availableQty"] for it in q_items)
            o_items = [{"productId": it["productId"], "quantity": it["availableQty"], "agreedUnitPrice": it["unitPrice"]} for it in q_items]
            await db.orders.insert_one({
                "rfqId": qd["rfqId"],
                "quoteId": qd["_id"],
                "buyerId": rfq_doc["buyerId"],
                "sellerId": seller_id,
                "items": o_items,
                "totalAmount": round(total, 2),
                "status": next_demo_order_status_for_seller(seller_id),
                "createdAt": now - timedelta(days=random.randint(0, 22)),
                "paymentStatus": random.choice(
                    ["payment_pending", "escrow_held", "released", "payment_pending", "escrow_held", "refunded"]
                ),
            })
            need_orders -= 1

    await db.adminactionlogs.insert_one({
        "adminId": admin_id,
        "actionType": "USER_CREATED",
        "targetId": str(seller_id),
        "details": {"message": "Hero demo accounts boost applied"},
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
    reset_order_status_sequence()

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
    n_quotes, n_orders = await create_quotes_and_orders_final(db, rfqs, all_products_map)

    print("10. Creating supplier scores...")
    await create_supplier_scores(db, all_sellers)

    print("11. Creating admin logs...")
    await create_admin_logs(db, admin_id, all_sellers)

    print("12. Creating workflow events and notifications...")
    await create_workflow_events_and_notifications(db, rfqs, admin_id, all_sellers, all_buyers)

    print("13. Boosting preserved demo seller/buyer (seller@ / buyer@) activity...")
    await boost_preserved_demo_accounts(db, seller_id, buyer_id, admin_id, category_names, all_buyers)
    await create_supplier_scores(db, [seller_id])

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
        ("workflow_events", db.workflow_events),
        ("notifications", db.notifications),
    ]:
        c = await coll.count_documents({})
        print(f"  {name}: {c}")
    print("\nPreserved credentials: admin@smartb2b.com / Admin@123, seller@example.com / Seller@123, buyer@example.com / Buyer@123")
    print("Demo users (sellers/buyers): password Demo@123")
    client.close()


if __name__ == "__main__":
    asyncio.run(run())
