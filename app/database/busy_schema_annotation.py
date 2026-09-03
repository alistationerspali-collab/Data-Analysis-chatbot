"""
Hand-verified schema annotation for the Busy Accounting Software database.

This is NOT auto-generated from INFORMATION_SCHEMA -- Busy uses generic,
cryptic column names (Value1/2/3, MasterCode1/2, CM1-CM11, D1-D12) that
cannot be understood from column names/types alone. Every mapping below
was manually verified against Busy's UI using known reference transactions.

Scope (v1): Sales Analysis, Purchase Analysis, Stock/Inventory (net movement),
            Account Books/Summary, Outstanding Analysis (net movement).

Known gaps -- DO NOT let the LLM guess at these, they are explicitly
flagged in the annotation below:
  - True opening balance (absolute Outstanding Balance) is not stored
    anywhere findable in the DB. Only "net movement over a date range"
    is supported.
  - True current/absolute stock quantity (with opening stock) is not
    reliably stored either. Only "net stock movement over a date range"
    is supported, same limitation as Outstanding Balance.
  - Salesman-to-voucher linkage: no MasterType=19 (Salesman) code has
    ever been found used in Tran2. Salesman field is not populated on
    vouchers in this install. Do not generate salesman-wise queries.
"""

BUSY_SCHEMA_ANNOTATION = """
=== BUSY ACCOUNTING SOFTWARE - VERIFIED SCHEMA (BusyComp0001_db12025) ===

TABLE: Master1  (unified master table for accounts, items, groups, salesmen)
  - Code (int)          : unique ID for this master record
  - Name (nvarchar)      : display name (party / item / group / salesman)
  - MasterType (smallint): entity type. CONFIRMED VALUES:
        2  = Account / Party (business/person ledger accounts)
        5  = Item Group (hierarchical -- can nest multiple levels deep via ParentGrp)
        6  = Item (has HSNCode populated)
        19 = Salesman (list confirmed against Busy UI, but NOT used on any
             voucher in this install -- do not join transactions to this type)
  - ParentGrp (int)       : Code of parent group. 0 = top of hierarchy (root).
        Hierarchy depth is VARIABLE (not fixed levels) -- always use a
        recursive CTE to walk up/down, never assume a fixed number of joins.
  - HSNCode (nvarchar)    : populated only for Items (MasterType=6)
  - D1, D2 (float)        : for Items, appear to be the item's ORIGINAL/LIFETIME
                            opening stock qty/value from when the item was first
                            created -- NOT the current financial year's opening
                            balance. Confirmed mismatch against a real item's
                            actual FY opening stock (D1=1.0 vs actual Op.Bal=233
                            in Busy's Inventory report). Do NOT use D1/D2 as
                            current-year opening stock.

TABLE: Tran2  (universal transaction/ledger line table, ~105 columns)
  Only the columns below have confirmed meaning. Ignore all other columns
  unless a new mapping is explicitly verified and added here.
  - RecType (smallint)    : row's role within the voucher (party leg / item
                            leg / tax leg). Values seen: 1, 2, 3.
  - VchCode (int)         : internal voucher ID. Joins to OrgSalePurc.VchCode
  - VchNo (nvarchar)      : display voucher number, e.g. 'Cr-5634/2025-26'
  - MasterCode1 (int)     : joins to Master1.Code (account OR item OR other,
                            depending on which row/RecType this is)
  - MasterCode2 (int)     : joins to Master1.Code (secondary linked account,
                            e.g. broker/sub-ledger; 0 if not applicable)
  - VchType (smallint)    : voucher type code (Sale/Purchase/Receipt/etc.) --
                            exact number-to-type mapping NOT yet decoded.
  - Date (datetime)       : transaction date
  - Value1 (float)        : for ITEM rows (joined to MasterType=6) = QUANTITY,
                            signed (negative = stock outflow/sale, positive =
                            stock inflow/purchase). Verified against Busy's
                            "Inventory - Monthly Summary" report (net movement
                            matched exactly: Qty In - Qty Out = SUM(Value1)).
                            For PARTY/ACCOUNT rows (joined to MasterType=2) =
                            signed amount used for balance movement (see sign
                            convention below).
  - Value2 (float)        : secondary/alternate unit quantity, often equals
                            Value1. NOT a rate.
  - Value3 (float)        : for ITEM rows = AMOUNT (Value3 / Value1 = Rate)
  - Balance1/2/3 (float)  : running balance -- ONLY populated for some
                            RecType/row combinations. Was all-zero for party
                            ledger rows in verified test case. DO NOT rely on
                            these for Outstanding Balance or Stock Balance;
                            use the net movement formulas instead (see below).

  SIGN CONVENTION -- PARTY/ACCOUNT rows (MasterCode1 -> MasterType=2):
    - Negative Value1 on a Sale-type voucher row => INCREASES the party's
      Dr (receivable) balance (they owe you more)
    - Positive Value1 on a Receipt-type voucher row => DECREASES the party's
      Dr balance (they paid you)
    - Formula: NetOutstandingChange = -SUM(Value1) over the period

  SIGN CONVENTION -- ITEM rows (MasterCode1 -> MasterType=6):
    - Value1 directly represents quantity movement: negative = net stock
      outflow (sold/issued more than received), positive = net stock inflow
      (received/purchased more than sold).
    - Formula: NetQtyMovement = SUM(Value1) over the period (NO sign flip
      needed here, unlike the party/account case above)

TABLE: OrgSalePurc  (voucher header / tax summary -- header level only, NOT item-wise)
  - VchCode (int)         : voucher ID, joins to Tran2.VchCode
  - VchNo (nvarchar)      : display voucher number
  - VchDate (datetime)    : voucher date
  - TaxableAmt, TaxAmt, TaxAmt1, SchgAmt (float): tax figures (often 0 for
    non-GST voucher types e.g. Receipts/Payments -- this is normal, not missing data)
  - RegType (smallint)    : GST registration type

=== VERIFIED QUERY PATTERNS (use these as templates) ===

-- Item-wise Sales/Purchase:
SELECT t.VchCode, t.VchNo, t.Date, m.Name AS ItemName, m.HSNCode,
       t.Value1 AS Qty, t.Value3 AS Amount,
       CASE WHEN t.Value1 <> 0 THEN t.Value3 / t.Value1 ELSE 0 END AS Rate
FROM Tran2 t
JOIN Master1 m ON t.MasterCode1 = m.Code
WHERE m.MasterType = 6
ORDER BY t.Date DESC;

-- Group-wise Sales (any level, variable hierarchy depth -- use recursive CTE):
WITH GroupPath AS (
    SELECT Code AS ItemCode, Code AS AncestorCode, Name AS AncestorName, ParentGrp, 0 AS Level
    FROM Master1 WHERE MasterType = 6
    UNION ALL
    SELECT gp.ItemCode, m.Code, m.Name, m.ParentGrp, gp.Level + 1
    FROM GroupPath gp JOIN Master1 m ON gp.ParentGrp = m.Code
    WHERE gp.ParentGrp <> 0
)
SELECT SUM(t.Value3) AS TotalSales
FROM Tran2 t JOIN GroupPath gp ON t.MasterCode1 = gp.ItemCode
WHERE gp.AncestorName = '<group_name>'
OPTION (MAXRECURSION 100);

-- Outstanding Analysis (NET MOVEMENT over a period -- NOT absolute balance):
SELECT m.Name AS PartyName, -SUM(t.Value1) AS NetOutstandingChange
FROM Tran2 t JOIN Master1 m ON t.MasterCode1 = m.Code
WHERE m.MasterType = 2 AND t.Date BETWEEN @FromDate AND @ToDate
GROUP BY m.Name
ORDER BY NetOutstandingChange DESC;

-- Stock/Inventory Net Movement (NET MOVEMENT over a period -- NOT absolute
-- current stock level, same limitation as Outstanding Analysis):
SELECT m.Name AS ItemName, SUM(t.Value1) AS NetQtyMovement
FROM Tran2 t JOIN Master1 m ON t.MasterCode1 = m.Code
WHERE m.MasterType = 6 AND t.Date BETWEEN @FromDate AND @ToDate
GROUP BY m.Name
ORDER BY NetQtyMovement;
-- Sign convention: negative NetQtyMovement = net stock outflow (more sold/
-- issued than received in this period); positive = net stock inflow (more
-- received than sold). Verified against Busy's "Inventory - Monthly Summary"
-- report (exact match: 233 opening + (-202) net movement = 31 closing).

=== EXPLICIT LIMITATIONS - DO NOT ATTEMPT THESE ===
- Do NOT generate a query for absolute/true Outstanding Balance (with opening
  balance included). Only "net movement over a date range" is supported.
  If asked for absolute outstanding balance, respond that this data isn't
  available and offer net movement over a period instead.
- Do NOT generate a query for absolute/current stock quantity (with opening
  stock included). Only "net stock movement over a date range" is supported,
  same limitation as Outstanding Balance -- the true opening stock figure per
  item is not reliably found in the DB (D1/D2 columns in Master1 appear to
  reflect original/lifetime opening stock from item creation, not the current
  financial year's opening balance).
- Do NOT generate salesman-wise sales queries. Salesman data is not populated
  on vouchers in this Busy install. If asked, say this data isn't currently
  tracked.
- Do NOT guess at Trial Balance / P&L / Balance Sheet / GST / TDS / Payroll
  queries -- these tables/mappings have not been verified. Refuse and say
  this report type isn't supported yet.
"""