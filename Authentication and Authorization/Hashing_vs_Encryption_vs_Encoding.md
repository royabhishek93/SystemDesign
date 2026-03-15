# Hashing vs Encryption vs Encoding — Complete Explanation

## 1. The Interview Question

One of the most common interview questions in backend development is:

**"What is the difference between Hashing, Encryption, and Encoding?"**

Many candidates confuse these terms because they all involve transforming data.

But they serve **completely different purposes** and have different characteristics.

Let's understand each one clearly.

## 2. Quick Comparison Table

| Feature | Hashing | Encryption | Encoding |
|---------|---------|------------|----------|
| **Purpose** | Data integrity & password storage | Data confidentiality | Data representation |
| **Reversible?** | ❌ No (One-way) | ✅ Yes (Two-way) | ✅ Yes (Two-way) |
| **Uses a key?** | ❌ No | ✅ Yes | ❌ No |
| **Security?** | ✅ Secure | ✅ Secure (with key) | ❌ Not secure |
| **Output length** | Fixed | Variable | Variable |
| **Use case** | Passwords, checksums | Sensitive data transmission | Data format conversion |
| **Examples** | bcrypt, SHA-256, MD5 | AES, RSA, DES | Base64, UTF-8, ASCII |

## 3. Visual Overview — All Three Compared

```
┌────────────────────────────────────────────────────────────────────┐
│                    HASHING vs ENCRYPTION vs ENCODING               │
└────────────────────────────────────────────────────────────────────┘

HASHING (One-Way)
─────────────────
Input: "password123"
   │
   │ Hash Function (SHA-256)
   ↓
Output: "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"
   │
   │ ❌ Cannot reverse
   ↓
   ✗ Cannot get back "password123"


ENCRYPTION (Two-Way with Key)
──────────────────────────────
Input: "Secret Message"
   │
   │ Encrypt (AES) + Key: "mySecretKey123"
   ↓
Output: "U2FsdGVkX1+jQ3..."
   │
   │ ✅ Can decrypt with same key
   ↓
   ✓ Decrypt → "Secret Message"


ENCODING (Two-Way, No Key)
───────────────────────────
Input: "Hello World"
   │
   │ Encode (Base64)
   ↓
Output: "SGVsbG8gV29ybGQ="
   │
   │ ✅ Can decode (no key needed)
   ↓
   ✓ Decode → "Hello World"
```

## 4. Hashing — Detailed Explanation

### What is Hashing?

Hashing is a **one-way function** that converts input data into a **fixed-size** string of characters.

The same input always produces the same output.

**Key Characteristics:**

- ✅ One-way function (cannot reverse)
- ✅ Fixed output length
- ✅ Same input → Same output
- ✅ Different input → (Usually) Different output
- ❌ No key required

### Visual: Hashing Process

```
┌─────────────────────────────────────────────────────────────┐
│                     HASHING PROCESS                         │
└─────────────────────────────────────────────────────────────┘

Input Data          Hash Function          Hash Output
─────────────       ──────────────         ────────────

"password123"           SHA-256         ef92b778bafe771e...
     │                     │             (64 characters)
     │                     │
     └─────────────────────┼────────────→ Fixed length
                           │
"abc"                   SHA-256         ba7816bf8f01cfea...
     │                     │             (64 characters)
     │                     │
     └─────────────────────┼────────────→ Same length!
                           │
"LongPasswordWith        SHA-256         5e884898da28047...
 ManyCharacters123"        │             (64 characters)
     │                     │
     └─────────────────────┼────────────→ Still same length!
                           │

Observation:
Different input lengths → Same output length (fixed)
```

### Common Hashing Algorithms

| Algorithm | Output Length | Use Case | Security |
|-----------|---------------|----------|----------|
| **MD5** | 128 bits (32 hex) | ❌ Outdated, broken | Insecure |
| **SHA-1** | 160 bits (40 hex) | ❌ Deprecated | Weak |
| **SHA-256** | 256 bits (64 hex) | ✅ Checksums, integrity | Strong |
| **bcrypt** | Variable | ✅ Password hashing | Very strong |
| **Argon2** | Variable | ✅ Password hashing | Very strong |

### Use Cases for Hashing

