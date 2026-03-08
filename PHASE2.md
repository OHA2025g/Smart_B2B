# SmartB2B Phase 2 – B2B Marketplace Features

## Summary

Phase 2 adds: **Wishlist**, **RFQ Cart**, **RFQ workflow** (create RFQ → sellers submit quotes → buyer accepts → Order created), **per-RFQ messaging**, and **Admin panel** (users, categories, RFQs, orders, activity logs).

Existing Phase 1 endpoints and pages are unchanged.

---

## Backend: New Models

- `Category` – name, slug, icon, isActive
- `WishlistItem` – buyerId, productId
- `CartItem` – buyerId, productId, quantity, notes
- `RFQ` – buyerId, items[], status (draft|sent|quoted|accepted|rejected|closed)
- `Quote` – rfqId, sellerId, items[], message, status
- `MessageThread` – rfqId, participants[], messages[]
- `Order` – rfqId, buyerId, sellerId, items[], totalAmount, status
- `AdminActionLog` – adminId, actionType, targetId, details

User model extended with `isBanned`, `isVerifiedSupplier`.

---

## Backend: New API Routes

| Group | Method | Path | Description |
|-------|--------|------|-------------|
| Categories | GET | /api/categories | List (public) |
| | POST | /api/categories | Create (admin) |
| | PUT | /api/categories/:id | Update (admin) |
| | DELETE | /api/categories/:id | Delete (admin) |
| Wishlist | GET | /api/wishlist | My wishlist (buyer) |
| | POST | /api/wishlist/:productId | Toggle (buyer) |
| | DELETE | /api/wishlist/:productId | Remove (buyer) |
| Cart | GET | /api/cart | My cart (buyer) |
| | POST | /api/cart | Add/update (buyer) |
| | POST | /api/cart/clear | Clear (buyer) |
| | DELETE | /api/cart/:productId | Remove (buyer) |
| RFQ | POST | /api/rfq | Create (buyer) |
| | GET | /api/rfq/me | My RFQs (buyer) |
| | GET | /api/rfq/assigned | Assigned to me (seller) |
| | GET | /api/rfq/:id | By id (buyer/seller/admin) |
| | PUT | /api/rfq/:id/status | Update status (buyer) |
| | GET | /api/rfq/:id/quotes | Quotes for RFQ (buyer) |
| | POST | /api/rfq/:id/quote | Submit quote (seller) |
| | POST | /api/rfq/:id/accept-quote/:quoteId | Accept quote → create Order (buyer) |
| Quote | PUT | /api/quote/:id | Revise (seller) |
| Orders | GET | /api/orders/me | My orders (buyer/seller) |
| | GET | /api/orders/:id | By id |
| | PUT | /api/orders/:id/status | Update status (seller) |
| Messages | GET | /api/messages/:rfqId | Thread (buyer/seller/admin) |
| | POST | /api/messages/:rfqId | Send (buyer/seller) |
| Admin | GET | /api/admin/users | List users |
| | PUT | /api/admin/users/:id/ban | Ban/unban |
| | PUT | /api/admin/users/:id/verify-supplier | Verify supplier |
| | GET | /api/admin/rfqs | List RFQs |
| | GET | /api/admin/orders | List orders |
| | GET | /api/admin/logs | Activity logs |

---

## Frontend: New Pages & Routes

| Route | Role | Page |
|-------|------|------|
| /wishlist | buyer | Wishlist – list, remove, add to cart |
| /cart | buyer | RFQ Cart – quantity, notes, “Request Quotation (RFQ)” |
| /rfq | buyer | My RFQs list |
| /rfq/:id | buyer/seller/admin | RFQ detail, quotes table, accept quote, messages |
| /seller/rfqs | seller | Assigned RFQs, “Submit Quote” modal |
| /seller/orders | seller | Orders, confirm/shipped/delivered |
| /admin/panel | admin | Tabs: Users, Categories, RFQs, Orders, Logs |

**Products page** (existing): category chips from `/api/categories`, wishlist heart (buyer), “Add to RFQ Cart” (buyer).

**Navbar** (by role):

- **Buyer:** Products, Wishlist, Cart, RFQs, Dashboard
- **Seller:** Products, My Products, RFQs, Orders, Company, Dashboard
- **Admin:** Products, Admin Panel, Dashboard

---

## File Tree Changes

**Backend (new/updated):**

- `src/models/` – Category.js, WishlistItem.js, CartItem.js, RFQ.js, Quote.js, MessageThread.js, Order.js, AdminActionLog.js
- `src/models/User.js` – isBanned, isVerifiedSupplier
- `src/controllers/` – categoryController, wishlistController, cartController, rfqController, quoteController, orderController, messageController; adminController extended
- `src/routes/` – categoryRoutes, wishlistRoutes, cartRoutes, rfqRoutes, quoteRoutes, orderRoutes, messageRoutes; adminRoutes extended
- `src/utils/validators.js` – new validators
- `src/utils/adminLog.js` – new
- `src/scripts/seed.js` – categories, 2 sellers, 2 buyers, sample RFQ/Quote/Order/thread
- `src/app.js` – mount new routes
- `src/routes/rootRoutes.js` – route index updated

**Frontend (new/updated):**

- `src/api/client.js` – categoriesApi, wishlistApi, cartApi, rfqApi, quoteApi, ordersApi, messagesApi; adminApi extended
- `src/pages/Wishlist.jsx` – new
- `src/pages/Cart.jsx` – new
- `src/pages/RFQList.jsx` – new
- `src/pages/RFQDetail.jsx` – new
- `src/pages/SellerRFQs.jsx` – new
- `src/pages/SellerOrders.jsx` – new
- `src/pages/AdminPanel.jsx` – new
- `src/pages/Products.jsx` – categories, wishlist, add to cart
- `src/components/Navbar.jsx` – role-based links
- `src/App.jsx` – new routes + ProtectedRoute

---

## Commands to Run

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate   # Windows; on macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed  # categories, users, products, sample RFQ/quote/order
python run.py           # http://localhost:5000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev             # http://localhost:5173
```

---

## Demo Path Checklist

1. **Seed**  
   - `cd backend && python -m scripts.seed`  
   - Logins: admin@smartb2b.com / Admin@123; seller@example.com / Seller@123; buyer@example.com / Buyer@123; seller2@example.com / Seller2@123; buyer2@example.com / Buyer2@123.

2. **Buyer flow**  
   - Login as **buyer@example.com**.  
   - **Products:** use category chips, add to wishlist (heart), “Add to RFQ Cart”.  
   - **Wishlist:** open /wishlist, remove or “Add to cart”.  
   - **Cart:** open /cart, adjust quantity/notes, click “Request Quotation (RFQ)” → redirect to /rfq/:id.  
   - **RFQ detail:** see quotes (if any), “Accept” a quote → order created; send messages in thread.

3. **Seller flow**  
   - Login as **seller@example.com**.  
   - **Seller RFQs:** /seller/rfqs, open “Submit Quote” for an assigned RFQ, submit.  
   - **Seller Orders:** /seller/orders, confirm → mark shipped → mark delivered.

4. **Admin flow**  
   - Login as **admin@smartb2b.com**.  
   - **Admin Panel:** /admin/panel.  
   - **Users:** ban/unban, verify supplier.  
   - **Categories:** add category, delete.  
   - **RFQs / Orders / Logs:** view lists and activity.

5. **Existing Phase 1**  
   - /login, /register, /dashboard, /products, /product/:id, /seller/products, /profile/company, /api/docs, /health still work as before.
