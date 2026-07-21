# codimango/android-sqlite-freelist-true-row-count

From-scratch Python script that parses a SQLite-inspired binary format, walks the freelist chain to exclude deleted pages, walks each b-tree page's freeblock chain to exclude deleted cells inside the page, counts live cells by hand, and reports total live rows. No sqlite3/pandas/numpy allowed. Graded on held-out files with independent ground truth.

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 (1.00) |
| Avocado | 2/5 (0.40) |
| Opus | 0/5 (0.00) |
| gpt-5.5 | 0/5 (0.00) |

## Model Analysis
The natural approach sums cell_count across every page, ignoring both the freelist page chain and the per-page freeblock chain. That over-counts deleted rows substantially on every held-out file. Correct implementation parses the header by hand with struct, walks the freelist to skip whole deleted pages, walks each b-tree page's freeblock chain to subtract deleted cells inside the page, and sums only live cells. Both Opus and gpt-5.5 failed with identical over-count sequences, confirming the difficulty comes from the specific SQLite freelist semantics, not spec ambiguity.

<!-- revalidate sqlite e14085c -->

<!-- revalidate sqlite 80a3776 -->

<!-- revalidate sqlite 3712e4f -->
