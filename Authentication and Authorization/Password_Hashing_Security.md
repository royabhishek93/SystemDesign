# How Passwords Are Stored Securely in Databases (Hashing)

## 1. Basic Security Principle

One very important rule in application security is:

**A user's real password should never be stored in the database.**

For example, suppose a user signs up on a website and enters:

```
Email: shruti@gmail.com
Password: ABC@123
```

The system does **NOT** store `ABC@123` directly in the database.

If the real password were stored and the database got leaked, attackers could immediately see all user passwords. That would be extremely dangerous because users often reuse the same password across many platforms.

To prevent this, applications use a technique called **password hashing**.

## 2. What is Hashing?

Hashing is a process where:

- The original password is converted into a unique fixed-length string of characters.
- This conversion is done using a **hashing algorithm**.

**Example:**

```
ABC@123
```

After hashing it might look like:

```
$2a$10$X7g9QeJxK2M3dJk8VZpGzOf7sRkL3N0wPq9a
```

This output is called a **hash value**.

### Important characteristics of hashing:

#### One-way function

You **cannot** convert the hash back into the original password.

```
Example:
ABC@123 → hash ✔

But you cannot reverse it:
hash → ABC@123 ❌
```

#### Same input produces same hash

If the same password is hashed again with the same algorithm, it produces the same hash (with some algorithms unless salted).

#### Used for security

Because even if the database is leaked, attackers only see hashes, not real passwords.

## 3. Visual Overview — The Problem Without Hashing

```
┌─────────────────────────────────────────────────────────────┐
│                    ❌ INSECURE WAY (Never Do This)          │
└─────────────────────────────────────────────────────────────┘

User Signup
┌──────────────┐
│ Email:       │
│ shruti@      │
│ gmail.com    │
│              │
│ Password:    │
│ ABC@123      │
└──────┬───────┘
       │
       │ Stored directly
       ↓
┌─────────────────────────────────────────┐
│         DATABASE (INSECURE)             │
├──────────────────┬──────────────────────┤
│ Email            │ Password             │
├──────────────────┼──────────────────────┤
│ shruti@gmail.com │ ABC@123              │ ← 🚨 PLAIN TEXT!
│ john@gmail.com   │ password123          │
│ alice@gmail.com  │ mySecret!            │
└──────────────────┴──────────────────────┘

If database is hacked:
└─→ Attacker sees all real passwords! 🚨
```

## 4. Visual Overview — Secure Way With Hashing

```
┌─────────────────────────────────────────────────────────────┐
│                    ✅ SECURE WAY (With Hashing)             │
└─────────────────────────────────────────────────────────────┘

User Signup
┌──────────────┐
│ Email:       │
│ shruti@      │
│ gmail.com    │
│              │
│ Password:    │
│ ABC@123      │
└──────┬───────┘
       │
       │ Sent to server
       ↓
┌─────────────────────────────────────────┐
│          SERVER                         │
│                                         │
│  Password: ABC@123                      │
│       ↓                                 │
│  [Hashing Algorithm - bcrypt]           │
│       ↓                                 │
│  Hash: $2a$10$X7g9QeJxK2M3dJk8...       │
└──────┬──────────────────────────────────┘
       │
       │ Store hash only
       ↓
┌─────────────────────────────────────────────────────────────────┐
│              DATABASE (SECURE)                                  │
├──────────────────┬──────────────────────────────────────────────┤
│ Email            │ Password Hash                                │
├──────────────────┼──────────────────────────────────────────────┤
│ shruti@gmail.com │ $2a$10$X7g9QeJxK2M3dJk8VZpGzOf7sRk...        │
│ john@gmail.com   │ $2a$10$Y8h0RfKyL3N4eKl9WaqHaQg8tSm...        │
│ alice@gmail.com  │ $2a$10$Z9i1SgLzM4O5fLm0XbrIbRh9uTn...        │
└──────────────────┴──────────────────────────────────────────────┘

If database is hacked:
└─→ Attacker only sees meaningless hashes ✅
└─→ Cannot reverse hash to get real password ✅
```

## 5. What Happens During Signup (Step-by-Step)

### Step 1 — User fills the signup form

```
Example:
Email: shruti@gmail.com
Password: ABC@123
```

User clicks **Sign Up**.

The frontend sends a request to the server.

```
Frontend → Server
POST /signup
{
  "email": "shruti@gmail.com",
  "password": "ABC@123"
}
```

### Step 2 — Server hashes the password

The server receives the password.

Instead of storing it directly, the server uses a hashing library such as:

- **bcrypt**
- **argon2**
- **PBKDF2**

Example using bcrypt:

```javascript
hashedPassword = bcrypt.hash("ABC@123")
```

The result may look like:

