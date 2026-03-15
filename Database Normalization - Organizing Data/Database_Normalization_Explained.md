# Database Normalization - Organizing Data Efficiently

## What is Database Normalization?

**Normalization** is the process of organizing database tables to **reduce redundancy** (duplicate data) and **improve data integrity** (consistency).

Think of it like **organizing a messy closet** - group similar items together, eliminate duplicates, and make things easy to find.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    UNNORMALIZED vs NORMALIZED                            │
└─────────────────────────────────────────────────────────────────────────┘

UNNORMALIZED (Bad - Redundant Data):
─────────────────────────────────────

orders table:
┌────────┬───────────┬──────────────┬──────────┬────────────────┬─────────┐
│order_id│ user_name │ user_email   │ product  │ product_price  │ quantity│
├────────┼───────────┼──────────────┼──────────┼────────────────┼─────────┤
│ 1      │ Alice     │ alice@x.com  │ Laptop   │ 999            │ 1       │
│ 2      │ Alice     │ alice@x.com  │ Mouse    │ 25             │ 2       │
│ 3      │ Bob       │ bob@x.com    │ Laptop   │ 999            │ 1       │
│ 4      │ Alice     │ alice@x.com  │ Keyboard │ 75             │ 1       │
└────────┴───────────┴──────────────┴──────────┴────────────────┴─────────┘
           ─────────────────────────  ──────────────────────
           ↑ Duplicate!               ↑ Duplicate!

Problems:
❌ Alice's data repeated 3 times (waste of space)
❌ Update Alice's email → Must update 3 rows (error-prone)
❌ If email update misses one row → Data inconsistency!
❌ Laptop price stored twice → If price changes, must update all


NORMALIZED (Good - No Redundancy):
───────────────────────────────────

users table:
┌─────────┬───────────┬──────────────┐
│ user_id │ name      │ email        │
├─────────┼───────────┼──────────────┤
│ 1       │ Alice     │ alice@x.com  │  ← Stored once!
│ 2       │ Bob       │ bob@x.com    │
└─────────┴───────────┴──────────────┘

products table:
┌────────────┬──────────┬───────┐
│ product_id │ name     │ price │
├────────────┼──────────┼───────┤
│ 1          │ Laptop   │ 999   │  ← Stored once!
│ 2          │ Mouse    │ 25    │
│ 3          │ Keyboard │ 75    │
└────────────┴──────────┴───────┘

orders table:
┌────────┬─────────┬────────────┬──────────┐
│order_id│ user_id │ product_id │ quantity │
├────────┼─────────┼────────────┼──────────┤
│ 1      │ 1       │ 1          │ 1        │  ← References!
│ 2      │ 1       │ 2          │ 2        │
│ 3      │ 2       │ 1          │ 1        │
│ 4      │ 1       │ 3          │ 1        │
└────────┴─────────┴────────────┴──────────┘
         ↑         ↑
         Foreign Keys (references to other tables)

