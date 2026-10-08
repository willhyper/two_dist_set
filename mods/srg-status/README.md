# srg-status (Claude Code mod)

Status board for the SRG builder runs: a one-line band above the prompt (`srg: 3 running, 6 queued, 0 finished`,
refreshed every minute) and `/srg-board`, which opens a pane with the full table
(elapsed / pending partial matrices / graphs harvested / graphs expected). It only reads
`python -m srg.database status <logdir>` (src/srg/database/status.py); it starts nothing.

```
SRG_PYTHON=/path/to/venv/bin/python SRG_LOGDIR=/path/to/logs claude --plugin-dir mods/srg-status
```

`claude plugin validate mods/srg-status` lists what it does; `claude plugin test` (in this directory) runs its test.
Tested with Claude Code 2.1.292.
