# ACID Transactions - Database Consistency Explained

## What are ACID Transactions?

**ACID** is a set of properties that guarantee database transactions are processed reliably. ACID stands for:
- **A**tomicity
- **C**onsistency
- **I**solation
- **D**urability

Think of it as a **contract** that the database makes with you: "Your data will be safe and correct."

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ACID PROPERTIES                                  │
└─────────────────────────────────────────────────────────────────────────┘

   ┌──────────────┐       ┌──────────────┐
   │  ATOMICITY   │       │ CONSISTENCY  │
   │              │       │              │
   │ All or       │       │ Valid state  │
   │ Nothing      │       │ always       │
   └──────────────┘       └──────────────┘
          │                      │
          │                      │
          └──────────┬───────────┘
                     │
              ┌──────▼──────┐
              │    ACID     │
              │ Transaction │
              └──────┬──────┘
                     │
          ┌──────────┴───────────┐
          │                      │
   ┌──────▼──────┐       ┌──────▼──────┐
   │  ISOLATION  │       │ DURABILITY  │
   │             │       │             │
   │ Concurrent  │       │ Permanent   │
   │ txns don't  │       │ after       │
   │ interfere   │       │ commit      │
   └─────────────┘       └─────────────┘
```

---

## 1. ATOMICITY (All or Nothing)

**Simple Explanation:** A transaction is an **all-or-nothing** operation. Either all steps succeed, or none of them happen. No partial completion.

### Real-World Example: Bank Transfer

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ATOMICITY - BANK TRANSFER                             │
└─────────────────────────────────────────────────────────────────────────┘

Scenario: Transfer $100 from Alice to Bob

Alice's Account          Transaction              Bob's Account
Balance: $500                                     Balance: $300
     │                                                  │
     │   BEGIN TRANSACTION                             │
     │   ──────────────────                            │
     │                                                  │
     │   Step 1: Deduct $100 from Alice                │
     │   ────────────────────────────                  │
     ▼                                                  │
Balance: $400            ✓ Success                     │
     │                                                  │
     │   Step 2: Add $100 to Bob                       │
     │   ─────────────────────                         │
     │                                                  ▼
     │                   ✓ Success             Balance: $400
     │                                                  │
     │   COMMIT                                         │
     │   ──────                                         │
     ▼                                                  ▼
Final: $400                                       Final: $400
✓ Both steps completed successfully


WHAT IF STEP 2 FAILS?
──────────────────────

Alice's Account          Transaction              Bob's Account
Balance: $500                                     Balance: $300
     │                                                  │
     │   BEGIN TRANSACTION                             │
     │   Step 1: Deduct $100 from Alice                │
     ▼                                                  │
Balance: $400            ✓ Success                     │
     │                                                  │
     │   Step 2: Add $100 to Bob                       │
     │   ─────────────────────                         │
     │                   ✗ ERROR!                      │
     │                   (Network timeout)             │
     │                                                  │
     │   ROLLBACK                                       │
     │   ────────                                       │
     │   (Undo Step 1)                                 │
     ▼                                                  ▼
Balance: $500            ← Restored          Balance: $300
✓ Transaction rolled back - no money lost!
```

### Code Example

```java
@Service
public class BankService {

    @Transactional  // ← This ensures ATOMICITY
    public void transferMoney(Long fromId, Long toId, BigDecimal amount) {

        // Step 1: Deduct from sender
        Account fromAccount = accountRepo.findById(fromId);
        fromAccount.setBalance(fromAccount.getBalance().subtract(amount));
        accountRepo.save(fromAccount);

        // Simulate error
        if (amount.compareTo(new BigDecimal("1000")) > 0) {
            throw new RuntimeException("Transfer limit exceeded!");
            // ← This will ROLLBACK the entire transaction
            //    Step 1 will be undone automatically
        }

        // Step 2: Add to receiver
        Account toAccount = accountRepo.findById(toId);
        toAccount.setBalance(toAccount.getBalance().add(amount));
        accountRepo.save(toAccount);

        // If we reach here, COMMIT happens automatically
    }
}
```

**Key Point:** Without `@Transactional`, Step 1 would be permanent even if Step 2 fails. Money would disappear! ❌

---

## 2. CONSISTENCY (Valid State Always)

**Simple Explanation:** The database must remain in a **valid state** before and after the transaction. All rules (constraints, triggers, cascades) must be satisfied.

### Real-World Example: E-commerce Order

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONSISTENCY - ORDER PLACEMENT                         │
└─────────────────────────────────────────────────────────────────────────┘

Database Rules (Constraints):
  1. order.total_price = SUM(order_items.price)
  2. inventory.stock >= 0 (cannot be negative)
  3. user.balance >= order.total_price


VALID TRANSACTION (Maintains Consistency):
──────────────────────────────────────────