Benefits:
✓ Alice's data stored once (update in one place)
✓ Laptop price stored once (consistent)
✓ Less storage (no duplicates)
✓ Data integrity (email update in one place)
```

---

## Normal Forms (1NF, 2NF, 3NF)

### First Normal Form (1NF)

**Rule:** Each column must contain **atomic values** (single value, not list). No repeating groups.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FIRST NORMAL FORM (1NF)                               │
└─────────────────────────────────────────────────────────────────────────┘

❌ VIOLATES 1NF (Non-atomic values):
─────────────────────────────────────

employees table:
┌────┬───────┬──────────────────────────────┬─────────────────────┐
│ id │ name  │ phone_numbers                │ skills              │
├────┼───────┼──────────────────────────────┼─────────────────────┤
│ 1  │ Alice │ 555-1234, 555-5678           │ Java, Python, SQL   │
│ 2  │ Bob   │ 555-9999                     │ JavaScript, React   │
└────┴───────┴──────────────────────────────┴─────────────────────┘
              ─────────────────────────────  ─────────────────────
              ↑ Multiple values in one cell! ↑ Multiple values!

Problems:
• How to search for employee with skill "Python"?
• How to add a new phone number?


✓ SATISFIES 1NF (Atomic values):
─────────────────────────────────

employees table:
┌────┬───────┐
│ id │ name  │
├────┼───────┤
│ 1  │ Alice │
│ 2  │ Bob   │
└────┴───────┘

employee_phones table:
┌────┬─────────────┬──────────────┐
│ id │ employee_id │ phone_number │
├────┼─────────────┼──────────────┤
│ 1  │ 1           │ 555-1234     │  ← One value per cell
│ 2  │ 1           │ 555-5678     │
│ 3  │ 2           │ 555-9999     │
└────┴─────────────┴──────────────┘

employee_skills table:
┌────┬─────────────┬────────────┐
│ id │ employee_id │ skill      │
├────┼─────────────┼────────────┤
│ 1  │ 1           │ Java       │  ← One value per cell
│ 2  │ 1           │ Python     │
│ 3  │ 1           │ SQL        │
│ 4  │ 2           │ JavaScript │
│ 5  │ 2           │ React      │
└────┴─────────────┴────────────┘

✓ Each column has single value
✓ Can easily query: "Find employees with Python skill"
✓ Can easily add/remove skills

1NF Summary:
────────────
✓ Atomic values (no lists)
✓ No repeating groups
✓ Primary key defined
```

### Second Normal Form (2NF)

**Rule:** Must be in 1NF + **No partial dependencies** (non-key columns must depend on entire primary key, not part of it).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SECOND NORMAL FORM (2NF)                              │
└─────────────────────────────────────────────────────────────────────────┘

❌ VIOLATES 2NF (Partial dependency):
──────────────────────────────────────

order_items table (composite primary key: order_id + product_id):
┌──────────┬────────────┬──────────────┬───────┬──────────┐
│ order_id │ product_id │ product_name │ price │ quantity │
├──────────┼────────────┼──────────────┼───────┼──────────┤
│ 1        │ 101        │ Laptop       │ 999   │ 1        │
│ 1        │ 102        │ Mouse        │ 25    │ 2        │
│ 2        │ 101        │ Laptop       │ 999   │ 1        │
│ 3        │ 103        │ Keyboard     │ 75    │ 1        │
└──────────┴────────────┴──────────────┴───────┴──────────┘
           └────────────┴──────────────┴───────┘
           Primary Key (composite)     ↑       ↑
                                       │       │
                              Depends only on product_id
                              (Partial dependency!)

Problem:
• product_name depends only on product_id (not entire PK)
• price depends only on product_id (not entire PK)
• quantity depends on BOTH order_id + product_id ✓

Partial dependency = Non-key attribute depends on part of composite key


✓ SATISFIES 2NF (No partial dependencies):
───────────────────────────────────────────

products table:
┌────────────┬──────────────┬───────┐
│ product_id │ product_name │ price │
├────────────┼──────────────┼───────┤
│ 101        │ Laptop       │ 999   │  ← Product info here
│ 102        │ Mouse        │ 25    │
│ 103        │ Keyboard     │ 75    │
└────────────┴──────────────┴───────┘

order_items table:
┌──────────┬────────────┬──────────┐
│ order_id │ product_id │ quantity │
├──────────┼────────────┼──────────┤
│ 1        │ 101        │ 1        │  ← Only relationship data
│ 1        │ 102        │ 2        │
│ 2        │ 101        │ 1        │
│ 3        │ 103        │ 1        │
└──────────┴────────────┴──────────┘

✓ All non-key columns depend on ENTIRE primary key
✓ Product details stored once in products table
✓ No duplication of product_name and price

