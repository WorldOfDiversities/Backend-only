# API v1 Reference

Base URL:

- http://127.0.0.1:8000/api/v1/

Authentication:

- JWT Bearer token in Authorization header.
- Header format: Authorization: Bearer <access_token>

## Auth Endpoints

- POST auth/register/
- POST auth/token/
- POST auth/token/refresh/

Registration request body example:

```json
{
  "username": "cashier1",
  "email": "cashier1@example.com",
  "first_name": "Cash",
  "last_name": "User",
  "role": "CASHIER",
  "password": "StrongPass123",
  "confirm_password": "StrongPass123"
}
```

Registration response example:

```json
{
  "id": 21,
  "username": "cashier1",
  "email": "cashier1@example.com",
  "role": "CASHIER"
}
```

Token request body example:

```json
{
  "username": "admin",
  "password": "Admin@12345"
}
```

Token response example:

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

## Core Resource Endpoints

Accounts:

- GET, POST auth/profiles/
- GET, PUT, PATCH, DELETE auth/profiles/{id}/

Products:

- GET, POST products/categories/
- GET, PUT, PATCH, DELETE products/categories/{id}/
- GET, POST products/suppliers/
- GET, PUT, PATCH, DELETE products/suppliers/{id}/
- GET, POST products/items/
- GET, PUT, PATCH, DELETE products/items/{id}/

Inventory:

- GET, POST inventory/movements/
- GET, PUT, PATCH, DELETE inventory/movements/{id}/
- GET, POST inventory/alerts/
- GET, PUT, PATCH, DELETE inventory/alerts/{id}/

Customers:

- GET, POST customers/
- GET, PUT, PATCH, DELETE customers/{id}/

Sales:

- GET, POST sales/
- GET, PUT, PATCH, DELETE sales/{id}/
- POST sales/checkout/
- GET, POST sales/items/
- GET, PUT, PATCH, DELETE sales/items/{id}/

Payments:

- GET, POST payments/
- GET, PUT, PATCH, DELETE payments/{id}/

Receipts:

- GET, POST receipts/
- GET, PUT, PATCH, DELETE receipts/{id}/

Audit Logs:

- GET, POST auditlog/
- GET, PUT, PATCH, DELETE auditlog/{id}/

## Reporting Endpoints (7.1)

- GET reports/sales/daily/
- GET reports/sales/weekly/
- GET reports/products/performance/
- GET reports/inventory/summary/

### Daily Sales Report

Path:

- GET reports/sales/daily/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

Defaults:

- If no dates are provided, returns last 7 days.

Response shape:

```json
{
  "start_date": "2026-03-19",
  "end_date": "2026-03-25",
  "daily": [
    {
      "report_date": "2026-03-25",
      "sales_count": 4,
      "gross_total": "180.50"
    }
  ],
  "payment_breakdown": [
    {
      "method": "CASH",
      "total": "120.00",
      "payments": 3
    },
    {
      "method": "CARD",
      "total": "60.50",
      "payments": 1
    }
  ]
}
```

### Weekly Sales Report

Path:

- GET reports/sales/weekly/?weeks=8

Defaults and limits:

- Default weeks: 8
- Min: 1
- Max: 52

Response shape:

```json
{
  "weeks": 8,
  "start_date": "2026-01-29",
  "end_date": "2026-03-25",
  "weekly": [
    {
      "week_start": "2026-03-23",
      "sales_count": 24,
      "gross_total": "1680.00"
    }
  ]
}
```

### Product Performance Report

Path:

- GET reports/products/performance/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&limit=10

Defaults and limits:

- Date range default: last 30 days
- Limit default: 10
- Limit min: 1
- Limit max: 100

Response shape:

```json
{
  "start_date": "2026-02-25",
  "end_date": "2026-03-25",
  "limit": 10,
  "top_products": [
    {
      "product__id": 12,
      "product__name": "Bottled Water",
      "product__sku": "SKU-AB12CD34",
      "product__category__name": "Drinks",
      "units_sold": 240,
      "revenue": "480.00",
      "sale_lines": 72
    }
  ]
}
```

### Inventory Summary Report

Path:

- GET reports/inventory/summary/

Response shape:

```json
{
  "summary": {
    "total_products": 45,
    "active_products": 42,
    "total_units": 1240
  },
  "low_stock": [
    {
      "id": 7,
      "name": "Low Stock Cola",
      "sku": "SKU-1234ABCD",
      "quantity": 2,
      "low_stock_threshold": 5
    }
  ]
}
```

## Checkout Endpoint Example

Path:

- POST sales/checkout/

Request body:

```json
{
  "customer_id": 1,
  "items": [
    { "product_id": 3, "quantity": 2 },
    { "product_id": 9, "quantity": 1 }
  ],
  "payment_method": "CASH",
  "payment_reference": "",
  "discount_amount": "1.00",
  "tax_amount": "0.50",
  "notes": "Counter checkout"
}
```

Successful response:

```json
{
  "sale_id": 15,
  "sale_number": "SAL-2D3E4F5A6B",
  "subtotal": "21.00",
  "total_amount": "20.50",
  "payment_id": 15,
  "receipt_id": 15
}
```

## Common Query Parameters

List endpoints commonly support:

- search=<text>
- ordering=<field>
- filter fields specific to each resource

Example:

- GET products/categories/?search=snack
- GET products/categories/?ordering=name

## Error Format

Validation and business-rule errors are returned as JSON.

Examples:

```json
{
  "detail": "Insufficient stock for product SKU-1234ABCD"
}
```

```json
{
  "items": [
    {
      "quantity": ["Ensure this value is greater than or equal to 1."]
    }
  ]
}
```
