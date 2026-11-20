# Agreed workflows

Platform: native PC Windows, fullscreen. Reported game setting 1920x1080;
uploaded screenshot 2048x1280; live capture reported 2560x1600. Capture size is authoritative for detection.
Login is manual for the first version.

## Guild daily
Activities -> locate Guild Daily by title/icon (cards reorder) -> skip if 1/1
and completed checkmark -> Go -> wait for automatic travel -> Confirm accept
-> game auto completes -> verify activity 1/1. Need incomplete card and dialog templates.

## Quest board
Activities -> Quest Board -> skip if 1/1 -> Go -> wait for board -> Start
-> Confirm -> wait for auto completion -> verify all tasks complete or activity 1/1.
Need full-resolution Start/Confirm captures. Do not interrupt auto travel.

## Home
Bottom-right menu -> Home -> Return home -> chef NPC -> F/Communicate ->
Receive today's food -> Map -> farming sprout icon -> wing teleport.
Three plots, each six rows (18 rows total). Walk by click or WASD.
For EACH plot: draw water ONCE, walk to plot, water ONCE at start.
Verify whole-row mode (toggle only when single-cell mode is shown).
Harvest ripe row -> select pumpkin -> buy missing seeds -> plant ->
verify planted -> next row. No watering after each planted row.
Sample seed dialog shows six seeds and price 42; not a universal quantity assumption.
Track plot/row/harvest/purchase/plant independently; prevent duplicate purchases.
Need calibrated walking paths, mature/empty/planted observations and food-claim result.

## MVP
Read activity count -> stop at 3/3.
Open MVP -> prefer spawned (refreshed) boss, otherwise spawn within <=180 seconds.
Select correct boss -> Go now -> wait for travel -> map -> boss icon -> auto walk.
If unspawned, monitor actual countdown then reacquire boss icon.
At target use Z/Auto -> All monsters -> wait -> verify daily count increment.
Do not count attempts or vanished icons as kills. Recheck if boss dies before arrival.
No eligible boss: bounded waiting; death/disconnect/unrecognized UI: pause.
Need result/death templates and verification of Auto toggle semantics.

## Execution principles
Bounded waits/retries, screenshot-based verification, pause/stop, no blind click loops.
No purchases outside explicitly configured Home seeds.
Completion must be verified, not inferred solely from elapsed time.
Do not assume permission under game terms; no anti-cheat bypass.
Current implementation is read-only activity detection; all workflows above are specifications.

## Implementation progress v0.6
User verified activity click, Guild Go travel, F dialog, accept, and game Auto progress.
Completion evidence supplied: gray Guild card, daily 1/1, checkmark; card moves down list.
run_guild.py now connects Guild-only stages with bounded scrolling and fresh-state checks.
It never treats disappearance alone as completion. Integrated live run not yet verified.

## Implementation progress v0.8
Guild reported working by user. Quest Board start and confirmation images received.
run_board.py connects activity navigation, board start, confirmation and bounded
completion checks. No rerolls or extra-round purchases. Offline detector tests pass;
live Windows workflow and current-layout completion remain to be verified.