2NF Summary:
────────────
✓ Must be in 1NF
✓ No partial dependencies
✓ Applies only to tables with composite keys
```

### Third Normal Form (3NF)

**Rule:** Must be in 2NF + **No transitive dependencies** (non-key columns must depend on primary key directly, not on other non-key columns).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THIRD NORMAL FORM (3NF)                               │
└─────────────────────────────────────────────────────────────────────────┘

❌ VIOLATES 3NF (Transitive dependency):
─────────────────────────────────────────

employees table:
┌─────────────┬───────────┬────────────┬──────────────────┐
│ employee_id │ name      │ dept_id    │ dept_name        │
├─────────────┼───────────┼────────────┼──────────────────┤
│ 1           │ Alice     │ 10         │ Engineering      │
│ 2           │ Bob       │ 10         │ Engineering      │
│ 3           │ Charlie   │ 20         │ Sales            │
│ 4           │ David     │ 10         │ Engineering      │
└─────────────┴───────────┴────────────┴──────────────────┘
              ↑                         ↑
              Primary Key               └─ Depends on dept_id
                                           (not directly on employee_id)

Problem:
• dept_name depends on dept_id
• dept_id depends on employee_id
• Therefore: dept_name → dept_id → employee_id (Transitive!)

Transitive dependency = A → B → C

Issues:
• "Engineering" stored multiple times (redundancy)
• Update dept name → Must update multiple rows
• If all employees leave dept → Lose dept name!


✓ SATISFIES 3NF (No transitive dependencies):
──────────────────────────────────────────────

employees table:
┌─────────────┬───────────┬─────────┐
│ employee_id │ name      │ dept_id │
├─────────────┼───────────┼─────────┤
│ 1           │ Alice     │ 10      │
│ 2           │ Bob       │ 10      │
│ 3           │ Charlie   │ 20      │
│ 4           │ David     │ 10      │
└─────────────┴───────────┴─────────┘
              ↑           ↑
              PK          Foreign Key

departments table:
┌─────────┬──────────────┐
│ dept_id │ dept_name    │
├─────────┼──────────────┤
│ 10      │ Engineering  │  ← Stored once!
│ 20      │ Sales        │
│ 30      │ Marketing    │
└─────────┴──────────────┘

✓ All non-key columns depend DIRECTLY on primary key
✓ No transitive dependencies
✓ Department name stored once
✓ Can update department name in one place

3NF Summary:
────────────
✓ Must be in 2NF
✓ No transitive dependencies
✓ Non-key columns depend only on primary key
```

---

## Normalization Process: Complete Example

