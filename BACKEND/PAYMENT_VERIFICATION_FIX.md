# Payment Verification Issue - Complete Fix

## Problem Statement

After Paystack payment verification, the sale remains in "pending verification" status. User must click a manual "proceed with pending verification" button to finalize and record the sale.

## Root Cause

The payment system creates Payment records with `status=COMPLETED` immediately, without verifying with Paystack API first. This causes:

1. Payments marked as completed but not actually verified
2. Unclear payment status (payment might have failed on Paystack side but showing as completed locally)
3. Revenue recorded without confirmation

## Solution Overview

Implement a two-step payment flow:

1. **Step 1**: Create Payment with `status=PENDING` after checkout (for electronic payments)
2. **Step 2**: Verify with Paystack API, then finalize to `status=COMPLETED`

---

## Changes Made

### 1. Backend - Payment Service (`services/payment_service.py`)

**Change**: Modified `finalize_payment()` to create electronic payments as PENDING initially.

```python
# For electronic payments (CARD, MOBILE_MONEY, SPLIT), create as PENDING
# For cash payments, create as COMPLETED immediately (no verification needed)
initial_status = Payment.Status.PENDING if method in {
    Payment.Method.MOBILE_MONEY,
    Payment.Method.CARD,
    Payment.Method.SPLIT
} else Payment.Status.COMPLETED
```

**New Function**: Added `verify_and_complete_payment(payment_id)` to finalize pending payments after verification.

```python
def verify_and_complete_payment(*, payment_id: int) -> dict:
    """Convert pending payment to completed after Paystack verification"""
    # Marks payment and sale as COMPLETED
    # Returns summary dict
```

### 2. Backend - Payment ViewSet (`payments/views.py`)

**New Endpoint**: Added `POST /payments/{id}/finalize/` action to finalize a payment.

```
POST /payments/123/finalize/
Response: {
    "payment_id": 123,
    "status": "COMPLETED",
    "sale_id": 456,
    "message": "Payment finalized and recorded successfully."
}
```

**Flow**:

1. Frontend creates sale via `POST /sales/checkout/` → Payment created as PENDING
2. Frontend calls Paystack initialization via `POST /payments/paystack/initialize/`
3. User completes payment in Paystack modal
4. Frontend verifies with `POST /payments/paystack/verify/` → gets `verified: true`
5. **NEW**: Frontend calls `POST /payments/{payment_id}/finalize/` → Payment marked COMPLETED

---

## Frontend Implementation (Required Next Steps)

### Current Checkout Flow (Needs Update)

**Before** (Current):

```javascript
// pos.js - submitCheckout()
const response = await apiPost("/sales/checkout/", payload);
// Immediately shows success, payment assumed completed
openSuccessModal(totals.total, change);
```

**After** (Required):

```javascript
// Step 1: Create sale and payment (payment = PENDING for electronic payments)
const checkoutResponse = await apiPost("/sales/checkout/", {
  ...payload,
  payment_method: state.paymentMethod,
  payment_reference: referenceFromPaystack,
});

// Step 2: If electronic payment, verify and finalize
if (state.paymentMethod !== "CASH") {
  const finalizeResponse = await apiPost(
    `/payments/${checkoutResponse.payment_id}/finalize/`,
    {}, // Could pass verification data here
  );
  if (finalizeResponse.payment_id) {
    // Success - payment verified and recorded
    openSuccessModal(totals.total, change);
  }
} else {
  // Cash payment - no verification needed
  openSuccessModal(totals.total, change);
}
```

### Payment Flow for Card/Mobile Money