```
$2a$10$E7rYh8YcJ3V0Q5vGz...
```

### Step 3 — Store hashed password in database

The server stores:

```
Email: shruti@gmail.com
Password: $2a$10$E7rYh8YcJ3V0Q5vGz...
```

So the database contains:

| Email            | Password (Hashed)                        |
|------------------|------------------------------------------|
| shruti@gmail.com | $2a$10$E7rYh8YcJ3V0Q5vGz...                 |

Notice:

- ❌ Real password is not stored
- ✅ Only the hash value is stored

## 6. Visual Flow — Signup Process

```
┌──────────────────────────────────────────────────────────────────┐
│                        SIGNUP FLOW                               │
└──────────────────────────────────────────────────────────────────┘

Step 1: User Input
┌─────────────────┐
│   FRONTEND      │
│  ┌───────────┐  │
│  │ Email     │  │
│  │ Password  │  │
│  └─────┬─────┘  │
│        │        │
│    [Sign Up]    │
└────────┬────────┘
         │
         │ POST /signup
         │ { email, password: "ABC@123" }
         ↓
┌────────────────────────────────────────┐
│         BACKEND SERVER                 │
│                                        │
│  Step 2: Receive Password              │
│  ┌──────────────────────┐              │
│  │ password = "ABC@123" │              │
│  └──────────┬───────────┘              │
│             │                          │
│  Step 3: Hash Password                 │
│  ┌──────────▼───────────┐              │
│  │  bcrypt.hash()       │              │
│  │                      │              │
│  │  Input: ABC@123      │              │
│  │  Output: $2a$10$...  │              │
│  └──────────┬───────────┘              │
│             │                          │
│  Step 4: Store Hash                    │
│             │                          │
└─────────────┼──────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│           DATABASE                      │
│  ┌───────────────────────────────────┐  │
│  │ INSERT INTO users                 │  │
│  │ (email, password_hash)            │  │
│  │ VALUES                            │  │
│  │ ('shruti@gmail.com',              │  │
│  │  '$2a$10$E7rYh8...')              │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Stored:                                │
│  email: shruti@gmail.com                │
│  password_hash: $2a$10$E7rYh8...       │
└─────────────────────────────────────────┘
```

## 7. What Happens During Login (Step-by-Step)

Now suppose the same user wants to log in.

The user still enters the **real password**.

```
Email: shruti@gmail.com
Password: ABC@123
```

The user does not know that the password is stored as a hash.

### Step 1 — Login request sent

Frontend sends request:

```
POST /login
{
  "email": "shruti@gmail.com",
  "password": "ABC@123"
}
```

### Step 2 — Server retrieves stored hash

The server first finds the user in the database.

Example record:

```
Email: shruti@gmail.com
Password Hash: $2a$10$E7rYh8YcJ3V0Q5vGz...
```

### Step 3 — Hash the entered password

Now the server hashes the password entered during login.

```
hash("ABC@123")
```

### Step 4 — Compare hashes

The server compares:

```
Stored Hash
    VS
Login Hash
```

Example:

```
$2a$10$E7rYh8YcJ3V0Q5vGz...
        =
$2a$10$E7rYh8YcJ3V0Q5vGz...
```

If both hashes match:

✔ Login successful

If they do not match:

❌ Login rejected

## 8. Visual Flow — Login Process

