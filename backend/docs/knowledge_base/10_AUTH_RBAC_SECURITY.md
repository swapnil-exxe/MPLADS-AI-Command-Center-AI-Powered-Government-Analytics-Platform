# 10. Authentication, RBAC & Security Architecture

## Authentication, RBAC & Security Architecture

### Cryptographic Security Stack
- **JWT Standard**: HMAC-SHA256 (`HS256`) signed tokens with 60-minute expiration.
- **Password Hashing**: Direct `bcrypt` with 12 rounds cost factor.

### Timing Attack Defense
To prevent username enumeration via response timing, `api/auth/security.py` executes a pre-computed 12-round dummy bcrypt hash check (`DUMMY_BCRYPT_HASH`) when an invalid email is submitted. This ensures uniform ~90ms response times for all login attempts.

---

## Server-Side RBAC & Jurisdictional Scoping

Jurisdictional access control is enforced at the database query level via **predicate injection**:

- **`MINISTRY`**: Unrestricted national scope across all 36 States.
- **`STATE_OFFICER`**: Injects `WHERE works.state = :user_state`.
- **`DISTRICT_OFFICER`**: Injects composite predicate `WHERE works.state = :user_state AND works.district = :user_district` (resolves 75 duplicate district names across India).
- **`MP`**: Injects `WHERE works.mp_name = :user_mp_name`.

---

## IDOR Protection Strategy

- **List Endpoints**: Scoped queries return empty sets (`items: []`) for out-of-jurisdiction filters.
- **Detail Endpoints (`/works/{id}`)**: Returns `404 Not Found` if the work ID does not exist, and `403 Forbidden` if the work ID exists but falls outside the caller's jurisdiction.

