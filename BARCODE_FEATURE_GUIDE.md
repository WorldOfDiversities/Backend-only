# Barcode Feature Implementation Guide

## Overview

The barcode feature allows cashiers to scan product barcodes using any barcode scanner or manually enter barcodes to quickly add products to the POS cart. When a valid barcode is scanned, the product is automatically looked up and added to the cart if in stock.

## Components Implemented

### Backend

1. **API Endpoint**: `GET /products/lookup-barcode/?barcode=<code>`
   - Returns product details when a barcode is found
   - Returns 404 with error message if barcode not found
   - Requires authentication and appropriate permissions

2. **Management Command**: `python manage.py generate_barcodes`
   - Generates unique barcodes for all products without one
   - Format: `PREFIX-SKUPART-RANDOMSEGMENT` (e.g., `POS-SKU1234567-AB12CD`)
   - Can be customized with `--prefix` flag

### Frontend

1. **Barcode Scanner Modal**
   - Dedicated modal dialog opened from "Barcode Scan" button in topbar
   - Real-time search with 300ms debounce for responsiveness
   - Display product info with emoji, name, SKU, and price when found
   - Auto-add to cart functionality
   - Close on overlay click, escape key, or cancel button

2. **JavaScript Functions**
   - `openBarcodeScanner()` - Opens modal and focuses barcode input
   - `closeBarcodeScanner()` - Closes modal and clears state
   - `lookupProductByBarcode(barcode)` - Queries API and displays result
   - `addScannedProduct()` - Adds looked-up product to cart
   - `getEmojiForCategory(category)` - Returns category emoji for display

## Setup Instructions

### 1. Generate Barcodes for Existing Products

```bash
cd c:\Users\kojop\Desktop\POS\BACKEND
pipenv run python manage.py generate_barcodes
```

**Output:**

```
✓ Product Name: POS-SKU1234567-AB12CD
✓ Another Product: POS-SKU7654321-XY98ZW
...
Successfully generated barcodes for 25 products.
```

**To use a custom prefix:**

```bash
pipenv run python manage.py generate_barcodes --prefix MYSTORE
# Generates: MYSTORE-SKU1234567-AB12CD
```

### 2. Verify API Endpoint

Test the barcode lookup endpoint:

```bash
# Using curl or Postman
GET http://localhost:8000/api/v1/products/lookup-barcode/?barcode=POS-SKU1234567-AB12CD
Authorization: Bearer <your_token>
```

**Success Response (200):**

```json
{
  "id": 42,
  "sku": "SKU-1234567",
  "name": "Product Name",
  "barcode": "POS-SKU1234567-AB12CD",
  "price": "29.99",
  "quantity": 50,
  "category_name": "Beverages",
  "is_active": true
}
```

**Not Found Response (404):**

```json
{
  "error": "No product found with barcode: INVALID123"
}
```

### 3. Using the Barcode Scanner in POS

1. Click **"⊡ Barcode Scan"** button in the topbar
2. A modal dialog appears with a text input field
3. Scan the barcode with a physical scanner OR manually type the barcode code
4. Product details appear in real-time as barcode is entered
5. If product is found and in stock:
   - Product info is displayed (emoji, name, SKU, price)
   - Product is automatically added to cart
   - Toast notification confirms addition
   - Modal closes automatically
6. If product not found or out of stock:
   - Error message is shown
   - You can try another barcode

## Barcode Flow Diagram

```
┌─────────────────────────────────┐
│   POS Topbar                    │
│   "⊡ Barcode Scan" Button       │
└──────────────┬──────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Barcode Scanner      │
    │ Modal Dialog         │
    │ ┌──────────────────┐ │
    │ │ Barcode Input    │ │
    │ └──────────────────┘ │
    └──────────┬───────────┘
               │
         (Enter/Scan)
               │
               ▼
    ┌──────────────────────────┐
    │ Lookup Product by        │
    │ Barcode (API)            │
    │ GET /lookup-barcode/?... │
    └──────────┬───────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   Found (200)    Not Found (404)
        │             │
        ▼             ▼
   Show Product   Show Error
   Display Info   Message
        │             │
        ▼             ▼
   Auto-add to    Allow Retry
   Cart (if stock)
        │
        ▼
   Close Modal
   Show Toast
   Ready for next
```

