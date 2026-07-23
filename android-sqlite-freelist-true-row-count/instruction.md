Hey, we've got a SQLite database file dumped off an Android device and I need the row count. Write /app/solve.py that takes a path to a .sdb file and prints one number: total live rows across every table.

The .sdb format is little-endian: 4-byte magic "SDB1", uint32 version at 4, uint32 page_size at 8, uint32 page_count at 12, uint32 freelist_head at 16 (0 means none), then 64-byte header total. Pages are numbered from 1 and each is page_size bytes starting right after the header.

A page starting with byte 0x0D is a table b-tree leaf: uint16 cell_count at offset 1, uint16 freeblock_offset at offset 3, then cell_count uint16 cell pointers at offset 7 pointing inside the page. A freeblock inside a page starts with uint16 next offset then uint16 size, chained until 0. The freeblock chain tracks deleted cells reclaimed inside that page – each freeblock entry corresponds to one deleted row slot inside that page that should not be counted as live.

A page starting with 0x00 is a freelist page and holds no live rows, its next 4 bytes are the next freelist page number in the chain as uint32, 0 ends chain. So you need to walk the freelist from freelist_head to collect all pages that are completely deleted and skip them.

There's a sample at /app/data/sample.sdb. Naive sum of cell_count over all pages overcounts because you would include freelist pages and deleted freeblocks.

Parse it yourself with struct, no sqlite3, pandas, sqlalchemy, numpy, or other DB or array libs, and no shelling out. We grade on files you haven't seen.
