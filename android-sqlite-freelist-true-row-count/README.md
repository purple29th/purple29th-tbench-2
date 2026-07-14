# codimango/android-sqlite-freelist-true-row-count

From-scratch Python script that parses a SQLite-inspired binary format, walks the freelist chain to exclude deleted pages, walks each b-tree page's freeblock chain to exclude deleted cells inside the page, counts live cells by hand, and reports total live rows. No sqlite3/pandas/numpy allowed. Graded on held-out files with independent ground truth.

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 |
| Avocado | measured on submission |
| Opus | measured on submission |