State BEFORE Transaction:
┌─────────────────────────────────────────────────────────────┐
│ Users Table                                                 │
│ user_id: 1, name: "Alice", balance: $500                   │
│                                                             │
│ Inventory Table                                             │
│ product_id: 101, name: "Laptop", stock: 10                 │
│                                                             │
│ Orders Table                                                │
│ (empty)                                                     │
└─────────────────────────────────────────────────────────────┘

Transaction: Alice buys 1 Laptop for $400
───────────────────────────────────────────

BEGIN TRANSACTION;

  // Check balance: $500 >= $400 ✓
  // Check stock: 10 >= 1 ✓

  INSERT INTO orders VALUES (1, 1, 101, 1, 400);
  UPDATE users SET balance = 100 WHERE user_id = 1;
  UPDATE inventory SET stock = 9 WHERE product_id = 101;

  // Validate constraints:
  // ✓ user.balance = $100 (>= 0)
  // ✓ inventory.stock = 9 (>= 0)
  // ✓ order.price = $400 (correct)

COMMIT;

State AFTER Transaction:
┌─────────────────────────────────────────────────────────────┐
│ Users Table                                                 │
│ user_id: 1, name: "Alice", balance: $100 ✓                 │
│                                                             │
│ Inventory Table                                             │
│ product_id: 101, name: "Laptop", stock: 9 ✓                │
│                                                             │
│ Orders Table                                                │
│ order_id: 1, user_id: 1, product_id: 101, price: $400 ✓    │
└─────────────────────────────────────────────────────────────┘

✓ All constraints satisfied - Database is CONSISTENT


INVALID TRANSACTION (Violates Consistency):
────────────────────────────────────────────

Transaction: Alice tries to buy 15 Laptops (only 10 in stock)

BEGIN TRANSACTION;
  INSERT INTO orders VALUES (1, 1, 101, 15, 6000);
  UPDATE inventory SET stock = -5 WHERE product_id = 101;
  // ✗ stock = -5 (violates stock >= 0 constraint)

ROLLBACK;  ← Database automatically rejects this transaction

✓ Database remains CONSISTENT
```

---

## 3. ISOLATION (Concurrent Transactions Don't Interfere)

**Simple Explanation:** Multiple transactions can run **concurrently** without affecting each other. Each transaction feels like it's running **alone**.

### Isolation Levels

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       ISOLATION LEVELS                                   │
└─────────────────────────────────────────────────────────────────────────┘

        Strongest Isolation ▲
                            │
        ┌───────────────────┴──────────────────┐
        │  SERIALIZABLE                        │  Slowest, Safest
        │  (Complete isolation)                │
        ├──────────────────────────────────────┤
        │  REPEATABLE READ                     │
        │  (Lock rows read)                    │
        ├──────────────────────────────────────┤
        │  READ COMMITTED (Default in most DBs)│  Balanced
        │  (Read only committed data)          │
        ├──────────────────────────────────────┤
        │  READ UNCOMMITTED                    │  Fastest, Risky
        │  (Can read uncommitted data)         │
        └──────────────────────────────────────┘
                            │
        Weakest Isolation   ▼
```

### Isolation Problems Explained

#### Problem 1: Dirty Read

**What is it?** Reading **uncommitted** data from another transaction that might be rolled back.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DIRTY READ PROBLEM                              │
└─────────────────────────────────────────────────────────────────────────┘

Isolation Level: READ UNCOMMITTED (allows dirty reads)

Transaction A (Update)            Database                Transaction B (Read)
                               Balance: $500
       │  BEGIN                     │                            │
       │  UPDATE balance = $300     │                            │
       │───────────────────────────▶│                            │
       │                       Balance: $300                     │
       │                       (NOT COMMITTED YET!)              │
       │                            │         BEGIN              │
       │                            │◀───────────────────────────│
       │                            │  SELECT balance            │
       │                            │◀───────────────────────────│
       │                            │  Returns: $300             │
       │                            │───────────────────────────▶│
       │                            │                  Reads $300 (DIRTY!)
       │  ROLLBACK                  │                            │
       │───────────────────────────▶│                            │
       │                       Balance: $500                     │
       │                       (Restored)                        │
       │                            │                  But B thinks it's $300! ❌

Problem: Transaction B read data that was later rolled back!