```
┌─────────────────────────────────────────────────────────────────────────┐
│            NORMALIZATION: STEP-BY-STEP EXAMPLE                           │
└─────────────────────────────────────────────────────────────────────────┘

UNNORMALIZED (Messy spreadsheet):
──────────────────────────────────

student_courses table:
┌────────────┬───────────┬─────────────────────┬──────────────────────┬─────────────────────┐
│ student_id │ name      │ courses             │ instructors          │ instructor_emails   │
├────────────┼───────────┼─────────────────────┼──────────────────────┼─────────────────────┤
│ 1          │ Alice     │ Math, Physics       │ Dr. Smith, Dr. Jones │ smith@x, jones@x    │
│ 2          │ Bob       │ Math                │ Dr. Smith            │ smith@x             │
│ 3          │ Charlie   │ Physics, Chemistry  │ Dr. Jones, Dr. Brown │ jones@x, brown@x    │
└────────────┴───────────┴─────────────────────┴──────────────────────┴─────────────────────┘

Problems:
❌ Multiple values in cells (violates 1NF)
❌ Instructor info repeated (violates 2NF/3NF)
❌ Update Dr. Smith's email → Must update multiple rows
❌ Difficult to query: "Which students take Math?"


STEP 1: Convert to 1NF (Atomic values)
───────────────────────────────────────

student_courses table:
┌────────────┬───────────┬───────────┬──────────────┬──────────────────┐
│ student_id │ name      │ course    │ instructor   │ instructor_email │
├────────────┼───────────┼───────────┼──────────────┼──────────────────┤
│ 1          │ Alice     │ Math      │ Dr. Smith    │ smith@x          │
│ 1          │ Alice     │ Physics   │ Dr. Jones    │ jones@x          │
│ 2          │ Bob       │ Math      │ Dr. Smith    │ smith@x          │
│ 3          │ Charlie   │ Physics   │ Dr. Jones    │ jones@x          │
│ 3          │ Charlie   │ Chemistry │ Dr. Brown    │ brown@x          │
└────────────┴───────────┴───────────┴──────────────┴──────────────────┘

✓ Each cell has single value
❌ Still has redundancy (name repeated, instructor info repeated)


STEP 2: Convert to 2NF (Remove partial dependencies)
─────────────────────────────────────────────────────

Composite PK: (student_id, course)
• 'name' depends only on student_id (partial dependency!)
• 'instructor' depends only on course (partial dependency!)

Split into tables:

students table:
┌────────────┬───────────┐
│ student_id │ name      │
├────────────┼───────────┤
│ 1          │ Alice     │
│ 2          │ Bob       │
│ 3          │ Charlie   │
└────────────┴───────────┘

courses table:
┌───────────┬──────────────┬──────────────────┐
│ course_id │ course_name  │ instructor_name  │
├───────────┼──────────────┼──────────────────┤
│ 1         │ Math         │ Dr. Smith        │
│ 2         │ Physics      │ Dr. Jones        │
│ 3         │ Chemistry    │ Dr. Brown        │
└───────────┴──────────────┴──────────────────┘

enrollments table:
┌────────────┬───────────┐
│ student_id │ course_id │
├────────────┼───────────┤
│ 1          │ 1         │  (Alice → Math)
│ 1          │ 2         │  (Alice → Physics)
│ 2          │ 1         │  (Bob → Math)
│ 3          │ 2         │  (Charlie → Physics)
│ 3          │ 3         │  (Charlie → Chemistry)
└────────────┴───────────┘

✓ No partial dependencies
❌ Still has transitive dependency (instructor_email depends on instructor)


STEP 3: Convert to 3NF (Remove transitive dependencies)
────────────────────────────────────────────────────────

In courses table:
• instructor_email depends on instructor_name
• instructor_name depends on course_id
• Transitive: instructor_email → instructor_name → course_id

Split instructor info:

students table:
┌────────────┬───────────┐
│ student_id │ name      │
├────────────┼───────────┤
│ 1          │ Alice     │
│ 2          │ Bob       │
│ 3          │ Charlie   │
└────────────┴───────────┘

instructors table:
┌───────────────┬────────────────┬──────────────────┐
│ instructor_id │ name           │ email            │
├───────────────┼────────────────┼──────────────────┤
│ 1             │ Dr. Smith      │ smith@x          │
│ 2             │ Dr. Jones      │ jones@x          │
│ 3             │ Dr. Brown      │ brown@x          │
└───────────────┴────────────────┴──────────────────┘

courses table:
┌───────────┬──────────────┬───────────────┐
│ course_id │ course_name  │ instructor_id │
├───────────┼──────────────┼───────────────┤
│ 1         │ Math         │ 1             │
│ 2         │ Physics      │ 2             │
│ 3         │ Chemistry    │ 3             │
└───────────┴──────────────┴───────────────┘

enrollments table:
┌────────────┬───────────┐
│ student_id │ course_id │
├────────────┼───────────┤
│ 1          │ 1         │
│ 1          │ 2         │
│ 2          │ 1         │
│ 3          │ 2         │
│ 3          │ 3         │
└────────────┴───────────┘

✓ In 3NF (no transitive dependencies)
✓ No redundancy
✓ Update instructor email in one place
✓ Can query easily: "Which students take Math?"
  SELECT s.name FROM students s
  JOIN enrollments e ON s.student_id = e.student_id
  JOIN courses c ON e.course_id = c.course_id
  WHERE c.course_name = 'Math';
```

---

## Benefits vs Trade-offs

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NORMALIZATION BENEFITS                                │
└─────────────────────────────────────────────────────────────────────────┘

1. ELIMINATE REDUNDANCY
───────────────────────
Before: User name stored 100 times (100 orders)
After:  User name stored once (users table)
Savings: 99% less storage for user data


