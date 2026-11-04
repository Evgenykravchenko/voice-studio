import { test } from 'node:test';
import assert from 'node:assert/strict';
import { menuPosition } from '../src/menu-position.ts';

test('scene actions open above a trigger near the bottom of the window', () => {
  const menu = menuPosition({left: 270, right: 300, top: 640, bottom: 672}, {width: 200, height: 110}, {width: 1280, height: 720});
  assert.equal(menu.left, 100);
  assert.ok(menu.top + 110 < 640);
});

test('language/theme controls open below the header without leaving the right edge', () => {
  const menu = menuPosition({left: 1160, right: 1278, top: 16, bottom: 56}, {width: 200, height: 150}, {width: 1280, height: 720});
  assert.equal(menu.top, 64);
  assert.ok(menu.left + 200 <= 1272);
});

test('a narrow screen clamps the menu inside both viewport edges', () => {
  const menu = menuPosition({left: 12, right: 42, top: 80, bottom: 112}, {width: 300, height: 150}, {width: 390, height: 844});
  assert.equal(menu.left, 8);
  assert.ok(menu.left + 300 <= 382);
  assert.ok(menu.top >= 8 && menu.top + 150 <= 836);
});

test('a tall menu scrolls above its trigger in a short window instead of covering it', () => {
  const menu = menuPosition({left: 150, right: 300, top: 250, bottom: 294}, {width: 220, height: 320}, {width: 320, height: 400});
  assert.equal(menu.maxHeight, 234);
  assert.equal(menu.top + menu.maxHeight, 242);
  assert.ok(menu.left >= 8 && menu.left + 220 <= 312);
});
test('a tall menu scrolls below a header control while staying in the viewport', () => {
  const menu = menuPosition({left: 180, right: 300, top: 40, bottom: 84}, {width: 220, height: 320}, {width: 320, height: 240});
  assert.equal(menu.top, 92);
  assert.equal(menu.maxHeight, 140);
  assert.ok(menu.top + menu.maxHeight <= 232);
});
