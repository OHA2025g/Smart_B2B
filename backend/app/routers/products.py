import re
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.supplier_score import get_supplier_score_for_response

router = APIRouter()


async def _enrich_seller_with_score(seller_doc: dict, seller_oid) -> dict:
    if not seller_doc:
        return None
    out = serialize_doc(seller_doc)
    if not out:
        return None
    score = await get_supplier_score_for_response(seller_oid)
    if score:
        out["trustScore"] = score.get("total_score", 0)
        out["trustLevel"] = score.get("trust_level", "Low Trust")
    out["isVerifiedSupplier"] = bool(seller_doc.get("isVerifiedSupplier"))
    return out


@router.get("")
async def list_products(
    search: str | None = Query(None),
    category: str | None = Query(None),
    city: str | None = Query(None),
    verified_only: bool | None = Query(None, description="Only products from verified suppliers"),
    trust_level: str | None = Query(None, description="Filter by supplier trust level label"),
    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
):
    db = get_db()
    filter_q: dict = {"isActive": True}
    if category:
        filter_q["category"] = re.compile(re.escape(category), re.I)
    if city:
        filter_q["city"] = re.compile(re.escape(city), re.I)
    if search:
        filter_q["$or"] = [{"title": re.compile(re.escape(search), re.I)}, {"description": re.compile(re.escape(search), re.I)}, {"category": re.compile(re.escape(search), re.I)}]
    price_rng = {}
    if min_price is not None:
        price_rng["$gte"] = min_price
    if max_price is not None:
        price_rng["$lte"] = max_price
    if price_rng:
        filter_q["price"] = price_rng
    if verified_only:
        verified_ids = await db.users.find({"role": "seller", "isVerifiedSupplier": True}, {"_id": 1}).to_list(None)
        filter_q["seller"] = {"$in": [x["_id"] for x in verified_ids]}
    cursor = db.products.find(filter_q).sort("createdAt", -1)
    products = []
    async for p in cursor:
        seller = await db.users.find_one({"_id": p["seller"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if p.get("seller") else None
        doc = serialize_doc(p)
        if doc:
            doc["seller"] = await _enrich_seller_with_score(seller, p["seller"]) if seller else None
            if trust_level and doc.get("seller"):
                tl = (doc["seller"].get("trustLevel") or "").lower()
                if trust_level.lower() not in tl.lower():
                    continue
        products.append(doc)
    return success_response(data={"products": products})


@router.get("/seller/me")
async def list_my(request: Request, user: dict = Depends(require_roles("seller"))):
    db = get_db()
    cursor = db.products.find({"seller": ObjectId(user["id"])}).sort("createdAt", -1)
    products = [serialize_doc(p) async for p in cursor]
    return success_response(data={"products": products})


@router.get("/{id}")
async def get_by_id(id: str, request: Request):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid product ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    product = await db.products.find_one({"_id": oid})
    if not product:
        raise HTTPException(status_code=404, detail=error_response("Product not found.", "NOT_FOUND", path=str(request.url.path)))
    seller = await db.users.find_one({"_id": product["seller"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if product.get("seller") else None
    doc = serialize_doc(product)
    if doc:
        doc["seller"] = await _enrich_seller_with_score(seller, product["seller"]) if seller else None
    return success_response(data={"product": doc})


@router.post("", status_code=201)
async def create(request: Request, body: ProductCreate, user: dict = Depends(require_roles("seller"))):
    db = get_db()
    doc = dict(body.model_dump())
    doc["seller"] = ObjectId(user["id"])
    doc["isActive"] = True
    r = await db.products.insert_one(doc)
    doc["_id"] = r.inserted_id
    return success_response(data={"product": serialize_doc(doc)})


@router.put("/{id}")
async def update(id: str, request: Request, body: ProductUpdate, user: dict = Depends(require_roles("seller"))):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid product ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    product = await db.products.find_one({"_id": oid})
    if not product:
        raise HTTPException(status_code=404, detail=error_response("Product not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(product["seller"]) != user["id"]:
        raise HTTPException(status_code=403, detail=error_response("Not authorized to update this product.", "FORBIDDEN", path=str(request.url.path)))
    await db.products.update_one({"_id": oid}, {"$set": body.model_dump(exclude_unset=True)})
    updated = await db.products.find_one({"_id": oid})
    return success_response(data={"product": serialize_doc(updated)})


@router.delete("/{id}")
async def remove(id: str, request: Request, user: dict = Depends(require_roles("seller"))):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid product ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    product = await db.products.find_one({"_id": oid})
    if not product:
        raise HTTPException(status_code=404, detail=error_response("Product not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(product["seller"]) != user["id"]:
        raise HTTPException(status_code=403, detail=error_response("Not authorized to delete this product.", "FORBIDDEN", path=str(request.url.path)))
    await db.products.delete_one({"_id": oid})
    return success_response(data=None, message="Product deleted.")
