# Database Indexing - Speed Up Your Queries

## What is a Database Index?

A **database index** is like an **index in a book** - it helps you find information quickly without reading every page.

Without an index, the database must scan **every row** (full table scan). With an index, it jumps directly to the matching rows.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BOOK INDEX ANALOGY                                    │
└─────────────────────────────────────────────────────────────────────────┘

WITHOUT INDEX (Reading entire book):
─────────────────────────────────────
Find all mentions of "Database"

Page 1   ──┐
Page 2   ──┤
Page 3   ──┤
Page 4   ──┤  Read every page
...      ──┤  Slow! ❌
Page 498 ──┤
Page 499 ──┤
Page 500 ──┘

Time: 30 minutes


WITH INDEX (Using book index):
───────────────────────────────
Look up "Database" in index → Pages: 45, 123, 287

Page 45  ──┐
Page 123 ──┤  Jump directly to relevant pages
Page 287 ──┘  Fast! ✓

Time: 2 minutes


DATABASE ANALOGY:
─────────────────

WITHOUT INDEX (Full Table Scan):
┌──────────────────────────────────────┐
│ users table (1 million rows)        │
├──────────────────────────────────────┤
│ id │ name    │ email    │ age │     │
│ 1  │ Alice   │ a@x.com  │ 25  │ ←── Scan
│ 2  │ Bob     │ b@x.com  │ 30  │ ←── Scan
│ 3  │ Charlie │ c@x.com  │ 35  │ ←── Scan
│ ...│ ...     │ ...      │ ... │ ←── Scan all
│ 1M │ Zoe     │ z@x.com  │ 28  │ ←── Scan
└──────────────────────────────────────┘

Query: SELECT * FROM users WHERE email = 'bob@x.com';
Scans: 1,000,000 rows
Time: 2 seconds ❌


WITH INDEX on email:
┌──────────────────────────────────────┐
│ Index on email                       │
├──────────────────────────────────────┤
│ a@x.com  → row 1                     │
│ b@x.com  → row 2   ← Direct lookup  │
│ c@x.com  → row 3                     │
│ ...                                  │
│ z@x.com  → row 1M                    │
└──────────────────────────────────────┘
         │
         └──▶ Jump to row 2

Query: SELECT * FROM users WHERE email = 'bob@x.com';
Scans: 1 row (via index)
Time: 0.01 seconds ✓
```

---

## How Indexes Work Internally

### B-Tree Index (Most Common)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    B-TREE INDEX STRUCTURE                                │
└─────────────────────────────────────────────────────────────────────────┘

Table: users
┌────┬───────┬──────────────┬─────┐
│ id │ name  │ email        │ age │
├────┼───────┼──────────────┼─────┤
│ 1  │ Alice │ alice@x.com  │ 25  │
│ 2  │ Bob   │ bob@x.com    │ 30  │
│ 3  │ Eve   │ eve@x.com    │ 22  │
│ 4  │ John  │ john@x.com   │ 35  │
│ 5  │ Mary  │ mary@x.com   │ 28  │
│ 6  │ Tom   │ tom@x.com    │ 40  │
└────┴───────┴──────────────┴─────┘

Index on 'age' (B-Tree):
────────────────────────

Level 0 (Root Node):
                    ┌─────────┐
                    │   30    │
                    └────┬────┘
                         │
            ┌────────────┴────────────┐
            │                         │
Level 1:    │                         │
      ┌─────▼─────┐             ┌─────▼─────┐
      │   25      │             │   35      │
      └─────┬─────┘             └─────┬─────┘
            │                         │
      ┌─────┴─────┐             ┌─────┴─────┐
      │           │             │           │
Level 2 (Leaf Nodes):
    ┌─▼─┐  ┌─▼─┐  ┌─▼─┐       ┌─▼─┐  ┌─▼─┐  ┌─▼─┐
    │22 │  │25 │  │28 │       │30 │  │35 │  │40 │
    │→3 │  │→1 │  │→5 │       │→2 │  │→4 │  │→6 │
    └───┘  └───┘  └───┘       └───┘  └───┘  └───┘
     ↓      ↓      ↓           ↓      ↓      ↓
    Row 3  Row 1  Row 5       Row 2  Row 4  Row 6


Query: SELECT * FROM users WHERE age = 28;

Lookup Steps:
─────────────
1. Start at root: 28 < 30 → Go left
2. Node: 25, 28 → Go right
3. Leaf: 28 → Points to row 5
4. Fetch row 5 directly

Total comparisons: 3 (instead of scanning 6 rows)
Time complexity: O(log n)


For 1 million rows:
───────────────────
Without index: 1,000,000 comparisons
With B-Tree:   log₂(1,000,000) ≈ 20 comparisons

50,000x faster! ✓
```