```
┌──────────────────────────────────────────────────────────────────┐
│                        LOGIN FLOW                                │
└──────────────────────────────────────────────────────────────────┘

Step 1: User Input
┌─────────────────┐
│   FRONTEND      │
│  ┌───────────┐  │
│  │ Email     │  │
│  │ Password  │  │
│  └─────┬─────┘  │
│        │        │
│    [Login]      │
└────────┬────────┘
         │
         │ POST /login
         │ { email, password: "ABC@123" }
         ↓
┌────────────────────────────────────────────────────────────┐
│              BACKEND SERVER                                │
│                                                            │
│  Step 2: Receive Login Request                            │
│  ┌──────────────────────────────┐                         │
│  │ email: shruti@gmail.com      │                         │
│  │ password: "ABC@123"          │                         │
│  └──────────┬───────────────────┘                         │
│             │                                              │
│  Step 3: Query Database                                   │
│             │                                              │
└─────────────┼──────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│              DATABASE                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ SELECT password_hash FROM users                       │  │
│  │ WHERE email = 'shruti@gmail.com'                      │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                  │
│  Returns:                │                                  │
│  password_hash: $2a$10$E7rYh8...                           │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              BACKEND SERVER                                 │
│                                                             │
│  Step 4: Compare Hashes                                    │
│                                                             │
│  Stored Hash (from DB):                                    │
│  ┌────────────────────────────────────┐                    │
│  │  $2a$10$E7rYh8YcJ3V0Q5vGz...       │                    │
│  └────────────┬───────────────────────┘                    │
│               │                                             │
│  Hash of entered password:                                 │
│  ┌────────────▼───────────────────────┐                    │
│  │  bcrypt.hash("ABC@123")            │                    │
│  │  → $2a$10$E7rYh8YcJ3V0Q5vGz...     │                    │
│  └────────────┬───────────────────────┘                    │
│               │                                             │
│  Step 5: Compare                                           │
│  ┌────────────▼───────────────────────┐                    │
│  │  bcrypt.compare(                   │                    │
│  │    "ABC@123",                      │                    │
│  │    storedHash                      │                    │
│  │  )                                 │                    │
│  │                                    │                    │
│  │  Result: true ✅                   │                    │
│  └────────────┬───────────────────────┘                    │
│               │                                             │
│  Step 6: Decision                                          │
│               │                                             │
│      ┌────────┴────────┐                                   │
│      │                 │                                   │
│   Match?           No Match?                               │
│      │                 │                                   │
│      ↓                 ↓                                   │
│  ✅ Login          ❌ Login                                │
│   Success          Failed                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 9. Why Hashing is One-Way

Hashing algorithms are designed to be **one-way functions**.

Meaning:

```
Password → Hash ✔
Hash → Password ❌
```

Even the system cannot convert the hash back into the original password.

This protects users even if:

- the database is hacked
- the data is leaked

Attackers only get meaningless hashed values.

### Visual Representation of One-Way Function

```
┌──────────────────────────────────────────────────────────┐
│             ONE-WAY HASHING FUNCTION                     │
└──────────────────────────────────────────────────────────┘

Forward Direction (Possible ✅)
─────────────────────────────

Input Password          Hashing Algorithm          Hash Output
┌──────────┐                   │              ┌─────────────────┐
│ ABC@123  │ ──────────────────┼────────────→ │ $2a$10$E7rYh8  │
└──────────┘                   │              └─────────────────┘
                               │
                          bcrypt.hash()


Reverse Direction (IMPOSSIBLE ❌)
──────────────────────────────────

Hash Output                                    Original Password?
┌─────────────────┐                           ┌──────────┐
│ $2a$10$E7rYh8  │ ──────────X──────────────→ │    ???   │
└─────────────────┘        BLOCKED            └──────────┘

                    Cannot reverse the hash
                    Mathematical impossibility
```

## 10. Why bcrypt is Commonly Used

Modern applications usually use **bcrypt**.

Because it provides:

### 1. Salting

Random value added before hashing to prevent **rainbow table attacks**.

### 2. Slow hashing

bcrypt intentionally takes more time to compute.

This makes brute force attacks very difficult.

### 3. Built-in comparison

bcrypt provides a secure comparison method:

```javascript
bcrypt.compare(password, storedHash)
```

### Visual: bcrypt with Salt

```
┌─────────────────────────────────────────────────────────────┐
│              BCRYPT HASHING WITH SALT                       │
└─────────────────────────────────────────────────────────────┘

User 1 enters: "ABC@123"
┌──────────┐
│ ABC@123  │
└────┬─────┘
     │
     │ bcrypt generates random salt
     ↓
┌─────────────────────────┐
│  Salt: $2a$10$X7g9Qe    │  ← Random value
└────┬────────────────────┘
     │
     │ Combine password + salt
     ↓
┌──────────────────────────────────┐
│  ABC@123 + $2a$10$X7g9Qe         │
└────┬─────────────────────────────┘
     │
     │ Hash the combination
     ↓
┌───────────────────────────────────────────┐
│  Final Hash:                              │
│  $2a$10$X7g9QeJxK2M3dJk8VZpGzOf7sRk...   │
│  ─────────────────────────────────────    │
│  │        │                       │       │
│  │        │                       └─ Hash │
│  │        └─ Salt                         │
│  └─ Algorithm + Cost                      │
└───────────────────────────────────────────┘


User 2 ALSO enters: "ABC@123" (Same password!)
┌──────────┐
│ ABC@123  │
└────┬─────┘
     │
     │ bcrypt generates DIFFERENT random salt
     ↓
┌─────────────────────────┐
│  Salt: $2a$10$Y8h0Rf    │  ← Different random value
└────┬────────────────────┘
     │
     │ Combine password + salt
     ↓
┌──────────────────────────────────┐
│  ABC@123 + $2a$10$Y8h0Rf         │
└────┬─────────────────────────────┘
     │
     │ Hash the combination
     ↓
┌───────────────────────────────────────────┐
│  Final Hash:                              │
│  $2a$10$Y8h0RfKyL3N4eKl9WaqHaQg8tSm...   │  ← Different hash!
└───────────────────────────────────────────┘

