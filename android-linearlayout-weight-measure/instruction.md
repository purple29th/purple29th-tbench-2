# Setting

A Kotlin simulator of a horizontal layout measure pass over a row of views. Children declare a fixed width, a wrap-content intrinsic width, or a layout weight; the measurer divides the available width and lays the children out left to right. The current implementation in /app/src/com/example/layout/LinearLayoutMeasurer.kt produces wrong widths and positions across several scenarios. Fix it.

# Operations

Operations are read from /app/scenario.txt.

- CHILD <id> <kind> <value> <margin> — add a child. <kind> is FIXED, WRAP, or WEIGHT. For FIXED the measured width is <value>; for WRAP it is the content width <value>; for WEIGHT the child has width 0 in the first pass and a layout weight of <value>. <margin> is a leading margin.
- MEASURE <totalWidth> — run the measure + layout pass for the given parent width.
- QUERY — append a snapshot to /app/output.txt.

Children are laid out in the order they were added.

# Measure algorithm

For MEASURE <totalWidth>:

1. First pass. Walk children in order accumulating usedWidth. Every child contributes its margin to usedWidth. A FIXED or WRAP child is measured to its value and also adds that width to usedWidth. A WEIGHT child is measured to 0 in this pass.
2. remaining = totalWidth - usedWidth. overflow is true when remaining is negative.
3. Weight distribution over distributable = max(0, remaining):
   - If there is exactly one weighted child, it receives the entire distributable space.
   - If there are two or more weighted children, the space is divided in inverse proportion to weight: a child's share is proportional to its complement, defined as (totalWeight - the child's own weight), where totalWeight is the sum of the weighted children's weights. Concretely, let complementSum be the sum of every weighted child's complement. For each weighted child in order except the last, its width is `distributable * complement / complementSum` (integer division). The last weighted child receives `distributable - (the shares already assigned)`, so the weighted children together consume exactly the distributable space. If complementSum is 0, every weighted child is measured to 0.
4. Layout. Walk children in order with a running offset starting at 0. For each child: add its margin to the offset, record the child's start at the current offset, then add the child's measured width to the offset.

# Output format

Each QUERY appends:

    measure totalWidth=<W> remaining=<R> overflow=<true|false>
    children:
      id=<id> spec=<KIND(value)> margin=<m> measuredWidth=<w> start=<x>
      ...

remaining is totalWidth minus the first-pass usedWidth (may be negative). spec is the child's kind and declared value: FIXED(<px>), WRAP(<contentPx>), WEIGHT(<weight>). Children are listed in add order.

# What you need to do

Fix /app/src/com/example/layout/LinearLayoutMeasurer.kt. Do not modify Main.kt or LayoutTypes.kt. The verifier compiles and runs automatically.

# Reference build (local debugging only)

From /app:

    kotlinc src/com/example/layout/*.kt -include-runtime -d app.jar
    java -jar app.jar scenario.txt output.txt