### Hash Index

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        HASH INDEX                                        │
└─────────────────────────────────────────────────────────────────────────┘

Used for exact match queries (=) only

Table: users
┌────┬──────────────┐
│ id │ email        │
├────┼──────────────┤
│ 1  │ alice@x.com  │
│ 2  │ bob@x.com    │
│ 3  │ eve@x.com    │
└────┴──────────────┘

Hash Index on 'email':
──────────────────────

Hash Function: email → hash code → bucket

┌──────────────────────────────────────────┐
│          Hash Index                      │
├──────────────────────────────────────────┤
│ Bucket 0: []                             │
│ Bucket 1: [bob@x.com → row 2]            │
│ Bucket 2: []                             │
│ Bucket 3: [alice@x.com → row 1]          │
│ Bucket 4: [eve@x.com → row 3]            │
│ Bucket 5: []                             │
│ ...                                      │
└──────────────────────────────────────────┘

Query: SELECT * FROM users WHERE email = 'bob@x.com';

Lookup:
───────
1. Hash('bob@x.com') → Bucket 1
2. Direct lookup in Bucket 1
3. Fetch row 2

Time complexity: O(1) - Constant time! ✓

Limitations:
────────────
✓ Exact match (=): Fast
✗ Range queries (>, <): Cannot use hash index
✗ LIKE queries: Cannot use hash index
✗ ORDER BY: Cannot use hash index

Good for:
• Primary key lookups
• Unique constraints
• Cache keys
```

---

## Types of Indexes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INDEX TYPES                                       │
└─────────────────────────────────────────────────────────────────────────┘

1. PRIMARY KEY INDEX (Clustered Index)
───────────────────────────────────────

CREATE TABLE users (
    id INT PRIMARY KEY,  ← Automatically creates clustered index
    name VARCHAR(100),
    email VARCHAR(100)
);

┌─────────────────────────────────────┐
│ Table data stored in PRIMARY KEY    │
│ order (physically sorted by id)     │
├─────────────────────────────────────┤
│ id=1  │ Alice  │ alice@x.com        │
│ id=2  │ Bob    │ bob@x.com          │
│ id=3  │ Eve    │ eve@x.com          │
└─────────────────────────────────────┘

✓ One per table (data stored in this order)
✓ Fastest for primary key lookups
✓ Range queries on PK very fast


2. UNIQUE INDEX
───────────────

CREATE UNIQUE INDEX idx_email ON users(email);

Enforces uniqueness + faster lookups

┌──────────────────────┐
│  Unique Index        │
├──────────────────────┤
│ alice@x.com → row 1  │
│ bob@x.com   → row 2  │
│ eve@x.com   → row 3  │
└──────────────────────┘

✓ Prevents duplicate emails
✓ Fast lookups
✓ Can have multiple unique indexes per table


3. COMPOSITE INDEX (Multi-column)
──────────────────────────────────

CREATE INDEX idx_name_age ON users(name, age);

Index on multiple columns (order matters!)

┌──────────────────────────────────┐
│  Composite Index (name, age)     │
├──────────────────────────────────┤
│ (Alice, 25)  → row 1             │
│ (Bob, 30)    → row 2             │
│ (Bob, 35)    → row 4             │
│ (Eve, 22)    → row 3             │
└──────────────────────────────────┘

Works for:
✓ WHERE name = 'Bob' AND age = 30
✓ WHERE name = 'Bob'  (uses first column)
✗ WHERE age = 30      (doesn't use index - age not first!)

Left-most prefix rule:
• (name, age) index works for: name, (name + age)
• Does NOT work for: age alone


4. COVERING INDEX
─────────────────

Index that includes all columns needed by query

CREATE INDEX idx_covering ON users(email, name, age);

Query: SELECT name, age FROM users WHERE email = 'bob@x.com';

✓ All data in index (email, name, age)
✓ No need to access table (Index-Only Scan)
✓ Faster!

Without covering index:
1. Search index for email → Get row ID
2. Fetch row from table → Get name, age

With covering index:
1. Search index for email → Get name, age directly ✓


5. PARTIAL INDEX (Filtered)
───────────────────────────

Index only on subset of rows

CREATE INDEX idx_active_users ON users(email) WHERE active = true;

┌──────────────────────────────────┐
│  Partial Index (active users)    │
├──────────────────────────────────┤
│ alice@x.com → row 1 (active)     │
│ bob@x.com   → row 2 (active)     │
│ (eve@x.com  → row 3 NOT indexed) │
└──────────────────────────────────┘

✓ Smaller index (only active users)
✓ Faster updates (inactive users don't update index)
✓ Use when: Most queries filter on same condition


6. FULL-TEXT INDEX
──────────────────

For text search (LIKE, contains)

CREATE FULLTEXT INDEX idx_description ON products(description);

Query: SELECT * FROM products WHERE MATCH(description) AGAINST('laptop');

✓ Fast text search
✓ Supports relevance ranking
✓ Better than LIKE '%laptop%'

Use case: Product search, article search
```

