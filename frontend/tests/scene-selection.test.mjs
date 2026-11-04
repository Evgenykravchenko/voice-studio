import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveSceneSelection} from '../src/scene-selection.ts';

test('adding or duplicating a scene keeps its explicit selection despite the old URL',()=>{
  assert.equal(resolveSceneSelection([{id:'first'},{id:'new'}],'new','first',false),'new');
});
test('loading a project restores its valid deep-linked scene after asynchronous data arrives',()=>{
  assert.equal(resolveSceneSelection([{id:'first'},{id:'target'}],'initial-draft','target',true),'target');
});
test('opening another project resolves its URL instead of a prior project selection',()=>{
  assert.equal(resolveSceneSelection([{id:'first'},{id:'target'}],'first','target',true),'target');
});
test('deletion and undo retain the explicitly chosen remaining or restored scene',()=>{
  assert.equal(resolveSceneSelection([{id:'next'}],'next','deleted',false),'next');
  assert.equal(resolveSceneSelection([{id:'restored'},{id:'next'}],'restored','next',false),'restored');
});
test('invalid deep links select the first scene and an empty project clears selection',()=>{
  assert.equal(resolveSceneSelection([{id:'first'}],'stale','missing',true),'first');
  assert.equal(resolveSceneSelection([],'stale','missing',true),'');
});