#### 1. Password Storage

```
User Password: "myPassword123"
        ↓
    bcrypt.hash()
        ↓
Stored Hash: "$2a$10$X7g9QeJxK2M3..."
```

#### 2. Data Integrity Verification

```
Original File → Hash → abc123def456
        ↓
 Send file over network
        ↓
Received File → Hash → abc123def456
        ↓
Compare hashes → Match? → File is intact ✅
```

#### 3. Digital Signatures

```
Document → Hash → Sign with private key → Signature
```

### Visual: Password Hashing Flow

```
┌─────────────────────────────────────────────────────────────┐
│              PASSWORD HASHING (One-Way)                     │
└─────────────────────────────────────────────────────────────┘

SIGNUP
──────
User enters: "myPassword123"
       │
       │ bcrypt.hash()
       ↓
Stored: "$2a$10$X7g9QeJxK2M3dJk8VZpGzOf7sRk..."
       │
       │ Stored in database
       ↓
   [Database]
       │
       │ ❌ Cannot get back "myPassword123"
       │    Even the admin cannot see it!
       ↓


LOGIN
─────
User enters: "myPassword123"
       │
       │ bcrypt.hash()
       ↓
Generated: "$2a$10$X7g9QeJxK2M3dJk8VZpGzOf7sRk..."
       │
       │ Compare with stored hash
       ↓
   Match? ✅ → Login success
```

### Important Properties

**Property 1: Deterministic**

```
Input: "hello"  →  Hash: abc123...
Input: "hello"  →  Hash: abc123...  (Same!)
Input: "hello"  →  Hash: abc123...  (Same!)
```

**Property 2: Avalanche Effect**

Small change in input → Completely different output

```
Input: "hello"   →  Hash: 2cf24dba5fb0a30e...
Input: "Hello"   →  Hash: 185f8db32271fe25...  (Totally different!)
```

**Property 3: Fixed Output Length**

```
Input: "a"                    →  Hash: ca978112ca1b... (64 chars)
Input: "abcdefghijklmnop..."  →  Hash: 50b8c6c1c5f0... (64 chars)
```

## 5. Encryption — Detailed Explanation

### What is Encryption?

Encryption is a **two-way function** that converts plaintext into ciphertext using a **key**.

The ciphertext can be **decrypted** back to plaintext using the same key (or a corresponding key).

**Key Characteristics:**

- ✅ Two-way function (reversible)
- ✅ Requires a key
- ✅ Protects confidentiality
- ✅ Can decrypt to get original data
- ✅ Variable output length

### Visual: Encryption Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENCRYPTION PROCESS                           │
└─────────────────────────────────────────────────────────────────┘

ENCRYPTION (Plaintext → Ciphertext)
───────────────────────────────────

Plaintext: "Secret Message"
       │
       │ + Key: "myKey123"
       │
       │ Encrypt (AES-256)
       ↓
Ciphertext: "U2FsdGVkX1+jQ3eT9kJ..."
       │
       │ Can be transmitted safely
       ↓


DECRYPTION (Ciphertext → Plaintext)
───────────────────────────────────

Ciphertext: "U2FsdGVkX1+jQ3eT9kJ..."
       │
       │ + Key: "myKey123"  (Same key!)
       │
       │ Decrypt (AES-256)
       ↓
Plaintext: "Secret Message"  ✅ Original data recovered!
```

### Types of Encryption

#### 1. Symmetric Encryption (Same Key)

```
┌─────────────────────────────────────────────────────────┐
│           SYMMETRIC ENCRYPTION                          │
└─────────────────────────────────────────────────────────┘

Sender Side                                Receiver Side
───────────                                ──────────────

Plaintext                                  Ciphertext
"Hello"                                    "xJ9k2..."
   │                                           │
   │  Encrypt with                             │  Decrypt with
   │  Key: "secret123"                         │  Key: "secret123"
   │           │                               │        │
   ↓           ↓                               ↓        ↓
Ciphertext ─────────── Transmission ──────→ Plaintext
"xJ9k2..."      (over network)              "Hello"