2. DATA INTEGRITY
─────────────────
Before: Update user email → Must update 100 rows (error-prone)
After:  Update user email → Update 1 row ✓
Consistency guaranteed!


3. EASIER UPDATES
─────────────────
Before: Change product price → Update all order records
After:  Change product price → Update once in products table


4. AVOID ANOMALIES
──────────────────

Update Anomaly:
• Before: Update user email in 99 rows, miss 1 → Inconsistency!
• After: Update once ✓

Insert Anomaly:
• Before: Can't add department without employee
• After: Can add department independently ✓

Delete Anomaly:
• Before: Delete last employee → Lose department info!
• After: Department info preserved ✓


┌─────────────────────────────────────────────────────────────────────────┐
│                    NORMALIZATION TRADE-OFFS                              │
└─────────────────────────────────────────────────────────────────────────┘

❌ DISADVANTAGE 1: More Joins
──────────────────────────────

Unnormalized (one query):
SELECT * FROM orders WHERE order_id = 123;
Fast! (no joins)

Normalized (multiple joins):
SELECT o.*, u.name, u.email, p.name, p.price
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id
WHERE o.order_id = 123;

Slower (3 table joins)

Impact: 3-5x slower for complex queries


❌ DISADVANTAGE 2: More Complex Queries
────────────────────────────────────────

Simple query becomes complex with multiple joins
Harder to understand and maintain


❌ DISADVANTAGE 3: More Tables to Manage
─────────────────────────────────────────

Before: 1 table
After:  4 tables (users, products, orders, order_items)

More foreign keys, more indexes, more complexity


WHEN TO DENORMALIZE:
────────────────────

Read-heavy applications where query speed critical:

• Reporting databases (data warehouse)
• Analytics dashboards
• Search results (Elasticsearch)
• Caching layers (Redis)

Example: Order history view
Instead of joining 4 tables each time:
CREATE TABLE order_history_denormalized AS
SELECT o.order_id, o.total,
       u.name as user_name,
       u.email as user_email,
       p.name as product_name
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id;

✓ Fast reads (no joins)
✗ Must refresh when data changes
```

---

## When to Normalize vs Denormalize

```
┌─────────────────────────────────────────────────────────────────────────┐
│                NORMALIZATION vs DENORMALIZATION                          │
└─────────────────────────────────────────────────────────────────────────┘

NORMALIZE (Use 3NF):
────────────────────

✓ OLTP (Transactional) systems
  • E-commerce checkout
  • Banking transactions
  • User management
  • Frequent updates

✓ Write-heavy applications
  • Need consistency
  • Frequent inserts/updates

✓ Small to medium data (<10M rows)
  • Joins not too expensive

Example: E-commerce order processing
  users → orders → order_items → products
  ✓ Updates frequent (order status, inventory)
  ✓ Consistency critical


DENORMALIZE (Trade consistency for speed):
───────────────────────────────────────────

✓ OLAP (Analytics) systems
  • Data warehouses
  • Business intelligence
  • Reporting dashboards

✓ Read-heavy applications
  • Product listings
  • Search results
  • News feeds
  • Social media timelines

✓ Large data (>100M rows)
  • Joins too expensive
  • Need fast queries

Example: Order history view
  order_id | user_name | user_email | product_name | price | quantity
  ✓ No joins needed
  ✓ Fast queries
  ✗ Duplicate data (acceptable)
  ✗ Stale data (refresh nightly)


HYBRID APPROACH (Best of both):
────────────────────────────────

Normalize write database (PostgreSQL)
  ✓ Consistency for transactions
  ✓ ACID guarantees

Denormalize read database (MongoDB/Elasticsearch)
  ✓ Fast queries
  ✓ Optimized for reads

Synchronize:
  Write DB → Event Bus → Read DB
  (Eventual consistency)

Example: E-commerce
  • Write: Normalized PostgreSQL (orders, users, products)
  • Read: Denormalized MongoDB (order_history with all joined data)
  • Sync: Kafka event stream updates MongoDB when PostgreSQL changes
