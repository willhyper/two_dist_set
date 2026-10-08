// SRG status board: a one-line band above the prompt plus a pane with the full table.
//
// Reads `python -m srg.database status <logdir>` (src/srg/database/status.py), once a minute.
// Environment: SRG_PYTHON (python with srg installed, default python3), SRG_LOGDIR (directory with the *.err
// progress logs and queue.txt of the running builds, default the current directory).
const PANE = 'srg-status'
const REFRESH_MS = 60_000

// The last table the status command printed, and when it failed (if it did)
let table = 'no status yet'
let failure = ''

// One line for the band: how many quests are running and queued, from the table's state column
function summary(text) {
  const running = (text.match(/\brunning\b/g) || []).length
  const queued = (text.match(/\bqueued #/g) || []).length
  const finished = (text.match(/\bfinished\b/g) || []).length
  return 'srg: ' + running + ' running, ' + queued + ' queued, ' + finished + ' finished'
}

async function refresh($) {
  try {
    const python = (await $.env.get('SRG_PYTHON')) || 'python3'
    const logdir = (await $.env.get('SRG_LOGDIR')) || '.'
    const out = await $.process.run([python, '-m', 'srg.database', 'status', logdir], { timeoutMs: 20000 })
    if (out.exitCode === 0) {
      table = out.stdout.trimEnd()
      failure = ''
    } else {
      failure = 'status exited with ' + out.exitCode + ': ' + out.stderr.trim().split('\n').pop()
    }
  } catch (err) {
    failure = 'status failed: ' + String(err)
  }
  $.ui.invalidate('ui.render')
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    $.clock.every(REFRESH_MS, () => refresh($))
    refresh($)
    await $.command.register({ name: 'srg-board', description: 'Open the SRG quest status board', immediate: true })
    return next(e)
  })

  // /srg-board opens the pane (and refreshes it)
  on('command.run', { command: 'srg-board' }, async ($) => {
    await $.ui.open({ id: PANE, title: 'SRG quests', focus: true, closeOnEscape: true })
    refresh($)
    return {}
  })

  // The band above the prompt: one line, shown whenever there is something to say
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const { Box, Text } = $.ui.resolve(e)
    const theirs = await next(e)
    return Box({
      flexDirection: 'column',
      children: [Text({ dimColor: true, children: [failure || summary(table)] }), theirs],
    })
  })

  // The pane: the table, one Text per line, and a refresh button
  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE) return next(e)
    const { Box, Text, Button } = $.ui.resolve(e)
    const lines = (failure ? [failure] : []).concat(table.split('\n'))
    return Box({
      flexDirection: 'column',
      children: [
        ...lines.map((line, i) => Text({ key: 'line-' + i, wrap: 'truncate', children: [line || ' '] })),
        Button({ key: 'refresh', label: 'Refresh', hotkey: 'r', onPress: () => refresh($) }),
      ],
    })
  })
}
