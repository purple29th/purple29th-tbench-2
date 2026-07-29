hey i am on android photos team fixing our mini fragment manager for nested tabs. we have root containers like main and child containers like homeTabs inside fragment Home that holds Tab1 etc. child can have its own child so nesting goes deep. each fragment has hidden flag detached flag lifecycle that is one of INITIALIZED CREATED VIEW_CREATED STARTED RESUMED and maxLifecycle that caps it, plus viewModel map that survives rotation but is cleared on remove and parent remove and readd must be empty, and savedState map that survives rotation and pop restore, and children set.

we ship a kotlin app that reads scenario dot txt one operation per line and writes output dot txt. some contract tests fail so you need to fix the implementation.

operations are

BEGIN txn id starts a transaction

ADD txn id container fragment adds root fragment into container

ADD_CHILD txn id parent fragment child container child fragment adds child under parent parent must exist and not detached else ignore

REPLACE txn id container fragment replaces container contents removing previous fragments and all their descendants and clearing their viewmodels

REMOVE txn id fragment removes fragment and all its descendants from all containers and registry and clears viewmodels

HIDE txn id fragment hides fragment hidden true lifecycle drops to STARTED capped by max and that downgrade propagates to all descendants and their max is also capped by parent max

SHOW txn id fragment shows fragment hidden false lifecycle goes to RESUMED capped by max and parent max unless parent hidden or detached then stays STARTED and upgrade propagates to children that are not hidden detached

DETACH txn id fragment detaches fragment removes it and its children from containers but keeps their state registry with detached true lifecycle CREATED viewmodel and savedstate retained and lastContainer remembered

ATTACH txn id fragment re attaches previously detached fragment only if it was detached adds it back to its lastContainer and its children back to their last containers lifecycle becomes STARTED if hidden else RESUMED capped by max and parent max

SET_MAX txn id fragment state sets maxLifecycle to that state and caps own lifecycle to min of current and max and also cascades to all descendants capping their maxLifecycle to min of their max and parent max and their lifecycle to min of lifecycle and new max

SAVE fragment key value immediate savedState write survives rotation and pop restore

VM_PUT fragment key value immediate viewModel write survives ROTATE but cleared on REMOVE and parent REMOVE and readd must be empty but retained when restored via pop of REPLACE

ADD_TO_BACK_STACK txn id name or NONE marks transaction as backstack entry NONE means anon

COMMIT txn id applies ops in order and if marked records on backstack capturing replaced fragments with full child subtree hidden detached lifecycle max lastContainer viewmodel savedstate children and container mapping and hidden snapshot max snapshot detached snapshot

POP name or NONE pops backstack POP NONE pops most recent POP name pops down to and including most recent entry with that name searching from top case sensitive if name not found it is no op must not drain stack popping restores replaced fragments with entire child subtree and captured state including container mapping

ROTATE simulates config change clears live containers and fragment registry but keeps backstack list snapshot and replays entries via TransactionReplay replayInto must correctly recreate root and child fragments only from backstacked entries non backstacked lost viewmodel savedstate for recreated must be retained from pre rotate stores child whose parent was never backstacked must not reappear

QUERY records snapshot

output format at end print one block per QUERY in order blocks separated by blank line each block has

container lines sorted by container name containers ever used are still printed even if empty after REMOVE REPLACE DETACH with fragments equals empty list sorted e g container equals main fragments equals open bracket Home close bracket

fragment lines sorted by name e g fragment equals Home parent equals NONE hidden equals false detached equals false lifecycle equals RESUMED maxLifecycle equals RESUMED viewModel equals open curly close curly savedState equals open curly close curly children equals open bracket close bracket

parent NONE for root hidden detached bool lower case lifecycle and maxLifecycle one of those five viewModel savedState maps sorted by key as key equals value comma separated children sorted direct child names

final line backstack equals open bracket entries comma separated anon for unnamed close bracket

contract tests are at app src com example fragment test ManagerContractKt run bash app src run contract dot sh

make all pass pay attention to tricky interactions like set max capping children and replacing and detaching etc but there is no list of bugs you must figure out by reading contract

build run bash app src run dot sh reads app scenario dot txt writes app output dot txt

where to start app src com example fragment FragmentManagerKt and TransactionReplayKt and ContainerKt and FragmentKt and BackStackEntryKt
