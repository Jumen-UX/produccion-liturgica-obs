// Comprueba que la previsualización no replique ni modifique el motor de OBS.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'..',name),'utf8');

test('scripts de salida, estudio, biblioteca y dock sin errores de sintaxis',()=>{
 for(const page of ['overlay.html','studio.html','biblioteca.html','dock.html']){
  const source=read(page);
  const scripts=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.ok(scripts.length,page+' requiere script');
  for(const [i,script] of scripts.entries())assert.doesNotThrow(()=>new vm.Script(script[1],{filename:page+':'+i}));
 }
});
test('estudio y biblioteca usan el mismo renderizador de OBS',()=>{
 for(const page of ['studio.html','biblioteca.html']){
  const markup=read(page);
  assert.match(markup,/src="\/overlay\.html\?preview=1"/);
  assert.match(markup,/type:'plobs-preview'/);
  assert.match(markup,/1920px/);
  assert.doesNotMatch(markup,/class="mock"/);
 }
});
test('la vista previa no consulta ni publica estado en vivo',()=>{
 const source=read('overlay.html');
 assert.match(source,/const previewMode=new URLSearchParams/);
 assert.match(source,/if\(previewMode\)\{/);
 assert.match(source,/event\.origin!==location\.origin/);
 assert.match(source,/else\{\s*async function tick\(/);
});
test('rotación de redes selecciona una sola entrada por turno',()=>{
 const source=read('overlay.html');
 assert.match(source,/const selected=allowed\?entries\[idx\]:null/);
 assert.match(source,/items\.replaceChildren\(\)/);
 assert.match(source,/selected\.phrase/);
 assert.match(source,/socialMarks\[selected\.network\]/);
});
