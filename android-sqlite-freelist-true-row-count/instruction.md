We dump a little database file off the device and need the real row count. Write your script to /app/solve.py that reads the file path from the first argument and prints one number, the total live rows across every table.

The file is little endian with magic SDB1, version at four, page size at eight, page count at twelve, freelist head at sixteen then sixty four byte header total. So header is 64 bytes: 0-3 magic, 4-7 version uint32, 8-11 page_size uint32, 12-15 page_count uint32, 16-19 freelist_head uint32 (page number, 0 means no freelist), rest reserved.

Pages are numbered from one and each is page_size bytes right after header. Page N starts at offset 64 + (N-1)*page_size.

Two page types:

- 0x00 freelist page: holds no live rows, must be skipped. It is part of the freelist chain. At byte 1 inside the page (page_offset+1) there is next freelist page number as little-endian uint32, zero ends chain. So walk from freelist_head following next pointer to collect all freelist page numbers in a set.

- 0x0D table b-tree leaf: contains live rows but some rows inside may be deleted. Layout:
  byte 0: 0x0D marker
  offset 1: cell_count as uint16 little endian (total slots ever allocated in this page)
  offset 3: freeblock_offset as uint16 little endian, byte offset inside page where first freeblock (deleted cell) starts, 0 means no freeblocks
  offset 5: maybe unused
  offset 7 onward: cell_count * uint16 cell pointers (you can ignore for counting)

  A freeblock inside a page tracks one deleted row reclaimed inside that page. Freeblock structure at its offset inside page:
    0-1: next freeblock offset as uint16 (0 ends chain)
    2-3: size as uint16 (you can ignore size, just count occurrence)
  Chain until zero. So walk freeblock chain from freeblock_offset and count how many freeblocks you see – each freeblock equals one deleted row inside that page.

  Live rows in this b-tree page = cell_count - freeblock_count

Important: both levels matter. Naive sum of cell_count across all pages over-counts heavily. Example diffs on held-outs are 22-44 rows over. You must:
1) skip any page number that appears in freelist chain (whole pages deleted)
2) for remaining 0x0D pages, subtract freeblock count inside page

Total live rows = sum over pages NOT in freelist: (cell_count - freeblock_chain_len)

A sample is in the data folder as sample.sdb at /app/data/sample.sdb you can test locally. It has 12 pages, freelist head 9 chain 9->11, naive sum 119 but true live is 97 after removing freelist pages and freeblocks.

Parse it yourself with struct, no sqlite3, pandas, sqlalchemy, numpy, or other DB or array libs, and no shelling out. We grade on files you have not seen with different page counts, freelist lengths, and freeblock counts.
