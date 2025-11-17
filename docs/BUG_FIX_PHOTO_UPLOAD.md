# Bug Fix: Property Photo Upload 500 Error

**Date:** 2025-11-15
**Status:** ✅ FIXED
**Severity:** Critical (blocking photo uploads)

---

## Problem Description

When attempting to upload photos through the mobile app's EditProperty screen, the update was failing with a **500 Server Error**:

```
Failed to update property: Error: Server error. Please try again later.
```

The error occurred during the property update step, **before** the photo upload step.

---

## Root Cause Analysis

### Error Details

The full backend error was:

```
MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
Was IO attempted in an unexpected place?

Error extracting attribute: photos
```

### Technical Explanation

The `update_property` endpoint in `backend/app/api/v1/endpoints/properties.py` was returning a `PropertyResponse` object that includes a `photos` field (added when we integrated Cloudinary).

**The Issue:**
- When Pydantic validated the `PropertyResponse`, it tried to access the `property.photos` relationship
- This relationship was **not eagerly loaded** with `selectinload()`
- SQLAlchemy attempted to **lazy load** the relationship in an async context
- This caused the `MissingGreenlet` error because lazy loading isn't allowed in async contexts after a database session operation

**Why other endpoints worked:**
- `GET /properties` - Already had `selectinload(Property.photos)` ✓
- `GET /properties/{id}` - Already had `selectinload(Property.photos)` ✓
- `PUT /properties/{id}` - **Missing** `selectinload(Property.photos)` ❌

---

## The Fix

### Code Change

**File:** `backend/app/api/v1/endpoints/properties.py`
**Function:** `update_property`
**Lines:** 205-213

**Before:**
```python
try:
    # Get property
    query = select(Property).where(
        Property.id == property_id,
        Property.deleted_at.is_(None)
    )
    result = await db.execute(query)
    property = result.scalar_one_or_none()
```

**After:**
```python
try:
    # Get property with photos eager loaded
    query = select(Property).options(
        selectinload(Property.photos)
    ).where(
        Property.id == property_id,
        Property.deleted_at.is_(None)
    )
    result = await db.execute(query)
    property = result.scalar_one_or_none()
```

### What Changed

Added `.options(selectinload(Property.photos))` to the query to **eagerly load** the `photos` relationship along with the property.

This ensures that when `PropertyResponse.model_validate(property)` is called, the `photos` field is already loaded in memory and doesn't trigger a lazy load.

---

## Verification Tests

### Test 1: Property Update (Before Photo Upload)

**Command:**
```python
requests.put(
    "http://localhost:8000/api/v1/properties/{id}",
    json={"title": "Updated Title", "description": "Updated description"}
)
```

**Result:**
```
Status Code: 200 ✓
Response includes: photos: [] ✓
```

---

### Test 2: Photo Upload

**Command:**
```python
requests.post(
    "http://localhost:8000/api/v1/properties/{id}/photos",
    files={'file': ('test.jpg', img_bytes, 'image/jpeg')},
    params={'is_cover': 'true', 'display_order': '0'}
)
```

**Result:**
```
Status Code: 201 Created ✓
Photo URL: https://res.cloudinary.com/dar5w44sh/image/upload/.../photo-{uuid}.jpg ✓
Thumbnail URL: https://res.cloudinary.com/.../c_fill,h_300,w_400/.../photo-{uuid} ✓
```

---

### Test 3: Get Property with Photos

**Command:**
```python
requests.get("http://localhost:8000/api/v1/properties/{id}")
```

**Result:**
```
Status Code: 200 ✓
photos: [
  {
    "id": "e84edbce-1634-4662-ac61-1042ac66ad38",
    "photo_url": "https://res.cloudinary.com/...",
    "thumbnail_url": "https://res.cloudinary.com/.../c_fill,h_300,w_400/...",
    "is_cover": true,
    "display_order": 0
  }
] ✓
```

---

## Impact Assessment