Result:
Same password → Different hashes (because of different salts)
This prevents rainbow table attacks ✅
```

## 11. Real-World Example Flow

### Signup Flow

```
User enters password
        ↓
Server hashes password
        ↓
Hash stored in database
```

### Login Flow

```
User enters password
        ↓
Server hashes entered password
        ↓
Compare with stored hash
        ↓
If match → login success
If not → login failed
```

## 12. Complete End-to-End Visual Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  COMPLETE PASSWORD SECURITY FLOW                        │
└─────────────────────────────────────────────────────────────────────────┘

                        SIGNUP                    LOGIN
                          │                         │
                          │                         │
User Action          ┌────▼────┐              ┌────▼────┐
                     │ Register│              │  Login  │
                     │ Form    │              │  Form   │
                     └────┬────┘              └────┬────┘
                          │                         │
                          │ Password: ABC@123       │ Password: ABC@123
                          │                         │
                          ↓                         ↓
                     ┌─────────────────────────────────┐
Frontend             │  POST /signup                   │
                     │  { email, password }            │
                     └────┬───────────────────────┬────┘
                          │                       │
                          │                       │
                          ↓                       ↓
                     ┌─────────────────────────────────┐
Backend              │                                 │
                     │  bcrypt.hash()    bcrypt.compare()
                     │       ↓                  ↓      │
                     │   Generate         Compare      │
                     │    Hash             Hashes      │
                     └────┬───────────────────────┬────┘
                          │                       │
                          │                       │
                          ↓                       ↓
                     ┌─────────────────────────────────┐
Database             │  Store Hash         Retrieve    │
                     │                      Hash       │
                     │  ┌──────────────┐   ┌─────────┐│
                     │  │ password_hash│   │  Match? ││
                     │  │ $2a$10$...   │   │  ✅/❌  ││
                     │  └──────────────┘   └─────────┘│
                     └─────────────────────────────────┘
```

## 13. Security Benefits Summary

```
┌──────────────────────────────────────────────────────────┐
│           WHY PASSWORD HASHING IS SECURE                 │
└──────────────────────────────────────────────────────────┘

✅ Database Breach Protection
   └─ Even if database is hacked, real passwords are safe

✅ One-Way Function
   └─ Hash cannot be reversed to get original password

✅ Salting (with bcrypt)
   └─ Same password → Different hashes for different users
   └─ Prevents rainbow table attacks

✅ Slow Computation (with bcrypt)
   └─ Makes brute force attacks impractical

✅ No Plain Text Storage
   └─ System never stores real passwords

✅ Admin Cannot See Passwords
   └─ Even system administrators cannot view real passwords
```

## 14. Short Interview Answer (Best Version)

You can say this in an interview:

> In secure systems, the user's real password is never stored in the database. Instead, the password is hashed using algorithms like bcrypt.
>
> During signup, the server hashes the password and stores the hash value in the database.
>
> When the user logs in, the server hashes the entered password again and compares it with the stored hash.
>
> If both hashes match, the user is authenticated.
>
> Since hashing is a one-way function, even if the database is leaked, the original passwords cannot be recovered.
>
> bcrypt is commonly used because it includes salting (to prevent rainbow table attacks) and is intentionally slow (to prevent brute force attacks).

## 15. Bonus: Common Attack Scenarios and Defenses

```
┌──────────────────────────────────────────────────────────────┐
│              ATTACK SCENARIOS & DEFENSES                     │
└──────────────────────────────────────────────────────────────┘

Attack 1: Rainbow Table Attack
─────────────────────────────────
Attacker has pre-computed hashes for common passwords

Without Salt:
  Password: "password123"
  Hash: always same → attacker finds it in rainbow table ❌

With Salt (bcrypt):
  Password: "password123"
  Hash 1: $2a$10$X7g9Qe... (user 1)
  Hash 2: $2a$10$Y8h0Rf... (user 2)
  → Different hashes → rainbow table useless ✅


Attack 2: Brute Force Attack
────────────────────────────
Attacker tries millions of password combinations

Without bcrypt:
  Fast hashing → millions of attempts per second ❌

With bcrypt:
  Slow hashing → only thousands of attempts per second ✅
  → Makes brute force impractical


Attack 3: Database Leak
───────────────────────
Attacker gains access to database

Without hashing:
  Attacker sees: "password": "ABC@123" ❌
  → All passwords compromised immediately

With hashing:
  Attacker sees: "password_hash": "$2a$10$E7rYh8..." ✅
  → Cannot reverse to get real passwords
```

---

## Next Recommended Topic

**Difference between Hashing, Encryption, and Encoding**

This is a very common interview question that appears in almost every backend or Spring Boot interview!

Would you like me to create a detailed explanation for this next?