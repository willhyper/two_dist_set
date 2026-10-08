import { expect, test } from 'claude-code/testing'

test('/srg-board opens the pane and the table comes from the status command', async ($, on) => {
  // Answer the status command in place of python
  on('process.run', () => ({
    value: { exitCode: 0, stderr: '', stdout: 'quest state\nSRG(29,14,6,7) running\nSRG(40,12,2,4) queued #1\n' },
  }))
  on('env.get', () => ({ value: undefined }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  const answer = await $.command.run({ command: 'srg-board', args: '' })
  expect(answer).toEqual({})
})