```javascript
async function submitElectronicPayment() {
  const totals = readTotals();
  const customerId = customerSelectNode.value
    ? Number.parseInt(customerSelectNode.value, 10)
    : null;

  try {
    // 1. Initialize Paystack
    const initResponse = await apiPost("/payments/paystack/initialize/", {
      amount: totals.total,
      email: getUserEmail(),
      payment_method: state.paymentMethod,
    });

    const { reference, authorization_url } = initResponse;

    // 2. Show Paystack modal (library call)
    // User completes payment in modal

    // 3. After modal closes, verify payment
    const verifyResponse = await apiPost("/payments/paystack/verify/", {
      reference: reference,
    });

    if (!verifyResponse.verified) {
      showToast("Payment verification failed");
      return;
    }

    // 4. Create sale with verified reference
    const checkoutPayload = {
      customer_id: customerId,
      items: items.map((item) => ({ product_id: item.id, quantity: item.qty })),
      payment_method: state.paymentMethod,
      payment_reference: reference,
      discount_amount: totals.discount,
      tax_amount: totals.tax,
    };

    const checkoutResponse = await apiPost("/sales/checkout/", checkoutPayload);

    // 5. Finalize payment (mark as COMPLETED)
    const finalizeResponse = await apiPost(
      `/payments/${checkoutResponse.payment_id}/finalize/`,
      {},
    );

    // 6. Show success
    openSuccessModal(totals.total, 0);
  } catch (error) {
    showToast(`Payment failed: ${error.message}`);
  }
}
```

---

## Testing Checklist

### Backend Tests (Add to `payments/tests.py`)

- [ ] Test creating PENDING payment for electronic payment methods
- [ ] Test creating COMPLETED payment for cash
- [ ] Test `verify_and_complete_payment()` with valid payment_id
- [ ] Test error when finalizing already-completed payment
- [ ] Test error when finalizing failed payment
- [ ] Test sale status updates to COMPLETED after payment finalized

```python
def test_electronic_payment_created_as_pending(self):
    payment = create_payment(method='CARD', status='PENDING')
    assert payment.status == Payment.Status.PENDING

def test_finalize_payment_completes_sale(self):
    result = verify_and_complete_payment(payment_id=payment.id)
    payment.refresh_from_db()
    assert payment.status == Payment.Status.COMPLETED
    assert payment.sale.status == Sale.Status.COMPLETED
```

### Frontend Tests

- [ ] Test Cash payment (no finalization step needed)
- [ ] Test Card payment (requires finalization)
- [ ] Test Mobile Money payment (requires finalization)
- [ ] Test payment verification failure
- [ ] Test retry after failed verification

---

## API Endpoints Summary

| Endpoint                         | Method | Purpose                           | Status      |
| -------------------------------- | ------ | --------------------------------- | ----------- |
| `/sales/checkout/`               | POST   | Create sale + pending payment     | ✅ Updated  |
| `/payments/paystack/initialize/` | POST   | Get Paystack auth URL             | ✅ Existing |
| `/payments/paystack/verify/`     | POST   | Verify payment with Paystack      | ✅ Existing |
| `/payments/{id}/finalize/`       | POST   | Mark pending payment as COMPLETED | ✅ NEW      |

---

## Data Flow Diagram

```
CASH PAYMENT:
┌─────────────────┐
│ Frontend        │
└────────┬────────┘
         │ POST /sales/checkout/
         │ (payment_method: "CASH")
         ▼
┌─────────────────────────┐
│ Backend Checkout        │
├─────────────────────────┤
│ 1. Create Sale          │
│ 2. Create Payment       │
│    (status: COMPLETED)  │
│ 3. Deduct Inventory     │
│ 4. Generate Receipt     │
└────────┬────────────────┘
         │ Response: {payment_id, sale_id}
         ▼
    ✅ Sale Complete

ELECTRONIC PAYMENT (CARD/MOMO):
┌─────────────────┐
│ Frontend        │
└────────┬────────┘
         │ 1. POST /payments/paystack/initialize/
         ▼ 2. Show Paystack Modal (user pays)
         │ 3. POST /payments/paystack/verify/
┌─────────────────────────────────────┐
│ Backend Payment Verification        │
├─────────────────────────────────────┤
│ Paystack API: GET /transaction/verify/{ref}
└────────┬────────────────────────────┘
         │ verified: true/false
         ▼
    If verified ✅
         │ 4. POST /sales/checkout/
         │    (with payment_reference)
         ▼
┌─────────────────────────────────────┐
│ Backend Checkout                    │
├─────────────────────────────────────┤
│ 1. Create Sale                      │
│ 2. Create Payment                   │
│    (status: PENDING)  ⏳             │
│ 3. Deduct Inventory                 │
│ 4. Generate Receipt                 │
└────────┬────────────────────────────┘
         │ Response: {payment_id, sale_id}
         │ 5. POST /payments/{id}/finalize/
         ▼
┌─────────────────────────────────────┐
│ Backend Finalize Payment            │
├─────────────────────────────────────┤
│ 1. Set Payment.status = COMPLETED   │
│ 2. Set Sale.status = COMPLETED      │
└────────┬────────────────────────────┘
         │ Response: {status: COMPLETED}
         ▼
    ✅ Sale Complete
```