```

---

## Real-World Example: E-commerce Database

```
┌─────────────────────────────────────────────────────────────────────────┐
│              E-COMMERCE DATABASE SCHEMA (3NF)                            │
└─────────────────────────────────────────────────────────────────────────┘

users table:
┌─────────┬───────────┬──────────────┬──────────┐
│ user_id │ name      │ email        │ password │
├─────────┼───────────┼──────────────┼──────────┤
│ 1       │ Alice     │ alice@x.com  │ ***      │
│ 2       │ Bob       │ bob@x.com    │ ***      │
└─────────┴───────────┴──────────────┴──────────┘

addresses table:
┌────────────┬─────────┬──────────────┬──────────────┬──────────┐
│ address_id │ user_id │ street       │ city         │ zip_code │
├────────────┼─────────┼──────────────┼──────────────┼──────────┤
│ 1          │ 1       │ 123 Main St  │ New York     │ 10001    │
│ 2          │ 1       │ 456 Oak Ave  │ Los Angeles  │ 90001    │
│ 3          │ 2       │ 789 Elm St   │ Chicago      │ 60601    │
└────────────┴─────────┴──────────────┴──────────────┴──────────┘

categories table:
┌─────────────┬─────────────────┐
│ category_id │ category_name   │
├─────────────┼─────────────────┤
│ 1           │ Electronics     │
│ 2           │ Clothing        │
│ 3           │ Books           │
└─────────────┴─────────────────┘

products table:
┌────────────┬──────────────┬─────────────┬───────┬───────┐
│ product_id │ name         │ category_id │ price │ stock │
├────────────┼──────────────┼─────────────┼───────┼───────┤
│ 1          │ Laptop       │ 1           │ 999   │ 50    │
│ 2          │ T-Shirt      │ 2           │ 25    │ 200   │
│ 3          │ Novel        │ 3           │ 15    │ 100   │
└────────────┴──────────────┴─────────────┴───────┴───────┘

orders table:
┌──────────┬─────────┬────────────┬──────────────┬────────┬────────────┐
│ order_id │ user_id │ address_id │ total_amount │ status │ created_at │
├──────────┼─────────┼────────────┼──────────────┼────────┼────────────┤
│ 1        │ 1       │ 1          │ 1024         │ paid   │ 2024-03-15 │
│ 2        │ 2       │ 3          │ 999          │ pending│ 2024-03-16 │
└──────────┴─────────┴────────────┴──────────────┴────────┴────────────┘

order_items table:
┌──────────┬────────────┬──────────┬───────┐
│ order_id │ product_id │ quantity │ price │
├──────────┼────────────┼──────────┼───────┤
│ 1        │ 1          │ 1        │ 999   │  (Laptop)
│ 1        │ 2          │ 1        │ 25    │  (T-Shirt)
│ 2        │ 1          │ 1        │ 999   │  (Laptop)
└──────────┴────────────┴──────────┴───────┘

✓ 3NF: No redundancy
✓ Users stored once
✓ Products stored once
✓ Can have multiple addresses per user
✓ Can add category without products


Query: Get order details with all info
───────────────────────────────────────

SELECT
    o.order_id,
    u.name as user_name,
    u.email,
    a.street,
    a.city,
    p.name as product_name,
    oi.quantity,
    oi.price
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN addresses a ON o.address_id = a.address_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_id = 1;

Result:
┌──────────┬───────────┬─────────────┬─────────────┬──────────┬──────────────┬──────────┬───────┐
│ order_id │ user_name │ email       │ street      │ city     │ product_name │ quantity │ price │
├──────────┼───────────┼─────────────┼─────────────┼──────────┼──────────────┼──────────┼───────┤
│ 1        │ Alice     │ alice@x.com │ 123 Main St │ New York │ Laptop       │ 1        │ 999   │
│ 1        │ Alice     │ alice@x.com │ 123 Main St │ New York │ T-Shirt      │ 1        │ 25    │
└──────────┴───────────┴─────────────┴─────────────┴──────────┴──────────────┴──────────┴───────┘

