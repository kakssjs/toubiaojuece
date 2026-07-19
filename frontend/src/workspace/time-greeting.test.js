import test from 'node:test'
import assert from 'node:assert/strict'

import { formatWorkspaceDate, greetingForHour } from './time-greeting.js'

test('greetingForHour uses the appropriate time period', () => {
  assert.equal(greetingForHour(2), '夜深了')
  assert.equal(greetingForHour(8), '上午好')
  assert.equal(greetingForHour(12), '中午好')
  assert.equal(greetingForHour(15), '下午好')
  assert.equal(greetingForHour(20), '晚上好')
  assert.equal(greetingForHour(23), '夜深了')
})

test('formatWorkspaceDate follows the current calendar date', () => {
  assert.equal(formatWorkspaceDate(new Date(2026, 6, 18, 9)), '2026 年 7 月 18 日 · 星期六')
})