---

## Index Performance Impact

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INDEX PERFORMANCE COMPARISON                          │
└─────────────────────────────────────────────────────────────────────────┘

Test: Find user by email in 1 million row table

WITHOUT INDEX:
──────────────
SELECT * FROM users WHERE email = 'user123@example.com';

Execution:
• Full table scan
• Scans: 1,000,000 rows
• Time: 2.5 seconds ❌
• Query plan: Seq Scan on users

EXPLAIN output:
┌────────────────────────────────────────┐
│ Seq Scan on users                      │
│ Filter: (email = 'user123@example.com')│
│ Rows: 1000000                          │
│ Time: 2500ms                           │
└────────────────────────────────────────┘


WITH INDEX on email:
────────────────────
CREATE INDEX idx_email ON users(email);

SELECT * FROM users WHERE email = 'user123@example.com';

Execution:
• Index scan
• Scans: 1 row (via index)
• Time: 0.01 seconds ✓
• Query plan: Index Scan using idx_email

EXPLAIN output:
┌────────────────────────────────────────┐
│ Index Scan using idx_email             │
│ Index Cond: (email = 'user123@x.com')  │
│ Rows: 1                                │
│ Time: 10ms                             │
└────────────────────────────────────────┘

250x faster! ✓


RANGE QUERY COMPARISON:
───────────────────────

Query: SELECT * FROM orders WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31';

Without Index:
• Seq Scan: 5,000,000 rows
• Time: 8 seconds

With Index on order_date:
• Index Range Scan: 50,000 matching rows
• Time: 0.2 seconds

40x faster! ✓
```

---

## When Indexes Help (and When They Don't)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WHEN TO USE INDEXES                                   │
└─────────────────────────────────────────────────────────────────────────┘

✓ INDEXES HELP:
───────────────

1. WHERE clause with selective columns
   SELECT * FROM users WHERE email = 'alice@x.com';
   ✓ Email likely unique → Index helpful

2. JOIN columns
   SELECT * FROM orders o JOIN users u ON o.user_id = u.id;
   ✓ Index on user_id speeds up join

3. ORDER BY columns
   SELECT * FROM products ORDER BY price;
   ✓ Index on price → sorted data, no sort needed

4. GROUP BY columns
   SELECT country, COUNT(*) FROM users GROUP BY country;
   ✓ Index on country → faster grouping

5. Foreign key columns
   orders.user_id references users.id
   ✓ Index on orders.user_id speeds up joins


✗ INDEXES DON'T HELP:
─────────────────────

1. Small tables (< 1000 rows)
   SELECT * FROM settings;
   ✗ Full scan faster than index lookup

2. Columns with low selectivity (few distinct values)
   SELECT * FROM users WHERE gender = 'M';
   ✗ Returns 50% of rows → Full scan may be faster
   ✗ Index not selective enough

3. Functions on indexed column
   SELECT * FROM users WHERE LOWER(email) = 'alice@x.com';
   ✗ Function prevents index use
   ✓ Fix: Create index on LOWER(email)

4. Queries returning large % of table
   SELECT * FROM users WHERE age > 18;
   ✗ Returns 95% of rows → Index not helpful

5. Leading wildcard in LIKE
   SELECT * FROM users WHERE email LIKE '%@gmail.com';
   ✗ Cannot use index with leading wildcard
   ✓ Works: email LIKE 'alice%' (no leading wildcard)


SELECTIVITY RULE:
─────────────────

Index useful when query returns < 10-15% of rows

Good:  WHERE user_id = 123 (returns 1 row)      ✓
Good:  WHERE status = 'premium' (returns 5%)    ✓
Bad:   WHERE active = true (returns 90%)        ✗
Bad:   WHERE age > 18 (returns 95%)             ✗
```