5 table joins, but data is consistent and no redundancy ✓
```

---

## Denormalization for Performance

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DENORMALIZATION EXAMPLE                               │
└─────────────────────────────────────────────────────────────────────────┘

Problem: Order history page slow (5 table joins)

Solution: Create denormalized view/table

order_history_view (Materialized View):
┌──────────┬───────────┬─────────────┬──────────────┬──────────┬──────────┐
│ order_id │ user_name │ user_email  │ product_name │ quantity │ total    │
├──────────┼───────────┼─────────────┼──────────────┼──────────┼──────────┤
│ 1        │ Alice     │ alice@x.com │ Laptop       │ 1        │ 1024     │
│ 2        │ Bob       │ bob@x.com   │ Laptop       │ 1        │ 999      │
└──────────┴───────────┴─────────────┴──────────────┴──────────┴──────────┘
           ─────────────────────────  ──────────────
           ↑ Denormalized!            ↑ Denormalized!

Query (fast, no joins):
SELECT * FROM order_history_view WHERE user_name = 'Alice';

Trade-off:
✓ Fast queries (no joins)
✗ Duplicate data (user_name, user_email repeated)
✗ Must refresh when orders/users change

Refresh strategy:
• Real-time: Update view on every order change
• Batch: Refresh nightly (acceptable for reports)
• Incremental: Refresh only changed rows
```

---

## System Design Interview Answer

**Question: "What is database normalization and when should you use it?"**

**Answer:**

"Database normalization is the process of organizing tables to reduce data redundancy and improve data integrity. It involves applying normal forms (1NF, 2NF, 3NF) to eliminate duplicate data.

**Normal Forms:**
- **1NF**: Each column has atomic values (no lists). Example: Split 'skills: Java, Python' into separate rows.
- **2NF**: No partial dependencies. Non-key columns depend on entire primary key. Example: In order_items table with composite key (order_id, product_id), product_name depends only on product_id, so extract to products table.
- **3NF**: No transitive dependencies. Non-key columns depend directly on primary key. Example: If dept_name depends on dept_id, which depends on employee_id, extract departments to separate table.

**Benefits:**
- **Eliminate redundancy**: User data stored once, not in every order
- **Data integrity**: Update user email in one place, not 100 places
- **Avoid anomalies**: Can add department without employee, can't lose department when last employee leaves

**Trade-offs:**
- **More joins**: Must join 3-5 tables for complex queries (slower)
- **Query complexity**: Simple queries become complex
- **Performance**: Normalized queries 3-5x slower due to joins

**When to Normalize:**
- **OLTP systems**: Order processing, user management (frequent updates)
- **Write-heavy**: Consistency critical
- **Small/medium data**: Joins not too expensive

**When to Denormalize:**
- **OLAP systems**: Data warehouses, analytics (read-heavy)
- **Large data**: Joins too expensive (100M+ rows)
- **Performance critical**: Product listings, search results

**Hybrid Approach:**
In my e-commerce design:
- **Write database**: Normalized PostgreSQL (users, orders, products) - consistency
- **Read database**: Denormalized MongoDB (order_history with all joined data) - speed
- **Sync**: Kafka events update MongoDB when PostgreSQL changes

This gives both consistency for transactions and speed for queries."

---

## Key Takeaways

✓ **1NF**: Atomic values, no repeating groups

✓ **2NF**: No partial dependencies (composite key tables)

✓ **3NF**: No transitive dependencies (most common in practice)

✓ **Benefits**: Eliminate redundancy, improve integrity, avoid anomalies

✓ **Trade-offs**: More joins, slower queries, increased complexity

✓ **Normalize for**: Transactions (OLTP), write-heavy, consistency

✓ **Denormalize for**: Analytics (OLAP), read-heavy, performance

✓ **Hybrid**: Normalize writes, denormalize reads

✓ **Goal**: Balance consistency vs performance based on use case