Same Key Used for Both Encryption and Decryption! 🔑
```

**Symmetric Algorithms:**

- **AES** (Advanced Encryption Standard) — Most popular
- **DES** (Data Encryption Standard) — Outdated
- **3DES** (Triple DES) — More secure than DES
- **Blowfish**
- **ChaCha20**

**Use Cases:**

- Encrypting files on disk
- Database encryption
- VPN connections
- SSL/TLS (partially)

#### 2. Asymmetric Encryption (Key Pair)

```
┌─────────────────────────────────────────────────────────────┐
│             ASYMMETRIC ENCRYPTION                           │
└─────────────────────────────────────────────────────────────┘

Sender Side                                    Receiver Side
───────────                                    ─────────────

Plaintext                                      Has:
"Hello"                                        - Public Key 🔓
   │                                           - Private Key 🔐
   │  Encrypt with
   │  Receiver's PUBLIC Key 🔓
   │
   ↓
Ciphertext ───────── Transmission ──────→     Ciphertext
"xJ9k2..."    (over network)                  "xJ9k2..."
                                                   │
                                                   │  Decrypt with
                                                   │  Private Key 🔐
                                                   ↓
                                               Plaintext
                                               "Hello"

Different Keys Used! Public key encrypts, Private key decrypts
```

**Asymmetric Algorithms:**

- **RSA** (Most popular)
- **ECC** (Elliptic Curve Cryptography)
- **DSA** (Digital Signature Algorithm)
- **Diffie-Hellman**

**Use Cases:**

- SSL/TLS handshake
- Digital signatures
- Email encryption (PGP)
- SSH key authentication

### Comparison: Symmetric vs Asymmetric

| Feature | Symmetric | Asymmetric |
|---------|-----------|------------|
| **Keys** | Same key for both | Key pair (public + private) |
| **Speed** | ✅ Fast | ❌ Slow |
| **Key distribution** | ❌ Difficult | ✅ Easy |
| **Use case** | Bulk data | Key exchange, signatures |
| **Example** | AES, DES | RSA, ECC |

### Use Cases for Encryption

#### 1. Secure Communication

```
User A                        User B
  │                             │
  │  "Hello" + Key              │
  │  → Encrypt → "xJ9k..."      │
  │                             │
  ├──────────────────────────→  │
  │       Ciphertext            │
  │                             │
  │                             │  Decrypt with Key
  │                             │  → "Hello"
  │                             │
```

#### 2. Database Encryption

```
Sensitive Data: "Credit Card: 1234-5678-9012-3456"
        ↓
   Encrypt (AES)
        ↓
Stored: "U2FsdGVkX1+jQ3eT9..."
        ↓
   [Database]
        ↓
When needed:
   Decrypt with key → "Credit Card: 1234-5678-9012-3456"
```

#### 3. File Encryption

```
Original File: document.pdf
        ↓
   Encrypt with password
        ↓
Encrypted File: document.pdf.enc
        ↓
Only someone with the password can decrypt and open it
```

## 6. Encoding — Detailed Explanation

### What is Encoding?

Encoding is a **two-way transformation** that converts data from one format to another.

**It is NOT for security!**

**Key Characteristics:**

- ✅ Two-way function (reversible)
- ❌ No key required
- ❌ NOT secure (anyone can decode)
- ✅ For data representation/transmission
- ✅ Variable output length

### Visual: Encoding Process

```
┌─────────────────────────────────────────────────────────────┐
│                    ENCODING PROCESS                         │
└─────────────────────────────────────────────────────────────┘

ENCODING
────────
Input: "Hello World"
   │
   │ Encode (Base64)
   ↓
Output: "SGVsbG8gV29ybGQ="
   │
   │ ⚠️ NOT secure! Anyone can decode
   ↓


DECODING
────────
Input: "SGVsbG8gV29ybGQ="
   │
   │ Decode (Base64)
   ↓
Output: "Hello World"  ✅ Original data recovered
```

### Common Encoding Schemes

#### 1. Base64 Encoding

```
┌─────────────────────────────────────────────────────────┐
│                 BASE64 ENCODING                         │
└─────────────────────────────────────────────────────────┘

Original: "Hello"
   │
   │ Base64 Encode
   ↓
Encoded: "SGVsbG8="
   │
   │ Base64 Decode (no key needed!)
   ↓
Original: "Hello"