---

## Index Maintenance Cost

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INDEX TRADE-OFFS                                      │
└─────────────────────────────────────────────────────────────────────────┘

READS vs WRITES:
────────────────

┌─────────────────────────────────────────────────────────────┐
│                      READ Operation                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Without Index:                                             │
│    • Slow ❌ (scan all rows)                                │
│                                                             │
│  With Index:                                                │
│    • Fast ✓ (direct lookup)                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                     WRITE Operation                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Without Index:                                             │
│    INSERT INTO users VALUES (1, 'Alice', 'alice@x.com');   │
│    • Fast ✓ (just insert row)                               │
│    • Time: 1ms                                              │
│                                                             │
│  With 5 Indexes:                                            │
│    INSERT INTO users VALUES (1, 'Alice', 'alice@x.com');   │
│    • Insert row                                             │
│    • Update index 1 (id)                                    │
│    • Update index 2 (email)                                 │
│    • Update index 3 (name)                                  │
│    • Update index 4 (age)                                   │
│    • Update index 5 (created_at)                            │
│    • Time: 5ms (5x slower) ❌                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘


STORAGE COST:
─────────────

Table: 1 million rows × 1 KB = 1 GB

Each index:
• 10-20% of table size
• 5 indexes = 500 MB extra storage

Total: 1 GB (table) + 500 MB (indexes) = 1.5 GB


UPDATE EXAMPLE:
───────────────

UPDATE users SET email = 'new@example.com' WHERE id = 123;

Without index on email:
  1. Update row
  Time: 1ms

With index on email:
  1. Update row
  2. Delete old email from index
  3. Insert new email into index
  Time: 3ms (3x slower)


GOLDEN RULE:
────────────
• More indexes = Faster reads, Slower writes
• Too many indexes = More storage, Slower inserts/updates
• Balance based on read/write ratio

