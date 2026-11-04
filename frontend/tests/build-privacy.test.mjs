import assert from 'node:assert/strict';
import {copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import test from 'node:test';

function fixture(run) {
  const root=mkdtempSync(join(tmpdir(),'voice-studio-build-'));
  try {
    for(const dir of ['scripts','dist/client','worker','.openai','public/licenses','public/audio']) mkdirSync(join(root,dir),{recursive:true});
    for(const [name,value]of [['dist/client/index.html','<html></html>'],['worker/index.js','export default {};'],['.openai/hosting.json','{}'],['public/licenses/Notice.txt','Original license'],['public/audio/scene-1.wav','private local recording']])writeFileSync(join(root,name),value);
    copyFileSync(new URL('../scripts/prepare-sites-build.mjs',import.meta.url),join(root,'scripts/prepare-sites-build.mjs'));
    run(root,()=>spawnSync(process.execPath,[join(root,'scripts/prepare-sites-build.mjs')],{encoding:'utf8'}));
  } finally {rmSync(root,{recursive:true,force:true});}
}

test('ships notices and hosting files while retaining local audio outside the build',()=>{
  fixture((root,build)=>{
    const result=build();assert.equal(result.status,0,result.stderr);
    assert.equal(readFileSync(join(root,'dist/client/licenses/Notice.txt'),'utf8'),'Original license');
    assert.ok(existsSync(join(root,'dist/server/index.js')));
    assert.ok(existsSync(join(root,'dist/.openai/hosting.json')));
    assert.equal(existsSync(join(root,'dist/client/audio')),false);
    assert.equal(readFileSync(join(root,'public/audio/scene-1.wav'),'utf8'),'private local recording');
  });
});

test('refuses packaging if private audio has already been copied into the client build',()=>{
  fixture((root,build)=>{
    mkdirSync(join(root,'dist/client/audio'));writeFileSync(join(root,'dist/client/audio/scene-1.wav'),'private local recording');
    const result=build();assert.notEqual(result.status,0);
    assert.match(result.stderr,/Private local audio must stay outside the web build/);
    assert.equal(existsSync(join(root,'dist/server/index.js')),false);
  });
});
