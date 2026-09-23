import { test } from 'node:test';
import assert from 'node:assert/strict';
import { projectAmounts } from './src/project-dashboard-data.ts';

test('各段階を分離し、取消・下書き・無効を確定金額から除く', () => {
  const row = (status, total) => ({status, total});
  assert.deepEqual(projectAmounts({
    quotes: [row('draft', '100'), row('issued', '200')],
    orders: [row('received','100'), row('completed','200'), row('cancelled','900')],
    invoices: [row('draft','800'),row('issued','100'),row('paid','200'),row('void','700')],
  }), {quoted:'300',ordered:'300',invoiced:'300',unpaid:'100',paid:'200'});
});
test('書類がない案件は全額ゼロ', () => {
  assert.deepEqual(projectAmounts({quotes:[],orders:[],invoices:[]}), {quoted:'0',ordered:'0',invoiced:'0',unpaid:'0',paid:'0'});
});
test('大きな金額も浮動小数点の誤差を発生させない', () => {
  assert.equal(projectAmounts({quotes:[{status:'draft',total:'9007199254740991'},{status:'draft',total:'2'}],orders:[],invoices:[]}).quoted,'9007199254740993');
});