Solution: Use READ COMMITTED (default in most databases)
```

#### Problem 2: Non-Repeatable Read

**What is it?** Reading the **same row twice** but getting **different values** because another transaction updated it.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     NON-REPEATABLE READ PROBLEM                          │
└─────────────────────────────────────────────────────────────────────────┘

Isolation Level: READ COMMITTED (allows non-repeatable reads)

Transaction A (Read twice)        Database              Transaction B (Update)
                               Balance: $500
       │  BEGIN                     │                            │
       │  SELECT balance            │                            │
       │───────────────────────────▶│                            │
       │  Returns: $500             │                            │
       │◀───────────────────────────│                            │
       │                            │         BEGIN              │
       │                            │◀───────────────────────────│
       │                            │  UPDATE balance = $300     │
       │                            │◀───────────────────────────│
       │                            │  COMMIT                    │
       │                            │◀───────────────────────────│
       │                       Balance: $300                     │
       │  SELECT balance (again)    │                            │
       │───────────────────────────▶│                            │
       │  Returns: $300             │                            │
       │◀───────────────────────────│                            │
       │  Same query, different result! ❌

Problem: Same query in same transaction returned different values!

Solution: Use REPEATABLE READ (locks rows when you read them)
```

**REPEATABLE READ Explained:**

When you use REPEATABLE READ isolation level:
1. You read a row → Database **LOCKS** that row 🔒
2. Other transactions **CANNOT UPDATE** that row
3. They must **WAIT** until you finish
4. You can read the same row again → Get **SAME value** ✓

Think of it like checking out a library book:
- You check out a book (read a row) → Book is "locked" to you
- Others can still READ it, but cannot CHANGE it
- When you return it (commit), others can update it

#### Problem 3: Phantom Read

**What is it?** Running the **same query twice** but getting **different number of rows** because another transaction inserted or deleted rows.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PHANTOM READ PROBLEM                              │
└─────────────────────────────────────────────────────────────────────────┘

Isolation Level: REPEATABLE READ (allows phantom reads)

Transaction A (Count twice)       Database              Transaction B (Insert)
                            Orders: [Order1, Order2]
       │  BEGIN                     │                            │
       │  SELECT COUNT(*)           │                            │
       │  WHERE status = 'pending'  │                            │
       │───────────────────────────▶│                            │
       │  Returns: 2                │                            │
       │◀───────────────────────────│                            │
       │                            │         BEGIN              │
       │                            │◀───────────────────────────│
       │                            │  INSERT INTO orders        │
       │                            │  (status = 'pending')      │
       │                            │◀───────────────────────────│
       │                            │  COMMIT                    │
       │                            │◀───────────────────────────│
       │                Orders: [Order1, Order2, Order3]         │
       │  SELECT COUNT(*)           │                            │
       │  WHERE status = 'pending'  │                            │
       │───────────────────────────▶│                            │
       │  Returns: 3                │                            │
       │◀───────────────────────────│                            │
       │  New row appeared (phantom)! ❌

Problem: New rows appeared between two reads!

