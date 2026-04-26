"""
Seed script.

Default: full marketplace demo (scripts.generate_demo_data — large dataset, clears non-preserved data).
Minimal legacy seed: set SEED_MINIMAL=1

Run: python -m scripts.seed (ensure MONGODB_URI is set and DB is running)
"""
import asyncio
import os
import re
from bson import ObjectId

from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/smartb2b")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _db_name():
    path = urlparse(MONGODB_URI).path
    name = (path or "/").strip("/").split("/")[0].split("?")[0]
    return name or "smartb2b"


def slug(s):
    return re.sub(r"[^a-z0-9-]", "", s.lower().replace(" ", "-"))


async def seed():
    if os.getenv("SEED_MINIMAL", "").lower() not in ("1", "true", "yes"):
        from scripts.generate_demo_data import run as run_bulk_demo

        await run_bulk_demo()
        return

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[_db_name()]
    print("Connected to MongoDB (SEED_MINIMAL mode)")

    admin_email = "admin@smartb2b.com"
    admin_password = "Admin@123"

    admin = await db.users.find_one({"email": admin_email})
    if not admin:
        admin_doc = {
            "email": admin_email,
            "password": pwd_context.hash(admin_password),
            "role": "admin",
            "name": "Admin User",
            "isBanned": False,
            "isVerifiedSupplier": False,
        }
        r = await db.users.insert_one(admin_doc)
        admin = await db.users.find_one({"_id": r.inserted_id})
        print("Created admin:", admin_email)
    else:
        print("Admin already exists:", admin_email)

    category_names = ["Industrial", "Textiles", "Electronics", "Agriculture", "Chemicals", "Machinery"]
    for name in category_names:
        await db.categories.update_one(
            {"slug": slug(name)},
            {"$set": {"name": name, "slug": slug(name), "isActive": True}},
            upsert=True,
        )
    print("Categories upserted")

    seller1 = await db.users.find_one({"email": "seller@example.com"})
    if not seller1:
        r = await db.users.insert_one({
            "email": "seller@example.com",
            "password": pwd_context.hash("Seller@123"),
            "role": "seller",
            "name": "Demo Seller",
            "isBanned": False,
            "isVerifiedSupplier": True,
        })
        seller1 = await db.users.find_one({"_id": r.inserted_id})
        print("Created seller 1:", seller1["email"])
        await db.companyprofiles.update_one(
            {"user": seller1["_id"]},
            {"$set": {"user": seller1["_id"], "companyName": "ABC Traders Pvt Ltd", "description": "Wholesale supplier of industrial goods", "city": "Mumbai", "state": "Maharashtra", "country": "India", "phone": "+91 9876543210"}},
            upsert=True,
        )

    seller2 = await db.users.find_one({"email": "seller2@example.com"})
    if not seller2:
        r = await db.users.insert_one({
            "email": "seller2@example.com",
            "password": pwd_context.hash("Seller2@123"),
            "role": "seller",
            "name": "Second Seller",
            "isBanned": False,
            "isVerifiedSupplier": False,
        })
        seller2 = await db.users.find_one({"_id": r.inserted_id})
        print("Created seller 2:", seller2["email"])
        await db.companyprofiles.update_one(
            {"user": seller2["_id"]},
            {"$set": {"user": seller2["_id"], "companyName": "XYZ Supplies", "city": "Pune", "country": "India"}},
            upsert=True,
        )

    products1 = await db.products.find({"seller": seller1["_id"]}).to_list(10)
    if not products1 and seller1:
        await db.products.insert_many([
            {"seller": seller1["_id"], "title": "Industrial Steel Pipes", "description": "High-grade steel pipes", "category": "Industrial", "price": 450, "unit": "meter", "minOrderQuantity": 100, "city": "Mumbai", "isActive": True},
            {"seller": seller1["_id"], "title": "Cotton Raw Material", "description": "Bulk cotton", "category": "Textiles", "price": 120, "unit": "kg", "minOrderQuantity": 500, "city": "Mumbai", "isActive": True},
            {"seller": seller1["_id"], "title": "Electronic Components Kit", "description": "Assorted components", "category": "Electronics", "price": 2500, "unit": "kit", "minOrderQuantity": 10, "city": "Pune", "isActive": True},
        ])
        print("Created 3 products for seller 1")

    products2 = await db.products.find({"seller": seller2["_id"]}).to_list(10)
    if not products2 and seller2:
        await db.products.insert_many([
            {"seller": seller2["_id"], "title": "Steel Beams", "description": "Construction steel", "category": "Industrial", "price": 380, "unit": "meter", "minOrderQuantity": 50, "city": "Pune", "isActive": True},
            {"seller": seller2["_id"], "title": "Cotton Yarn", "description": "Spun cotton yarn", "category": "Textiles", "price": 95, "unit": "kg", "minOrderQuantity": 200, "city": "Pune", "isActive": True},
        ])
        print("Created 2 products for seller 2")

    buyer1 = await db.users.find_one({"email": "buyer@example.com"})
    if not buyer1:
        r = await db.users.insert_one({"email": "buyer@example.com", "password": pwd_context.hash("Buyer@123"), "role": "buyer", "name": "Demo Buyer", "isBanned": False, "isVerifiedSupplier": False})
        buyer1 = await db.users.find_one({"_id": r.inserted_id})
        print("Created buyer 1:", buyer1["email"])

    buyer2 = await db.users.find_one({"email": "buyer2@example.com"})
    if not buyer2:
        r = await db.users.insert_one({"email": "buyer2@example.com", "password": pwd_context.hash("Buyer2@123"), "role": "buyer", "name": "Second Buyer", "isBanned": False, "isVerifiedSupplier": False})
        buyer2 = await db.users.find_one({"_id": r.inserted_id})
        print("Created buyer 2:", buyer2["email"])

    all_products = await db.products.find().limit(5).to_list(5)

    # Wishlist: buyer1 has one product in wishlist
    if buyer1 and all_products:
        p0 = all_products[0]
        await db.wishlistitems.update_one(
            {"buyerId": buyer1["_id"], "productId": p0["_id"]},
            {"$set": {"buyerId": buyer1["_id"], "productId": p0["_id"]}},
            upsert=True,
        )
        print("Wishlist item added for buyer1")
    # Cart: buyer2 has one cart item
    if buyer2 and all_products and len(all_products) > 1:
        p1 = all_products[1]
        await db.cartitems.update_one(
            {"buyerId": buyer2["_id"], "productId": p1["_id"]},
            {"$set": {"buyerId": buyer2["_id"], "productId": p1["_id"], "quantity": 50, "notes": "Sample cart note"}},
            upsert=True,
        )
        print("Cart item added for buyer2")

    # Supplier scores — weighted formula (see app.services.supplier_score)
    from app.services.supplier_score import recalculate_supplier_score

    for s in [seller1, seller2]:
        if s:
            await recalculate_supplier_score(s["_id"])
    print("Supplier scores recalculated")

    if all_products and buyer1:
        rfq_exists = await db.rfqs.find_one({"buyerId": buyer1["_id"]})
        if not rfq_exists:
            p1 = all_products[0]
            now_seed = datetime.datetime.utcnow()
            rfq_doc = {
                "buyerId": buyer1["_id"],
                "items": [{"productId": p1["_id"], "quantity": p1.get("minOrderQuantity") or 10, "notes": "Urgent requirement"}],
                "status": "quoted",
                "createdAt": now_seed,
                "validUntil": now_seed + datetime.timedelta(days=7),
            }
            r_rfq = await db.rfqs.insert_one(rfq_doc)
            rfq = await db.rfqs.find_one({"_id": r_rfq.inserted_id})
            quote_doc = {
                "rfqId": rfq["_id"],
                "sellerId": p1["seller"],
                "items": [{"productId": p1["_id"], "unitPrice": p1["price"], "availableQty": p1.get("minOrderQuantity") or 10, "deliveryDays": 7}],
                "message": "We can supply at listed price.",
                "status": "accepted",
                "createdAt": now_seed,
                "quoteValidUntil": now_seed + datetime.timedelta(days=5),
            }
            r_quote = await db.quotes.insert_one(quote_doc)
            quote = await db.quotes.find_one({"_id": r_quote.inserted_id})
            total = sum(it["unitPrice"] * it["availableQty"] for it in quote["items"])
            await db.orders.insert_one({
                "rfqId": rfq["_id"], "quoteId": quote["_id"], "buyerId": buyer1["_id"], "sellerId": p1["seller"],
                "items": [{"productId": p1["_id"], "quantity": quote["items"][0]["availableQty"], "agreedUnitPrice": p1["price"]}],
                "totalAmount": total, "status": "confirmed",
                "createdAt": now_seed,
            })
            await db.rfqs.update_one({"_id": rfq["_id"]}, {"$set": {"status": "accepted"}})
            await db.messagethreads.insert_one({
                "rfqId": rfq["_id"], "participants": [buyer1["_id"], p1["seller"]],
                "messages": [{"senderId": buyer1["_id"], "text": "When can you deliver?"}, {"senderId": p1["seller"], "text": "Within 7 days."}],
            })
            print("Created sample RFQ, Quote, Order and thread")

    print("\n--- Seed complete ---")
    print("Admin:  admin@smartb2b.com / Admin@123")
    print("Seller: seller@example.com / Seller@123")
    print("Seller2: seller2@example.com / Seller2@123")
    print("Buyer:  buyer@example.com / Buyer@123")
    print("Buyer2: buyer2@example.com / Buyer2@123")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
