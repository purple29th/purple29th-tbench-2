Hey, we've got a SQLite database file dumped off an Android device and I need the row count. Write /app/solve.py that takes a path to a .sdb file and prints one number: total live rows across every table.

The .sdb format is little-endian: 4-byte magic "SDB1", uint32 version at 4, uint32 page_size at 8, uint32 page_count at 12, uint32 freelist_head at 16 (0 means none), then 64-byte header total. Pages are numbered from 1 and each is page_size bytes starting right after the header.

A page starting with byte 0x00 is a freelist trunk page: uint32 next_trunk at offset 1 (0 ends chain), uint32 leaf_count at offset 5, then leaf_count uint32 leaf page numbers at offset 9. Both trunk pages in the chain from freelist_head and all leaf pages referenced inside each trunk are completely free and hold no live rows. Walk the chain to collect the full free set.

A page starting with 0x05 is a table b-tree interior page: uint16 cell_count at offset 1, uint16 freeblock_offset at offset 3, uint32 rightmost_child at offset 5, then cell_count uint16 cell pointers at offset 9. Each interior cell is 8 bytes (uint32 left_child + uint32 key) somewhere inside the page. Interior pages hold no rows themselves.

A page starting with 0x0D is a table b-tree leaf: uint16 cell_count at offset 1, uint16 freeblock_offset at offset 3, then cell_count uint16 cell pointers at offset 7 pointing inside the page. A freeblock inside a leaf page starts with uint16 next_offset then uint16 size, chained until 0. Each freeblock occupies interval [offset, offset+size). Freeblocks are reclaimed space — some correspond to deleted rows and some are fragmentation. A leaf cell whose pointer lies inside any freeblock interval is deleted and must not be counted. Count only cell pointers whose offset lies outside all freeblock intervals.

There's a sample at /app/data/sample.sdb. Naive sum of cell_count over all pages overcounts because you would include freelist pages (both trunk and leaf), interior pages, and deleted cells whose pointers sit inside freeblocks. Counting cell_count minus number_of_freeblocks also fails due to fragmentation freeblocks.

Parse it yourself with struct, no sqlite3, pandas, sqlalchemy, numpy, or other DB or array libs, and no shelling out. We grade on files you haven't seen.
