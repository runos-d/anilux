import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_windows import compile_host

work = ROOT.parent / 'data/local_release/native-webview2/self-test'
work.mkdir(parents=True, exist_ok=True)
report = work / 'result.json'
source = (ROOT / 'windows/Program.cs').read_text(encoding='utf-8')
source = source.replace('Text="AniLux"; Width=1280;', 'Opacity=0; ShowInTaskbar=false; Text="AniLux"; Width=1280;')
source = source.replace('Shown += async (s,e)=>await Initialize();', '''Shown += async (s,e)=> {
    try { await Initialize(); await SelfTest(); }
    catch(Exception error) { File.WriteAllText(Environment.GetEnvironmentVariable("ANILUX_QA_REPORT"),json.Serialize(new {passed=false,error=error.ToString()})); }
    finally {Close();}
};''')
source = source.replace('core.Navigate(server);', 'core.Navigate(server+"/anime/kovboy-bibop/watch");')
source = re.sub(r'} catch\(WebView2RuntimeNotFoundException\) \{.*?\n    \}\n    \[STAThread\]', '} catch {throw;}\n    }\n    [STAThread]', source, flags=re.S)
test = r'''
    async Task<Dictionary<string,object>> Inspect(MediaContext context,string expression,bool gesture=false) {
        var result=Parse(await Protocol(context.Session,"Runtime.evaluate",new {expression=expression,contextId=context.Id,userGesture=gesture,awaitPromise=true,returnByValue=true}));
        object row;
        if(result.TryGetValue("result",out row)) {
            var value=row as Dictionary<string,object>;
            if(value!=null && value.ContainsKey("value"))return value["value"] as Dictionary<string,object>;
        }
        return null;
    }
    async Task ButtonState(bool active) {
        for(int i=0;i<50;i++) {
            if(await web.ExecuteScriptAsync("document.querySelector('.system-pip-btn')?.getAttribute('aria-pressed')==='"+(active?"true":"false")+"'")=="true")return;
            await Task.Delay(200);
        }
        throw new Exception("Toolbar state did not become "+active+" "+await web.ExecuteScriptAsync("document.querySelector('.player-window-error')?.textContent"));
    }
    async Task SelfTest() {
        MediaContext provider=null;
        for(int i=0;i<120 && provider==null;i++) {
            foreach(var context in contexts.Values.ToArray())try {
                await Inspect(context,"(()=>{document.querySelector('a.play_button')?.click();return {ok:true}})()",true);
                var state=await Inspect(context,"({ready:[...document.querySelectorAll('video')].some(v=>!v.paused&&v.readyState>=2&&v.videoWidth>0)})");
                if(state!=null && Convert.ToBoolean(state["ready"])) {provider=context;break;}
            }catch{}
            if(provider==null)await Task.Delay(500);
        }
        if(provider==null)throw new Exception("No decoded video. Context count: "+contexts.Count);
        await Inspect(provider,"(()=>{window.__qaVideo=[...document.querySelectorAll('video')].find(v=>!v.paused&&v.videoWidth>0);return {ok:true};})()");
        var samples=new List<object>();
        for(int cycle=0;cycle<3;cycle++) {
            await Task.Delay(6500);
            await web.ExecuteScriptAsync("document.querySelector('.system-pip-btn').click()");
            await ButtonState(true);
            var entered=await Inspect(provider,"({pip:document.pictureInPictureElement===window.__qaVideo,time:window.__qaVideo.currentTime,paused:window.__qaVideo.paused})");
            if(!Convert.ToBoolean(entered["pip"])||Convert.ToBoolean(entered["paused"]))throw new Exception("Native PiP did not contain the playing video");
            await web.ExecuteScriptAsync("document.querySelector('.system-pip-btn').click()");
            await ButtonState(false);
            var exited=await Inspect(provider,"({pip:!!document.pictureInPictureElement,time:window.__qaVideo.currentTime,same:document.contains(window.__qaVideo)})");
            if(Convert.ToBoolean(exited["pip"])||!Convert.ToBoolean(exited["same"])||Convert.ToDouble(exited["time"])<Convert.ToDouble(entered["time"])-0.5)throw new Exception("Return replaced or reset the video");
            samples.Add(new {cycle=cycle,entered=entered,exited=exited});
        }
        File.WriteAllText(Environment.GetEnvironmentVariable("ANILUX_QA_REPORT"),json.Serialize(new {passed=true,samples=samples}));
    }
'''
source = source.replace('    [STAThread] static int Main', test+'\n    [STAThread] static int Main')
code = work / 'Program.cs'
code.write_text(source, encoding='utf-8-sig')
compile_host('http://127.0.0.1:8099', work, code)
env = {**os.environ, 'ANILUX_PROFILE': str(work / 'profile'), 'ANILUX_QA_REPORT': str(report)}
env.pop('WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS', None)
startup = subprocess.STARTUPINFO()
startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startup.wShowWindow = 0
subprocess.run([str(work / 'anilux.exe')], env=env, startupinfo=startup, timeout=180, check=True)
data = json.loads(report.read_text())
print(json.dumps(data, ensure_ascii=False))
if not data['passed']: sys.exit(1)
