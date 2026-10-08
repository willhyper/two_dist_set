---
description: Status of the running and queued SRG quests (elapsed / pending / harvested / expected)
argument-hint: [logdir]
---
Run `python -m srg.database status $ARGUMENTS` (default log dir: the directory the builder runs write their `*.err`
progress logs and `queue.txt` to) and show the table as is. Then add one line per finished quest: verify the file the
builder wrote (tests, `solved()`), commit and push to master.