Read-heavy (90% reads): More indexes ✓
Write-heavy (90% writes): Fewer indexes ✓
```

---

## Index Best Practices

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INDEX BEST PRACTICES                                  │
└─────────────────────────────────────────────────────────────────────────┘

1. INDEX FOREIGN KEYS
─────────────────────

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create index on foreign key
CREATE INDEX idx_user_id ON orders(user_id);

Why?
• Speeds up joins: SELECT * FROM orders o JOIN users u ON o.user_id = u.id
• Speeds up cascading deletes/updates


2. INDEX WHERE CLAUSE COLUMNS
──────────────────────────────

Common query:
SELECT * FROM orders WHERE status = 'pending' AND created_at > '2024-01-01';

-- Create composite index
CREATE INDEX idx_status_date ON orders(status, created_at);

Why?
• Most common query pattern
• Both columns used together


3. USE EXPLAIN TO VERIFY
────────────────────────

EXPLAIN SELECT * FROM users WHERE email = 'alice@x.com';

Look for:
✓ Index Scan (good)
✗ Seq Scan (bad - not using index)

Example output:
┌────────────────────────────────────────┐
│ Index Scan using idx_email             │  ← Good!
│ Index Cond: (email = 'alice@x.com')    │
└────────────────────────────────────────┘


4. DON'T OVER-INDEX
───────────────────

Bad: 10 indexes on one table
• Slow inserts/updates
• Wasted storage
• Database spends time maintaining unused indexes

Keep: 3-5 indexes per table
✓ Primary key
✓ Foreign keys
✓ Most common WHERE/JOIN columns


5. COMPOSITE INDEX COLUMN ORDER
────────────────────────────────

CREATE INDEX idx_name_age ON users(name, age);

Works for:
✓ WHERE name = 'Alice'
✓ WHERE name = 'Alice' AND age = 25

Doesn't work for:
✗ WHERE age = 25  (age not leftmost)

Rule: Most selective column first
• If name more unique than age → (name, age) ✓
• If age more unique than name → (age, name) ✓


6. INDEX SELECTIVE COLUMNS
──────────────────────────

High selectivity (unique values): ✓ Good for indexing
• email (unique)
• user_id (unique)
• order_id (unique)

Low selectivity (few distinct values): ✗ Bad for indexing
• gender (M/F)
• active (true/false)
• status (pending/complete/cancelled)

Exception: Partial index
CREATE INDEX idx_pending ON orders(status) WHERE status = 'pending';
• Only 5% of orders pending → Selective! ✓


7. MONITOR INDEX USAGE
──────────────────────

PostgreSQL:
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;  -- Unused indexes

Drop unused indexes:
DROP INDEX idx_unused;


8. AVOID INDEXES ON SMALL TABLES
─────────────────────────────────

Table with < 1000 rows:
✗ Don't index (overhead not worth it)
✓ Full scan is fast enough


9. USE COVERING INDEXES FOR HOT QUERIES
────────────────────────────────────────

Query: SELECT name, age FROM users WHERE email = 'alice@x.com';

Instead of:
CREATE INDEX idx_email ON users(email);

Use:
CREATE INDEX idx_email_covering ON users(email, name, age);

Why?
• Index contains all needed columns
• No table access needed (faster)


10. REBUILD FRAGMENTED INDEXES
───────────────────────────────

Over time, indexes become fragmented (inserts/deletes)

PostgreSQL:
REINDEX INDEX idx_email;

MySQL:
OPTIMIZE TABLE users;

Do this: Monthly or quarterly
```

---

## Common Index Pitfalls

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMMON INDEX MISTAKES                                 │
└─────────────────────────────────────────────────────────────────────────┘

❌ MISTAKE 1: Using Functions on Indexed Columns
────────────────────────────────────────────────

SELECT * FROM users WHERE LOWER(email) = 'alice@example.com';
                          ─────────────
                          ↑ Function prevents index use!

Fix: Create functional index
CREATE INDEX idx_email_lower ON users(LOWER(email));


❌ MISTAKE 2: Using OR with Different Columns
──────────────────────────────────────────────

SELECT * FROM users WHERE name = 'Alice' OR age = 25;
                          ──────────────────────────
                          ↑ Cannot use single index efficiently

Fix: Use UNION
SELECT * FROM users WHERE name = 'Alice'
UNION
SELECT * FROM users WHERE age = 25;


❌ MISTAKE 3: Implicit Type Conversion
───────────────────────────────────────

Table: user_id VARCHAR(50) with index
Query: SELECT * FROM users WHERE user_id = 123;
                                              ───
                                              ↑ Number, not string!

Database converts: WHERE CAST(user_id AS INT) = 123
• Function on indexed column → Index not used!

Fix: Use correct type
WHERE user_id = '123'


❌ MISTAKE 4: NOT using Index on Inequality
────────────────────────────────────────────

Query: SELECT * FROM users WHERE status != 'deleted';

• May not use index (returns most rows)
• Full scan faster!

Fix: Use positive condition
WHERE status IN ('active', 'pending', 'suspended')


❌ MISTAKE 5: Indexing Everything
──────────────────────────────────

Table: users with 20 columns
Indexes: 15 indexes on every column

Result:
• INSERT/UPDATE extremely slow
• Wasted storage (5 GB for indexes!)
• Most indexes never used

Fix: Index only frequently queried columns (3-5 indexes)


❌ MISTAKE 6: Wrong Column Order in Composite Index
────────────────────────────────────────────────────

Query: WHERE age = 25 AND name = 'Alice';
Index: idx_name_age (name, age)

Problem: If you only query by age, index not used!