Use Cases:
✅ Embedding images in HTML/CSS
✅ Sending binary data over email (MIME)
✅ Encoding binary data in JSON
✅ URL-safe data transmission
```

**Example:**

```
Text: "Hello"
Binary: 01001000 01100101 01101100 01101100 01101111
Base64: "SGVsbG8="
```

#### 2. URL Encoding

```
Original: "hello world"
   │
   │ URL Encode
   ↓
Encoded: "hello%20world"


Original: "name=John Doe&age=30"
   │
   │ URL Encode
   ↓
Encoded: "name%3DJohn%20Doe%26age%3D30"
```

#### 3. Character Encoding (UTF-8, ASCII)

```
Character: "A"
   │
   │ ASCII Encoding
   ↓
Binary: 01000001 (65 in decimal)


Character: "€" (Euro symbol)
   │
   │ UTF-8 Encoding
   ↓
Binary: 11100010 10000010 10101100
```

### Use Cases for Encoding

#### 1. Data Transmission

```
Binary Image Data
        ↓
   Base64 Encode
        ↓
Text String "iVBORw0KGgoAAAANSUhEUgAA..."
        ↓
   Send over HTTP (text-based protocol)
        ↓
   Base64 Decode
        ↓
Original Image Data
```

#### 2. Email Attachments

```
PDF File (binary)
        ↓
   Base64 Encode
        ↓
Text representation in email
        ↓
   Base64 Decode
        ↓
Original PDF File
```

#### 3. Embedding Images in HTML

```html
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." />
                                 └─────────────────────────┘
                                    Base64 encoded image
```

### Important: Encoding is NOT Secure!

```
⚠️  COMMON MISTAKE  ⚠️
─────────────────────

❌ WRONG:
Password: "myPassword"
   │
   │ Base64 Encode
   ↓
Stored: "bXlQYXNzd29yZA=="  ← Anyone can decode this!

✅ CORRECT:
Password: "myPassword"
   │
   │ bcrypt Hash
   ↓
Stored: "$2a$10$X7g9QeJxK2M3..."  ← Secure! Cannot reverse
```

## 7. Side-by-Side Comparison Example

Let's take the same input and apply all three:

```
┌─────────────────────────────────────────────────────────────────┐
│         SAME INPUT, THREE DIFFERENT OPERATIONS                  │
└─────────────────────────────────────────────────────────────────┘

Original Data: "Hello World"


HASHING (SHA-256)
─────────────────
Input: "Hello World"
   ↓
Output: "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
   │
   ↓ Can we reverse?
   ❌ NO! One-way function


ENCRYPTION (AES-256)
────────────────────
Input: "Hello World"
   ↓ + Key: "secret123"
Output: "U2FsdGVkX19Q3eT9kJ2mH8..."
   │
   ↓ Can we reverse?
   ✅ YES! With the key "secret123"
   ↓
Decrypted: "Hello World"


ENCODING (Base64)
─────────────────
Input: "Hello World"
   ↓
Output: "SGVsbG8gV29ybGQ="
   │
   ↓ Can we reverse?
   ✅ YES! No key needed, anyone can decode
   ↓
Decoded: "Hello World"
```

## 8. Real-World Scenarios

### Scenario 1: Storing User Passwords

```
❌ WRONG: Use Encoding
Password → Base64 → Store
Problem: Anyone can decode it!

❌ WRONG: Use Encryption
Password → Encrypt → Store
Problem: If key is leaked, all passwords exposed!

✅ CORRECT: Use Hashing
Password → bcrypt Hash → Store
Why: Cannot reverse, secure even if database leaks
```

### Scenario 2: Sending Sensitive Data Over Network

```
❌ WRONG: Use Hashing
Data → Hash → Send
Problem: Receiver cannot get original data back!

❌ WRONG: Use Encoding
Data → Base64 → Send
Problem: Anyone can decode it in transit!

✅ CORRECT: Use Encryption
Data → Encrypt (with TLS/SSL) → Send → Decrypt
Why: Only intended receiver can decrypt
```

### Scenario 3: Embedding Image in HTML

```
❌ WRONG: Use Hashing
Image → Hash → Embed
Problem: Cannot reconstruct image from hash!

