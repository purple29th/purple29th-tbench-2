# codimango/android-sqlite-freelist-true-row-count

From-scratch Python script that parses a SQLite-inspired binary format, walks the freelist trunk+leaf chain to exclude deleted pages, skips interior b-tree pages, walks each leaf b-tree page's freeblock chain as intervals to exclude deleted cells whose pointers sit inside freeblocks (fragmentation trap), counts live cells by hand, and reports total live rows. No sqlite3/pandas/numpy allowed. Graded on held-out files with independent ground truth.

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 (1.00) |
| Avocado | 2/5 (0.40) |
| Opus | 0/5 (0.00) |
| gpt-5.5 | 0/5 (0.00) |

## Model Analysis
Hardened v3: previous format (simple freelist chain + freeblock count subtraction) became too easy — all frontier models 5/5. New format adds three traps that break naive solutions: (1) SQLite-realistic freelist trunk pages with next_trunk + leaf_count + leaf array — need to collect both trunk and leaf pages from chain, simple next-only walk undercounts freelist and overcounts rows; (2) interior b-tree pages type 0x05 that must be skipped — counting them as leaf overcounts; (3) fragmentation freeblocks inside leaf pages — cell pointer inside freeblock interval is deleted, but number of freeblocks != number deleted due to extra frag blocks, so cell_count - freeblock_count undercounts. Correct implementation parses header with struct, walks trunk chain collecting all free pages, skips interior, builds freeblock intervals per leaf, counts pointers outside intervals. Tested oracle 3/3, claude-code 0/1 in local harbor (was 5/5 before).

<!-- revalidate sqlite hardened v3 trunk+leaf+interior+frag -->