Fix: Index should match most common query pattern
• Query by age only? → (age, name)
• Query by name only? → (name, age)
• Query by both? → Either works, but put most selective first
```

---

## Real-World Example: E-commerce System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    E-COMMERCE INDEXING STRATEGY                          │
└─────────────────────────────────────────────────────────────────────────┘

USERS TABLE:
────────────

CREATE TABLE users (
    id BIGINT PRIMARY KEY,              -- Clustered index (auto)
    email VARCHAR(255) UNIQUE,          -- Unique index (auto)
    phone VARCHAR(20),
    name VARCHAR(100),
    created_at TIMESTAMP
);

Indexes:
--------
✓ PRIMARY KEY (id) - Auto-created
✓ UNIQUE (email) - Auto-created
✓ CREATE INDEX idx_phone ON users(phone);
  • Why? Login by phone common
✗ Don't index 'name' (rarely queried alone)

Common queries:
• SELECT * FROM users WHERE email = ?  ✓ Uses unique index
• SELECT * FROM users WHERE phone = ?  ✓ Uses idx_phone
• SELECT * FROM users WHERE id = ?     ✓ Uses primary key


PRODUCTS TABLE:
───────────────

CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    category_id INT,
    price DECIMAL(10,2),
    stock INT,
    created_at TIMESTAMP
);

Indexes:
--------
✓ PRIMARY KEY (id)
✓ CREATE INDEX idx_category ON products(category_id);
  • Why? Filter by category common
✓ CREATE INDEX idx_category_price ON products(category_id, price);
  • Why? "Show laptops under $1000"
✗ Don't index 'name' alone (use full-text search instead)
✓ CREATE FULLTEXT INDEX idx_name_fulltext ON products(name);

Common queries:
• SELECT * FROM products WHERE category_id = ?
  ✓ Uses idx_category

• SELECT * FROM products WHERE category_id = ? AND price < 1000
  ✓ Uses idx_category_price

• SELECT * FROM products WHERE name LIKE '%laptop%'
  ✓ Uses idx_name_fulltext


ORDERS TABLE:
─────────────

CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    user_id BIGINT,
    status VARCHAR(50),
    total_amount DECIMAL(10,2),
    created_at TIMESTAMP
);

Indexes:
--------
✓ PRIMARY KEY (id)
✓ CREATE INDEX idx_user_id ON orders(user_id);
  • Why? "Show my orders" (foreign key)
✓ CREATE INDEX idx_status_created ON orders(status, created_at);
  • Why? "Show pending orders from last week"
✓ CREATE INDEX idx_created ON orders(created_at DESC);
  • Why? "Recent orders" (sorted by date)

Common queries:
• SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
  ✓ Uses idx_user_id + sorted by created_at

• SELECT * FROM orders WHERE status = 'pending' AND created_at > ?
  ✓ Uses idx_status_created

• SELECT * FROM orders WHERE id = ?
  ✓ Uses primary key


ORDER_ITEMS TABLE:
──────────────────

CREATE TABLE order_items (
    id BIGINT PRIMARY KEY,
    order_id BIGINT,
    product_id BIGINT,
    quantity INT,
    price DECIMAL(10,2)
);

Indexes:
--------
✓ PRIMARY KEY (id)
✓ CREATE INDEX idx_order_id ON order_items(order_id);
  • Why? JOIN with orders (foreign key)
✓ CREATE INDEX idx_product_id ON order_items(product_id);
  • Why? "Which orders contain this product?"

Common queries:
• SELECT * FROM order_items WHERE order_id = ?
  ✓ Uses idx_order_id (fetch items for order)

• SELECT * FROM order_items WHERE product_id = ?
  ✓ Uses idx_product_id (product sales report)


SUMMARY:
────────
Total indexes: 12 across 4 tables
• Primary keys: 4 (auto)
• Unique constraints: 1 (email)
• Foreign key indexes: 3 (user_id, order_id, product_id)
• Query optimization: 4 (category_price, status_created, etc.)

Read/Write ratio: 90% reads, 10% writes
• Index overhead acceptable for read performance
```

---

## Index Monitoring & Optimization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MONITOR INDEX PERFORMANCE                             │
└─────────────────────────────────────────────────────────────────────────┘

POSTGRESQL:
───────────

1. Find unused indexes:
   ────────────────────
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
   FROM pg_stat_user_indexes
   WHERE idx_scan = 0
   ORDER BY pg_relation_size(indexrelid) DESC;

   Output:
   ┌────────────┬───────────┬─────────────┬──────────┐
   │ table      │ index     │ scans    │ size     │
   ├────────────┼───────────┼──────────┼──────────┤
   │ users      │ idx_name  │ 0        │ 50 MB    │  ← Drop this!
   │ orders     │ idx_tmp   │ 0        │ 100 MB   │  ← Drop this!
   └────────────┴───────────┴──────────┴──────────┘