❌ WRONG: Use Encryption
Image → Encrypt → Embed
Problem: Browser cannot decrypt without key!

✅ CORRECT: Use Encoding
Image → Base64 → Embed in <img> tag
Why: Browser can decode Base64 automatically
```

### Scenario 4: Verifying File Integrity

```
❌ WRONG: Use Encoding
File → Base64 → Compare
Problem: Not efficient for integrity check!

❌ WRONG: Use Encryption
File → Encrypt → Compare
Problem: Unnecessary overhead!

✅ CORRECT: Use Hashing
File → SHA-256 Hash → Compare hashes
Why: Fast, fixed-size, detects any changes
```

## 9. Complete Visual Comparison

```
┌──────────────────────────────────────────────────────────────────┐
│              HASHING vs ENCRYPTION vs ENCODING                   │
│                    COMPLETE COMPARISON                           │
└──────────────────────────────────────────────────────────────────┘

HASHING
───────
Purpose:     Data Integrity, Password Storage
Direction:   One-Way (→)
Reversible:  ❌ No
Key:         ❌ Not required
Security:    ✅ Secure
Output:      Fixed length

Example:
"password" → [SHA-256] → "5e884898da28047151d0e56f8dc6292..."
                            ↓
                         Cannot reverse ❌


ENCRYPTION
──────────
Purpose:     Data Confidentiality
Direction:   Two-Way (⇄)
Reversible:  ✅ Yes (with key)
Key:         ✅ Required
Security:    ✅ Secure (if key is secure)
Output:      Variable length

Example:
"password" → [AES + Key] → "U2FsdGVkX1+jQ3..."
                               ↓
                         Can decrypt with key ✅
                               ↓
                          "password"


ENCODING
────────
Purpose:     Data Representation
Direction:   Two-Way (⇄)
Reversible:  ✅ Yes (no key needed)
Key:         ❌ Not required
Security:    ❌ NOT secure
Output:      Variable length

Example:
"password" → [Base64] → "cGFzc3dvcmQ="
                            ↓
                      Anyone can decode ⚠️
                            ↓
                        "password"
```

## 10. Decision Tree — Which One to Use?

```
┌─────────────────────────────────────────────────────────────┐
│              DECISION TREE                                  │
└─────────────────────────────────────────────────────────────┘

Start: What is your goal?
    │
    ├─→ Need to verify data hasn't changed?
    │   └─→ Use HASHING (SHA-256, bcrypt)
    │       Examples: Checksums, file integrity, passwords
    │
    ├─→ Need to protect data but retrieve it later?
    │   └─→ Use ENCRYPTION (AES, RSA)
    │       Examples: Credit cards, sensitive user data, communications
    │
    └─→ Need to represent data in different format?
        └─→ Use ENCODING (Base64, URL encoding)
            Examples: Images in HTML, URL parameters, email attachments
```

## 11. Common Interview Questions & Answers

### Q1: Why can't we use encoding for passwords?

**Answer:**

> Encoding is not secure because it's reversible without any key. Anyone can decode Base64 or other encoding schemes. For passwords, we need a one-way function (hashing) so that even if the database is compromised, attackers cannot retrieve the original passwords.

### Q2: Why don't we encrypt passwords instead of hashing them?

**Answer:**

> Encryption requires a key. If we encrypt passwords, we need to store the encryption key somewhere. If that key is compromised, all passwords can be decrypted. With hashing, there's no key to protect, and the hash cannot be reversed, making it more secure for password storage.

### Q3: Can you decrypt a hash?

**Answer:**

> No, hashing is a one-way function and cannot be reversed. However, attackers can use brute force or rainbow tables to try to find the original input. This is why we use salted hashing algorithms like bcrypt, which make such attacks impractical.

### Q4: When would you use symmetric vs asymmetric encryption?

**Answer:**

> Symmetric encryption (like AES) is faster and used for encrypting large amounts of data, such as file encryption or VPN connections.
>
> Asymmetric encryption (like RSA) is slower but doesn't require sharing the private key. It's used for key exchange, digital signatures, and SSL/TLS handshakes.
>
> Often, they're used together: asymmetric encryption to securely exchange a symmetric key, then symmetric encryption for the actual data.

### Q5: Is Base64 encoding secure?

**Answer:**

> No, Base64 encoding is NOT secure. It's a data representation format, not a security mechanism. Anyone can decode Base64 without any key. It's used for representing binary data in text format, not for protecting sensitive information.

## 12. Quick Interview Answer (Complete)

You can say this in an interview:

> **Hashing** is a one-way function that converts data into a fixed-size hash value. It cannot be reversed and is used for password storage and data integrity verification. Examples include bcrypt and SHA-256.
>
> **Encryption** is a two-way function that converts plaintext to ciphertext using a key. It can be decrypted back to the original data using the same key (symmetric) or a corresponding key pair (asymmetric). It's used to protect data confidentiality. Examples include AES and RSA.
>
> **Encoding** is a two-way transformation that changes data format without any key. It's NOT for security but for data representation and transmission. Anyone can decode it. Examples include Base64 and URL encoding.
>
> The key difference: Hashing is one-way and cannot be reversed, encryption is two-way with a key, and encoding is two-way without a key and not secure.

## 13. Visual Summary Cheat Sheet

```
┌──────────────────────────────────────────────────────────────┐
│                  QUICK REFERENCE                             │
└──────────────────────────────────────────────────────────────┘