Think of counting people in a room:
- You count: 5 people
- Someone walks in (you don't notice)
- You count again: 6 people
- Where did the extra person come from? (Phantom!)

Solution: Use SERIALIZABLE (prevents inserts that match your query)
```

### Isolation Levels Summary

```
╔════════════════════╦═══════════╦═════════════════╦═══════════════╗
║ Isolation Level    ║ Dirty     ║ Non-Repeatable  ║ Phantom       ║
║                    ║ Read      ║ Read            ║ Read          ║
╠════════════════════╬═══════════╬═════════════════╬═══════════════╣
║ READ UNCOMMITTED   ║ Possible  ║ Possible        ║ Possible      ║
║ (Weakest)          ║    ❌     ║      ❌         ║     ❌        ║
╠════════════════════╬═══════════╬═════════════════╬═══════════════╣
║ READ COMMITTED     ║ Prevented ║ Possible        ║ Possible      ║
║ (Default)          ║    ✓      ║      ❌         ║     ❌        ║
╠════════════════════╬═══════════╬═════════════════╬═══════════════╣
║ REPEATABLE READ    ║ Prevented ║ Prevented       ║ Possible      ║
║                    ║    ✓      ║      ✓          ║     ❌        ║
╠════════════════════╬═══════════╬═════════════════╬═══════════════╣
║ SERIALIZABLE       ║ Prevented ║ Prevented       ║ Prevented     ║
║ (Strongest)        ║    ✓      ║      ✓          ║     ✓         ║
╚════════════════════╩═══════════╩═════════════════╩═══════════════╝

Performance: READ UNCOMMITTED > READ COMMITTED > REPEATABLE READ > SERIALIZABLE
             (Fastest)                                              (Slowest)

Safety:      READ UNCOMMITTED < READ COMMITTED < REPEATABLE READ < SERIALIZABLE
             (Least Safe)                                          (Most Safe)
```

**When to use which?**
- **READ UNCOMMITTED**: Analytics (approximate data OK)
- **READ COMMITTED**: Most web applications (default, balanced)
- **REPEATABLE READ**: Financial reports (need consistent reads)
- **SERIALIZABLE**: Banking transactions (perfect consistency needed)

---

## 4. DURABILITY (Permanent After Commit)

**Simple Explanation:** Once a transaction is **committed**, the changes are **permanent**. Even if the database crashes immediately after, the data will be there when it restarts.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DURABILITY GUARANTEE                            │
└─────────────────────────────────────────────────────────────────────────┘

Timeline:

t=0     User updates account balance
        │  BEGIN TRANSACTION
        │  UPDATE accounts SET balance = 1000 WHERE id = 1
        │  COMMIT ✓
        ▼
t=100   Transaction COMMITTED
        ├─▶ Changes written to TRANSACTION LOG (disk)
        ├─▶ Changes written to DATABASE (disk)
        └─▶ User receives "Success" response

t=101   💥 DATABASE CRASHES! (power outage)
        │  (Server restarts...)
        ▼
t=200   Database recovers
        ├─▶ Reads TRANSACTION LOG
        ├─▶ Replays committed transactions
        └─▶ balance = 1000 ✓

✓ Data survived the crash!
```

### How Durability Works: Write-Ahead Log (WAL)

```
Step 1: User commits transaction
        ▼
Step 2: Write to TRANSACTION LOG (on disk)
        ┌─────────────────────────────────────┐
        │ LOG FILE (Persistent)               │
        ├─────────────────────────────────────┤
        │ TX-100 BEGIN                        │
        │ TX-100 UPDATE accounts SET...       │
        │ TX-100 COMMIT ✓                     │
        └─────────────────────────────────────┘
        ▼
Step 3: Write to DATABASE (on disk)
        ┌─────────────────────────────────────┐
        │ DATABASE FILE (Persistent)          │
        ├─────────────────────────────────────┤
        │ accounts table                      │
        │ id=1, balance=1000 ✓                │
        └─────────────────────────────────────┘
        ▼
Step 4: Return success to user

If crash happens before Step 3:
  → Database reads LOG on restart
  → Replays TX-100
  → Data is recovered ✓
```

---

## ACID in Action: Complete Example

```java
@Service
public class CheckoutService {

    @Transactional(
        isolation = Isolation.READ_COMMITTED,  // ← ISOLATION
        timeout = 10  // Timeout after 10 seconds
    )
    public Order checkout(Long userId, List<CartItem> items) {

        // ============ ATOMICITY ============
        // All these operations succeed or all fail together

        try {
            // Step 1: Validate user balance
            User user = userRepo.findById(userId);
            BigDecimal totalPrice = calculateTotal(items);

            // ============ CONSISTENCY ============
            // Enforce business rules
            if (user.getBalance().compareTo(totalPrice) < 0) {
                throw new InsufficientFundsException();
                // ← ROLLBACK happens - ATOMICITY preserved
            }

            // Step 2: Check inventory
            for (CartItem item : items) {
                Inventory inv = inventoryRepo.findById(item.getProductId());

                // ============ CONSISTENCY ============
                if (inv.getStock() < item.getQuantity()) {
                    throw new InsufficientStockException();
                    // ← ROLLBACK happens - ATOMICITY preserved
                }
            }

            // Step 3: Create order
            Order order = new Order(userId, totalPrice);
            orderRepo.save(order);

            // Step 4: Reduce inventory
            for (CartItem item : items) {
                Inventory inv = inventoryRepo.findById(item.getProductId());
                inv.setStock(inv.getStock() - item.getQuantity());
                inventoryRepo.save(inv);
            }

            // Step 5: Deduct user balance
            user.setBalance(user.getBalance().subtract(totalPrice));
            userRepo.save(user);

            // Step 6: Clear cart
            cartRepo.deleteByUserId(userId);

            // If we reach here, all steps succeeded
            // Database will COMMIT

            // ============ DURABILITY ============
            // After COMMIT, changes are permanent
            // Even if server crashes now, order is saved

            return order;

        } catch (Exception e) {
            // ============ ATOMICITY ============
            // Any error → ROLLBACK all changes
            throw e;
        }
    }

    // ============ ISOLATION ============
    // While this transaction runs, other transactions
    // don't see uncommitted changes
}
```

---

## Key Takeaways

✓ **ATOMICITY**: All or nothing (bank transfer example)

✓ **CONSISTENCY**: Valid state always (constraints enforced)

✓ **ISOLATION**: Transactions don't interfere
  - Dirty Read: Reading uncommitted data
  - Non-Repeatable Read: Same row, different value
  - Phantom Read: Different number of rows

✓ **DURABILITY**: Permanent after commit (survives crashes)

✓ **Use @Transactional**: Spring Boot handles ACID automatically

✓ **Isolation levels**:
  - READ COMMITTED: Default, good for most apps
  - REPEATABLE READ: For consistent reads (locks rows)
  - SERIALIZABLE: For perfect consistency (slowest)
