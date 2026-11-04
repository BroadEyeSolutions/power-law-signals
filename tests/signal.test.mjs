import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import signal from '../src/signal.js';

const rules = JSON.parse(readFileSync(new URL('../src/signal-rules.json', import.meta.url), 'utf8'));

test('codes are ordered: each band adds one more 1', () => {
  const { codes } = signal.encode(rules, { monthly_sales: 'over_100k', years_in_business: 'under_1' });
  assert.deepEqual(codes, { monthly_sales: '1110', years_in_business: '0000' });
  const order = Object.values(rules.questions.monthly_sales.codes);
  assert.deepEqual([...order].sort(), order, 'codes sort in band order');
});

test('the line sits at $30,000 a month and one year in business', () => {
  const cases = [
    ['under_10k', 'over_5', false],
    ['10k_to_30k', 'over_5', false],
    ['30k_to_100k', 'under_1', false],
    ['30k_to_100k', '1_to_3', true],
    ['over_100k', '3_to_5', true]
  ];
  for (const [sales, years, want] of cases) {
    assert.equal(signal.evaluate(rules, { monthly_sales: sales, years_in_business: years }).qualified, want, `${sales} / ${years}`);
  }
});

test('missing or unknown answers never qualify, and unknown ones are reported', () => {
  const r = signal.evaluate(rules, { monthly_sales: '$30,000 – $100,000', years_in_business: '1_to_3' });
  assert.equal(r.qualified, false);
  assert.deepEqual(r.unknown, ['monthly_sales=$30,000 – $100,000']);
  assert.equal(signal.evaluate(rules, {}).qualified, false);
});

test('an "any" rule and an "in" rule work too', () => {
  const alt = { questions: rules.questions, qualified: { any: [{ question: 'monthly_sales', in: ['1110'] }, { question: 'years_in_business', starts_with: '111' }] } };
  assert.equal(signal.evaluate(alt, { monthly_sales: 'over_100k', years_in_business: 'under_1' }).qualified, true);
  assert.equal(signal.evaluate(alt, { monthly_sales: '30k_to_100k', years_in_business: 'over_5' }).qualified, true);
  assert.equal(signal.evaluate(alt, { monthly_sales: '30k_to_100k', years_in_business: '3_to_5' }).qualified, false);
});
