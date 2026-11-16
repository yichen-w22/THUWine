"""Local-only live preview; no remote uploads and no image export."""
from __future__ import annotations
import datetime as dt
import json
import secrets
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

LIVE_SCRIPT=r'''<script>
(()=>{
let revision=__PB_REVISION__,reloading=false;
const key='pb-scroll:'+location.pathname;
const remembered=sessionStorage.getItem(key);
if(remembered){sessionStorage.removeItem(key);requestAnimationFrame(()=>window.scrollTo(0,Number(remembered)));}
const box=document.createElement('div');
box.style.cssText='position:fixed;bottom:12px;right:12px;max-width:440px;padding:9px 14px;background:#fff9;border:1px solid #ddd;border-radius:6px;color:#666;font:13px/1.6 sans-serif;z-index:9999;backdrop-filter:blur(8px)';
box.textContent='自动预览：修改正文.md并保存';document.body.append(box);
async function poll(){
 try{
  const state=await(await fetch('/__status',{cache:'no-store'})).json();
  box.textContent=state.error?'未更新：'+state.error:state.building?'正在更新预览…':'自动预览已连接 · '+state.updated;
  box.style.color=state.error?'#a12222':'#666';
  if(state.revision!==revision&&!reloading){reloading=true;sessionStorage.setItem(key,String(window.scrollY));location.reload();return;}
 }catch(e){box.textContent='自动预览未连接，请重新启动“开始编辑”';}
 setTimeout(poll,1000);
}
poll();
})();</script>'''

def signature(directory,root):
    paths=[directory/'post.json',directory/'正文.md',root/'theme.json']
    try:
        data=json.loads((directory/'post.json').read_text(encoding='utf-8-sig'))
        source=data.get('text_source')
        if source:paths.append(directory/source)
        paths.extend(directory/item['path'] for item in data.get('assets',{}).values())
    except (OSError,ValueError,KeyError):pass
    result=[]
    for p in paths:
        try:s=p.stat();result.append((str(p),s.st_mtime_ns,s.st_size))
        except OSError:result.append((str(p),None,None))
    return tuple(result)

class Watcher:
    def __init__(self,directory,root,project_factory,build):
        self.directory=directory;self.root=root;self.project_factory=project_factory;self.build=build
        self.lock=threading.Lock();self.stop=threading.Event()
        self.state={'project':directory.name,'revision':0,'digest':'','building':False,'error':'','updated':''}
        self.initial_signature=signature(directory,root)
    def snapshot(self):
        with self.lock:return dict(self.state)
    def rebuild(self):
        with self.lock:self.state['building']=True
        try:
            p=self.project_factory(self.directory);self.build(p,'Markdown/素材保存后自动更新')
            with self.lock:
                self.state.update(revision=self.state['revision']+1,digest=p.digest,error='',updated=dt.datetime.now().strftime('%H:%M:%S'))
            return True
        except Exception as exc:
            with self.lock:self.state['error']=str(exc)
            print('预览未更新（保留上次有效页面）：',exc,flush=True);return False
        finally:
            with self.lock:self.state['building']=False
    def run(self):
        seen=self.initial_signature;pending=None;changed_at=0
        while not self.stop.wait(.25):
            current=signature(self.directory,self.root)
            if current!=seen:
                seen=current;pending=current;changed_at=time.monotonic()
            if pending is not None and time.monotonic()-changed_at>=.6:
                self.rebuild();pending=None

def request_status(port):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f'http://127.0.0.1:{port}/__status',timeout=2) as r:return json.load(r)

def stop_server(directory):
    info=directory/'preview/server.json'
    if not info.exists():raise ValueError('本项目没有运行中的预览记录。')
    data=json.loads(info.read_text(encoding='utf-8'))
    req=urllib.request.Request(f'http://127.0.0.1:{data["port"]}/__stop',method='POST',headers={'X-Preview-Token':data['token']})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req,timeout=3) as response:
        if response.status!=200:raise ValueError('停止预览失败。')
    print('本项目的自动预览已停止。')

def serve(directory,root,project_factory,build,port=8876,open_browser=False):
    info=directory/'preview/server.json'
    if info.exists():
        try:
            saved=json.loads(info.read_text(encoding='utf-8'));old=request_status(saved['port'])
            if old.get('project')==directory.name and old.get('service_id')==saved.get('service_id'):
                url=f'http://127.0.0.1:{saved["port"]}/'
                print('自动预览已在运行：'+url,flush=True)
                if open_browser:webbrowser.open(url)
                return
        except (OSError,ValueError,urllib.error.URLError):pass
    watcher=Watcher(directory,root,project_factory,build)
    if not watcher.rebuild() and not (directory/'preview/index.html').exists():raise ValueError(watcher.snapshot()['error'])
    token=secrets.token_urlsafe(32);service_id=secrets.token_hex(12)
    class Handler(BaseHTTPRequestHandler):
        def permitted(self):
            host=self.headers.get('Host','').split(':',1)[0]
            return host in ('127.0.0.1','localhost')
        def send(self,code,body,content_type='application/json; charset=utf-8'):
            if isinstance(body,str):body=body.encode('utf-8')
            self.send_response(code);self.send_header('Content-Type',content_type)
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
            try:self.wfile.write(body)
            except (ConnectionError,BrokenPipeError):pass
        def do_GET(self):
            if not self.permitted():self.send(403,'{}');return
            path=self.path.split('?',1)[0]
            if path=='/__status':
                state=watcher.snapshot();state['service_id']=service_id;self.send(200,json.dumps(state,ensure_ascii=False));return
            if path in ('/','/index.html'):
                try:
                    with watcher.lock:
                        html=(directory/'preview/index.html').read_text(encoding='utf-8')
                        revision=watcher.state['revision']
                    html=html.replace('</html>',LIVE_SCRIPT.replace('__PB_REVISION__',str(revision))+'</html>')
                    self.send(200,html,'text/html; charset=utf-8')
                except OSError as exc:self.send(503,json.dumps({'error':str(exc)}))
                return
            self.send(404,'{}')
        def do_POST(self):
            if not self.permitted() or self.path!='/__stop' or not secrets.compare_digest(self.headers.get('X-Preview-Token',''),token):
                self.send(403,'{}');return
            self.send(200,'{"stopped":true}')
            threading.Thread(target=server.shutdown,daemon=True).start()
        def log_message(self,*args):pass
    server=None
    for candidate in range(port,port+20):
        try:server=ThreadingHTTPServer(('127.0.0.1',candidate),Handler);break
        except OSError as exc:
            if getattr(exc,'winerror',None)==10013:raise ValueError('系统不允许开启本地预览端口，请检查本机回环网络权限。') from exc
    if server is None:raise ValueError('本地预览端口被占用，请使用 --port 指定其他端口。')
    actual_port=server.server_address[1]
    record={'port':actual_port,'token':token,'service_id':service_id,'project':directory.name}
    info.write_text(json.dumps(record),encoding='utf-8')
    thread=threading.Thread(target=watcher.run,daemon=True);thread.start()
    url=f'http://127.0.0.1:{actual_port}/'
    print('自动预览：'+url+'\n在 Typora 中修改 '+str(directory/'正文.md')+' 并保存。\n关闭此窗口或运行停止预览.cmd可停止服务。',flush=True)
    if open_browser:webbrowser.open(url)
    try:server.serve_forever(poll_interval=.3)
    except KeyboardInterrupt:pass
    finally:
        watcher.stop.set();thread.join(timeout=3);server.server_close()
        try:
            if json.loads(info.read_text()).get('service_id')==service_id:info.unlink()
        except OSError:pass
