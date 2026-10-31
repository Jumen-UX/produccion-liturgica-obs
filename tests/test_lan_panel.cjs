// Run with: node --test tests/test_lan_panel.cjs
// Executes the real panel script with simulated DOM, HTTP and timer boundaries.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../panel.html'),'utf8');
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(match=>match[1]);
const source=scripts.find(script=>script.includes('/* Administración LAN:'));
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function setup(){
  const nodes=new Map(),timers=[];
  function element(){return {value:'',checked:false,hidden:false,disabled:false,textContent:'',children:[],listeners:{},
    addEventListener(type,callback){(this.listeners[type]??=[]).push(callback)},
    emit(type){for(const callback of this.listeners[type]||[])callback()},
    replaceChildren(){this.children=[];this.value=''},
    append(child){this.children.push(child);if(this.children.length===1)this.value=child.value},
    getAttribute(key){return this[key]??null}}}
  const get=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id)};
  let config={enabled:true,port:8766,operator_configured:true,sessions:0,urls:['http://192.168.1.40:8766/login.html']};
  const requests=[];
  const app={get,timers,requests,fail:false,hold:null,setConfig(value){config=value},config:()=>config};
  vm.runInNewContext(source,{URL,encodeURIComponent,document:{getElementById:get,createElement:element},confirm:()=>true,
    setInterval(callback){timers.push(callback)},
    async fetch(url,options){
      requests.push({url,options});
      if(options?.method==='POST'){
        if(app.hold)await app.hold;
        if(app.fail)return {ok:false,json:async()=>({error:'Puerto ocupado'})};
        const values=JSON.parse(options.body);
        config={...config,...values};
        config.urls=config.enabled?[`http://192.168.1.40:${config.port}/login.html`]:[];
        return {ok:true,json:async()=>({config})};
      }
      return {ok:true,json:async()=>config};
    }});
  return app;
}
function edit(app,id,value,property='value'){app.get(id)[property]=value;app.get(id).emit('input')}
test('all inline scripts parse',()=>{for(const script of scripts)new vm.Script(script)});
test('changing the saved port reloads QR and link together',async()=>{
  const app=setup();await flush();const initial=app.get('lanQr').src;
  edit(app,'lanPort','8767');app.get('lanSave').emit('click');await flush();
  assert.notEqual(app.get('lanQr').src,initial);
  assert.equal(new URL(app.get('lanQr').src,'http://localhost').searchParams.get('port'),'8767');
  assert.equal(app.get('lanLink').href,'http://192.168.1.40:8767/login.html');
});
test('polling updates status without discarding unsaved controls or issuing commands',async()=>{
  const app=setup();await flush();edit(app,'lanEnabled',false,'checked');edit(app,'lanPort','9000');
  app.setConfig({...app.config(),sessions:3});await app.timers[0]();
  assert.equal(app.get('lanEnabled').checked,false);assert.equal(app.get('lanPort').value,'9000');
  assert.match(app.get('lanMessage').textContent,/3 sesión/);
  assert.equal(app.get('lanSave').textContent,'Guardar desactivación');
  assert.equal(app.requests.filter(r=>r.options?.method==='POST').length,0);
});
test('failed saves preserve edits for retry',async()=>{
  const app=setup();await flush();edit(app,'lanPort','9000');app.fail=true;
  app.get('lanSave').emit('click');await flush();await app.timers[0]();
  assert.equal(app.get('lanPort').value,'9000');assert.equal(app.get('lanSave').disabled,false);
});
test('session revocation does not save or discard pending form edits',async()=>{
  const app=setup();await flush();edit(app,'lanPort','9000');edit(app,'lanOperatorPassword','pending-password');
  app.get('lanRevoke').emit('click');await flush();await app.timers[0]();
  assert.equal(app.get('lanPort').value,'9000');assert.equal(app.get('lanOperatorPassword').value,'pending-password');
  assert.deepEqual(JSON.parse(app.requests.find(r=>r.options?.method==='POST').options.body),{revoke_sessions:true});
});
test('edits made during a save survive its response and subsequent polling',async()=>{
  const app=setup();await flush();let release;app.hold=new Promise(resolve=>release=resolve);
  edit(app,'lanPort','8767');app.get('lanSave').emit('click');edit(app,'lanPort','9000');
  release();await flush();await app.timers[0]();assert.equal(app.get('lanPort').value,'9000');
});
test('a successful save allows future server changes to update a clean form',async()=>{
  const app=setup();await flush();edit(app,'lanPort','8767');app.get('lanSave').emit('click');await flush();
  app.setConfig({...app.config(),port:9000,enabled:false,urls:[]});await app.timers[0]();
  assert.equal(Number(app.get('lanPort').value),9000);assert.equal(app.get('lanEnabled').checked,false);
});
