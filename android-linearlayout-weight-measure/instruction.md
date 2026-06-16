# Setting

A Kotlin simulator of the horizontal LinearLayout measure pass — the integer-arithmetic core that decides how a row of Android views divides the available width, including the minimum-width redistribution that Android performs when a weighted child would be squeezed below its minimum. Children declare a fixed width, a wrap-content intrinsic width, or a layout_weight with an optional minimum width; the measurer runs the two-pass algorithm, redistributes around minimum-width constraints, and lays the children out left to right. Bugs here cause clipped views, misaligned rows, and weights that ignore minimums.

# Operations

Operations are read from /app/scenario.txt.

- CHILD <id> <kind> <value> <margin> <minWidth> — add a child. <kind> is FIXED, WRAP, or WEIGHT. For FIXED the measured width is <value>; for WRAP it is the content width <value>; for WEIGHT the child has width 0 and layout_weight <value>. <margin> is a leading margin. <minWidth> applies only to WEIGHT children (it is ignored for FIXED and WRAP).
- MEASURE <totalWidth> — run the measure + layout pass for the given parent width.
- QUERY — append a snapshot to /app/output.txt.

Children are kept and laid out in the order they were added.

# Measure algorithm

For MEASURE <totalWidth>:

1. First pass. Walk children in order accumulating usedWidth. Every child contributes its margin. A FIXED or WRAP child is measured to its value and also adds that width to usedWidth. A WEIGHT child is measured to 0 in this pass.
2. remaining = totalWidth - usedWidth. overflow is true when remaining is negative.
3. Weight distribution over distributable = max(0, remaining), with minimum-width redistribution:
   a. Consider all weighted children "active". Compute each active child's share: for every active child except the last, `share = avail * weight / activeWeightSum` (integer division), where avail is distributable minus the widths already pinned to minimums; the last active child gets `avail - (shares already assigned)` so the active children exactly fill avail.
   b. If any active child's share is below its minWidth, take the first such child in order, pin its width to its minWidth, remove it from the active set, and recompute step (a) for the remaining active children. Repeat until no active child is below its minimum.
   c. A pinned child keeps its minWidth even if that exceeds the space that was available.
3.5. Sticky measured widths (high-water mark). Each weighted child remembers the largest width it has ever been assigned across MEASURE calls — its high-water mark, initially 0. A weighted child's effective minimum is the larger of its declared minWidth and its high-water mark, and that effective minimum is what the redistribution in step 3 uses for the below-minimum check and for pinning. So once a weighted child has been measured at some width, a later MEASURE at a smaller parent width will not shrink it below that width. After each measure, every weighted child's high-water mark is updated to the larger of its previous high-water mark and its new measured width.

4. Layout. Walk children in order with a running offset from 0: add the child's margin, record its start, then add its measured width.

# Output format

Each QUERY appends:

    measure totalWidth=<W> remaining=<R> overflow=<true|false>
    children:
      id=<id> spec=<KIND(value)> margin=<m> minWidth=<mw> measuredWidth=<w> start=<x>
      ...

remaining is totalWidth minus the first-pass usedWidth (may be negative). spec is the kind and declared value: FIXED(<px>), WRAP(<contentPx>), WEIGHT(<weight>). Children are listed in add order.

# What you need to do

Fix /app/src/com/example/layout/LinearLayoutMeasurer.kt. Do not modify Main.kt or LayoutTypes.kt. The verifier compiles and runs automatically.

# Reference build (local debugging only)

From /app:

    kotlinc src/com/example/layout/*.kt -include-runtime -d app.jar
    java -jar app.jar scenario.txt output.txt