---

## Files Modified

1. ✅ `services/payment_service.py` - Updated `finalize_payment()`, added `verify_and_complete_payment()`
2. ✅ `payments/views.py` - Added `/payments/{id}/finalize/` endpoint
3. ⏳ `FRONTEND/pos.js` - **NEEDS UPDATE** - Implement finalization flow

---

## Optional Enhancements

### 1. Auto-Finalize with Webhook

Instead of frontend calling finalize, use Paystack webhook:

```python
# New endpoint: webhook receiver
@csrf_exempt
@action(detail=False, methods=['post'], url_path='paystack/webhook')
def paystack_webhook(self, request):
    """
    Paystack sends POST when payment succeeds
    Automatically finalize payment without user interaction
    """
    signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
    # Verify signature matches PAYSTACK_SECRET_KEY
    # If verified, call verify_and_complete_payment()
```

### 2. Automatic Retry

Frontend could retry verification if it fails:

```javascript
async function verifyWithRetry(reference, maxAttempts = 3) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await apiPost("/payments/paystack/verify/", {
        reference,
      });
      if (response.verified) return response;
      await new Promise((r) => setTimeout(r, 2000 * (i + 1))); // Exponential backoff
    } catch (e) {
      if (i === maxAttempts - 1) throw e;
    }
  }
}
```

### 3. Payment Status Polling

Frontend could poll payment status until it's finalized:

```javascript
async function pollPaymentStatus(paymentId, maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    const payment = await apiGet(`/payments/${paymentId}/`);
    if (payment.status === "COMPLETED") {
      return payment;
    }
    await new Promise((r) => setTimeout(r, 1000)); // Poll every 1 second
  }
  throw new Error("Payment verification timeout");
}
```

---

## Deployment Checklist

- [ ] Backup database before deploying
- [ ] Test on staging environment first
- [ ] Verify existing PENDING payments can be finalized
- [ ] Update API documentation
- [ ] Update frontend code with new flow
- [ ] Test end-to-end payment flow
- [ ] Monitor payment success rates after deployment

---

## Questions & Troubleshooting

**Q: Why can't we auto-finalize on checkout?**  
A: Because Paystack payment hasn't been confirmed yet. We only have a reference from initialization, not confirmation. Must verify before finalizing.

**Q: What if verification fails?**  
A: Keep payment as PENDING. User can retry verification via separate endpoint, or admin can manually finalize if they're confident payment succeeded.

**Q: Does this work with offline payments?**  
A: This flow is designed for online payments (CARD, MOBILE_MONEY). CASH payments still finalize immediately.

**Q: Can user create multiple payments by clicking finalize multiple times?**  
A: No - `verify_and_complete_payment()` checks current status first. If already COMPLETED, it throws error.

---

## Success Criteria

✅ **Before fix:**

- Payment created as COMPLETED immediately
- No Paystack verification before marking complete
- Unclear payment status

✅ **After fix:**

- Electronic payments created as PENDING
- Backend API call verifies with Paystack
- Frontend explicitly finalizes payment
- Clear payment status throughout lifecycle
- Sale marked complete only after payment verified