### Before Fix
- ❌ Property updates failed with 500 error
- ❌ Photo uploads blocked (can't save property)
- ❌ Users couldn't edit properties
- ❌ Mobile app showed generic "Server error"

### After Fix
- ✅ Property updates work correctly
- ✅ Photos upload to Cloudinary successfully
- ✅ Photos returned in property responses
- ✅ Mobile app can edit properties and upload images

---

## Related Code Locations

### Affected Files

1. **`backend/app/api/v1/endpoints/properties.py`** (FIXED)
   - Line 206-213: Added `selectinload(Property.photos)` to update query

2. **`backend/app/schemas/property.py`** (No changes needed)
   - Line 109: `PropertyResponse` includes `photos` field

3. **`backend/app/models/property.py`** (No changes needed)
   - Line 125-129: `Property.photos` relationship definition

4. **`mobile/src/screens/host/EditPropertyScreen.tsx`** (No changes needed)
   - Works correctly once backend fixed

### Similar Code Patterns to Watch

Any endpoint that returns `PropertyResponse` must eagerly load photos:

```python
# Correct pattern
query = select(Property).options(
    selectinload(Property.photos)
).where(...)
```

**Endpoints to verify:**
- ✅ `list_properties` - Already has selectinload
- ✅ `get_property` - Already has selectinload
- ✅ `update_property` - **FIXED** - Now has selectinload
- ✅ `delete_property` - Returns 204, doesn't need it

---

## Prevention Strategies

### Best Practices Going Forward

1. **Always Eager Load Relationships for Response Models**
   - If a response schema includes a relationship field, eager load it
   - Use `selectinload()` for one-to-many relationships
   - Use `joinedload()` for many-to-one relationships

2. **Test Response Validation**
   - When adding fields to response schemas, test all endpoints that return that schema
   - Check for `MissingGreenlet` errors in logs

3. **Code Review Checklist**
   - When adding relationship fields to schemas, verify all endpoints load them
   - Use linting or custom checks to detect missing eager loads

4. **Documentation**
   - Document which relationships must be eager loaded
   - Add comments in code when eager loading is required

---

## Lessons Learned

### Why This Happened

1. We added `photos` field to `PropertyResponse` when implementing Cloudinary
2. We updated `list_properties` and `get_property` with `selectinload`
3. We **forgot** to update `update_property` with `selectinload`
4. The error only appeared when trying to update (not when viewing)

### How to Avoid Similar Issues

1. **When modifying response schemas:**
   - Grep for all uses of that schema: `grep -r "PropertyResponse" backend/`
   - Verify each endpoint eager loads new relationships

2. **Testing:**
   - Test all CRUD operations after schema changes
   - Don't just test the new code, test existing endpoints too

3. **Automated Tests:**
   - Add integration tests that validate all response schemas
   - Test that relationships are accessible without lazy loading errors

---

## Files Changed

### Modified
- `backend/app/api/v1/endpoints/properties.py` - Added selectinload to update endpoint

### Created (for testing)
- `backend/test_update.py` - Property update test script
- `backend/test_photo_upload.py` - Photo upload test script
- `docs/BUG_FIX_PHOTO_UPLOAD.md` - This document

---

## Verification Steps for Users

If you encounter similar issues:

1. **Check backend logs** for `MissingGreenlet` errors
2. **Identify the endpoint** that's failing (look at the request URL)
3. **Check if the endpoint returns a schema with relationships**
4. **Verify the query uses `selectinload()` for those relationships**
5. **Add `selectinload()` if missing**
6. **Test the endpoint again**

---

## Timeline

| Time | Event |
|------|-------|
| 11:13 PM | User reports 500 error during photo upload |
| 11:15 PM | Screenshot shows "Failed to update property" error |
| 11:16 PM | Analyzed backend logs, found `MissingGreenlet` error |
| 11:18 PM | Identified missing `selectinload` in `update_property` |
| 11:19 PM | Applied fix, tested property update |
| 11:20 PM | Verified photo upload works |
| 11:23 PM | Confirmed property GET includes photos |
| 11:25 PM | Documented fix |

**Total Resolution Time:** ~12 minutes

---

## Status

✅ **RESOLVED**

- Property updates work correctly
- Photo uploads to Cloudinary succeed
- Mobile app can now upload property photos
- All tests passing

---

## Next Steps

### Immediate
- [x] Test mobile app photo upload flow
- [x] Verify photos appear in property listings
- [x] Check Cloudinary dashboard for uploaded images

### Short-term
- [ ] Add integration tests for all property endpoints
- [ ] Add automated check for missing eager loads
- [ ] Document relationship loading patterns

### Long-term
- [ ] Implement comprehensive test suite
- [ ] Add performance monitoring for relationship loading
- [ ] Consider using GraphQL to automatically handle eager loading

---

**Date:** 2025-11-15
**Status:** ✅ Complete