## Product Data Model

The `Product` model in `products/models.py` includes:

```python
barcode = models.CharField(max_length=64, unique=True, null=True, blank=True)
```

**Properties:**

- Unique: Each product can have only one barcode
- Nullable: Products can exist without barcodes
- Max length: 64 characters (supports all standard barcode formats)

## Standard Barcode Formats Supported

- **UPC-A**: 12 digits (e.g., `012345678905`)
- **EAN-13**: 13 digits (e.g., `9780201379624`)
- **Code 128**: Variable length alphanumeric
- **QR Codes**: Can be scanned and contain barcode data
- **Custom format**: Any string up to 64 characters (e.g., `POS-SKU1234567-AB12CD`)

## Barcode Scanner Hardware Integration

Most USB barcode scanners work as HID (Human Interface Device) and emit key presses automatically. The POS barcode input will work with:

- Laser barcode scanners
- 2D barcode scanners
- Mobile barcode scanner apps (with keyboard emulation)
- Manual typing

## Frontend UX Details

### Modal Display

- Title: "Scan Barcode"
- Subtitle: "Scan or enter a product barcode"
- Input placeholder: "Scan or type barcode…"
- Auto-focus on open for quick scanning

### Real-time Feedback

- Debounced lookup (300ms) to avoid excessive API calls
- Instant display of product info when found
- Shows emoji, product name, SKU, and price
- Auto-add happens immediately (no manual "Add" click needed)
- Toast notification confirms addition

### Error Handling

- Invalid/non-existent barcodes show error message
- Out-of-stock products show availability message
- Network errors are caught and shown as toast
- User can retry immediately without closing modal

## API Permissions

The barcode lookup endpoint respects the same permissions as the Product API:

- **Requires**: `IsAdminManagerOrReadOnly` permission
- **Allowed roles**: Admin, Manager, Cashier (with read permission)
- **Auth**: Bearer token in Authorization header

## Troubleshooting

### Barcodes not generating?

```bash
# Check if products exist
pipenv run python manage.py shell
>>> from products.models import Product
>>> Product.objects.filter(barcode__isnull=True).count()
```

### API endpoint returns 404 for valid barcode?

1. Verify barcode exists in product: `Product.objects.get(barcode='...')`
2. Check product is not soft-deleted: `is_deleted=False`
3. Ensure you're using correct authentication token

### Scanner not working?

1. Test with manual typing first to isolate hardware
2. Check browser console for JavaScript errors
3. Verify API endpoint is accessible: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/products/lookup-barcode/?barcode=test`

### Products not auto-adding to cart?

1. Check product quantity in database
2. Verify product `is_active=True`
3. Check browser console for JavaScript errors
4. Ensure `getEmojiForCategory()` is working (map may need updates)

## Future Enhancements

- Add bulk barcode generation/printing
- Implement barcode format validation (UPC, EAN, etc.)
- Add barcode history/scan log
- Support for barcode batches/import
- Mobile-optimized barcode scanner view
- Barcode label printing from products page

## Quick Reference

| Action                      | Command                                                                                                      |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Generate barcodes           | `python manage.py generate_barcodes`                                                                         |
| Generate with custom prefix | `python manage.py generate_barcodes --prefix MYSTORE`                                                        |
| Test API endpoint           | `curl -H "Authorization: Bearer TOKEN" "http://localhost:8000/api/v1/products/lookup-barcode/?barcode=CODE"` |
| Open scanner in POS         | Click "⊡ Barcode Scan" button                                                                                |
| Scan barcode                | Type or scan barcode code into input field                                                                   |
| Auto-add product            | Product added automatically if in stock                                                                      |
| Close scanner               | Press Escape, click X, or click outside modal                                                                |