HASHING
───────
Symbol:        →
Formula:       Data → Hash
Reverse:       ❌
Key:           ❌
Security:      ✅
Use:           Passwords, Integrity
Example:       password → 5e884898da28...


ENCRYPTION
──────────
Symbol:        ⇄
Formula:       Data + Key ⇄ Encrypted
Reverse:       ✅ (with key)
Key:           ✅
Security:      ✅
Use:           Confidential data
Example:       password + key ⇄ U2FsdGVk...


ENCODING
────────
Symbol:        ⇄
Formula:       Data ⇄ Encoded
Reverse:       ✅ (no key)
Key:           ❌
Security:      ❌
Use:           Format conversion
Example:       password ⇄ cGFzc3dvcmQ=
```

## 14. Real Code Examples

### Example 1: Hashing (Node.js with bcrypt)

```javascript
const bcrypt = require('bcrypt');

// Hashing
async function hashPassword(password) {
  const saltRounds = 10;
  const hash = await bcrypt.hash(password, saltRounds);
  return hash;
}

// Cannot reverse the hash!
const hashed = await hashPassword('myPassword123');
console.log(hashed);
// Output: $2b$10$X7g9QeJxK2M3dJk8VZpGzOf7sRk...

// Verification (not decryption!)
const isMatch = await bcrypt.compare('myPassword123', hashed);
console.log(isMatch); // true
```

### Example 2: Encryption (Node.js with crypto)

```javascript
const crypto = require('crypto');

// Encryption
function encrypt(text, key) {
  const cipher = crypto.createCipher('aes-256-cbc', key);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  return encrypted;
}

// Decryption
function decrypt(encrypted, key) {
  const decipher = crypto.createDecipher('aes-256-cbc', key);
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}

const key = 'mySecretKey123';
const encrypted = encrypt('Hello World', key);
console.log(encrypted); // "a8f3c2d1e5..."

const decrypted = decrypt(encrypted, key);
console.log(decrypted); // "Hello World" ✅
```

### Example 3: Encoding (Node.js)

```javascript
// Base64 Encoding
const text = 'Hello World';
const encoded = Buffer.from(text).toString('base64');
console.log(encoded); // "SGVsbG8gV29ybGQ="

// Base64 Decoding (no key needed!)
const decoded = Buffer.from(encoded, 'base64').toString('utf8');
console.log(decoded); // "Hello World" ✅

// Anyone can decode this! Not secure!
```

---

## Summary

```
┌──────────────────────────────────────────────────────────────┐
│                     REMEMBER THIS                            │
└──────────────────────────────────────────────────────────────┘

🔐 HASHING
   └─ One-way ticket → No return
   └─ Use for: Passwords, Checksums

🔒 ENCRYPTION
   └─ Round trip with key → Can return with key
   └─ Use for: Sensitive data, Communications

📝 ENCODING
   └─ Format change → Anyone can return
   └─ Use for: Data representation, NOT security
```

This is one of the most important concepts in backend security!

Make sure you understand the differences clearly for interviews.