2. Find missing indexes (slow queries):
   ────────────────────────────────────
   SELECT query, calls, mean_time, total_time
   FROM pg_stat_statements
   WHERE mean_time > 1000  -- Slower than 1 second
   ORDER BY total_time DESC
   LIMIT 10;


3. Index bloat (fragmentation):
   ────────────────────────────
   SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
   FROM pg_tables
   WHERE schemaname = 'public';

   Rebuild if needed:
   REINDEX INDEX idx_email;


MYSQL:
──────

1. Find unused indexes:
   ────────────────────
   SELECT * FROM sys.schema_unused_indexes;


2. Explain query plan:
   ───────────────────
   EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';

   Output:
   ┌────┬─────────┬─────────────────┬──────┐
   │ id │ type    │ key             │ rows │
   ├────┼─────────┼─────────────────┼──────┤
   │ 1  │ ref     │ idx_email       │ 1    │  ← Using index ✓
   └────┴─────────┴─────────────────┴──────┘

   Bad output:
   ┌────┬─────────┬─────────────────┬──────────┐
   │ id │ type    │ key             │ rows     │
   ├────┼─────────┼─────────────────┼──────────┤
   │ 1  │ ALL     │ NULL            │ 1000000  │  ← Full scan ❌
   └────┴─────────┴─────────────────┴──────────┘


3. Optimize table (rebuild indexes):
   ──────────────────────────────────
   OPTIMIZE TABLE users;
```

---

## System Design Interview Answer

**Question: "How do database indexes work and when should you use them?"**

**Answer:**

"Database indexes are data structures that speed up data retrieval, similar to a book's index. Without an index, the database performs a full table scan, checking every row. With an index, it can jump directly to matching rows.

**How they work:**
Most databases use **B-Tree indexes**:
- Tree structure with sorted keys
- Each node points to child nodes or table rows
- Lookup time: O(log n) instead of O(n)
- For 1 million rows: ~20 comparisons vs 1 million

**Types:**
1. **Primary Key** (clustered): Data physically sorted by this column
2. **Secondary indexes**: Separate structure pointing to rows
3. **Composite indexes**: Multiple columns (name, age)
4. **Unique indexes**: Enforces uniqueness + speeds up lookups

**When to use:**
- WHERE clauses with high selectivity (returns < 10% of rows)
- JOIN columns (foreign keys)
- ORDER BY columns
- Frequently queried columns

**When NOT to use:**
- Small tables (< 1000 rows)
- Low selectivity columns (gender: M/F returns 50%)
- Write-heavy tables (indexes slow down INSERT/UPDATE)
- Columns with functions: WHERE LOWER(email) = 'x' won't use index

**Trade-offs:**
- **Benefit**: 100-1000x faster reads
- **Cost**: Slower writes (must update index), extra storage (10-20% per index)

**Example:**
In e-commerce, I'd index:
- users.email (login queries)
- orders.user_id (foreign key for joins)
- orders.status + created_at (composite for 'show pending orders')
- products.category_id (filter by category)

But I wouldn't index everything - too many indexes slow down writes. Typically 3-5 indexes per table is optimal.

**Monitoring:**
I use EXPLAIN to verify queries use indexes and monitor unused indexes with pg_stat_user_indexes. Drop unused indexes to reduce write overhead."

---

## Key Takeaways

✓ **Indexes speed up reads**: 100-1000x faster for selective queries

✓ **B-Tree most common**: Supports range queries, ORDER BY

✓ **Hash indexes**: O(1) for exact match, but limited use

✓ **Index foreign keys**: Essential for joins

✓ **Composite indexes**: Column order matters (left-most prefix rule)

✓ **Trade-off**: Faster reads vs slower writes

✓ **Don't over-index**: 3-5 indexes per table typical

✓ **Monitor with EXPLAIN**: Verify queries use indexes

✓ **Drop unused indexes**: Reduce write overhead

✓ **Selectivity matters**: Index helpful when returns < 10% rows
