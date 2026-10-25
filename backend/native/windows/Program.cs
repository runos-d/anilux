using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

internal class AppWindow : Form {
    readonly WebView2 web = new WebView2();
    readonly JavaScriptSerializer json = new JavaScriptSerializer();
    readonly Dictionary<string, MediaContext> contexts = new Dictionary<string, MediaContext>();
    readonly MenuStrip menu = new MenuStrip();
    Rectangle restoredBounds;
    FormWindowState restoredState;
    readonly string assets = AppDomain.CurrentDomain.BaseDirectory;
    readonly string profile = Environment.GetEnvironmentVariable("ANILUX_PROFILE") ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AniLux");
    string server;
    class MediaContext { public string Session; public int Id; }
    Dictionary<string,object> Parse(string value) { return json.Deserialize<Dictionary<string,object>>(value); }
    static string Origin(string value) {
        var uri = new Uri(value);
        if (uri.Scheme != "https" && uri.Scheme != "http") throw new ArgumentException("Требуется адрес HTTP или HTTPS");
        return uri.GetLeftPart(UriPartial.Authority);
    }
    bool Allowed(string value) {
        try {
            if (Origin(value) == server) return true;
            return new [] {"kodikplayer.com","kodik.cc","kodik.info","kodik.biz","kodikai.com"}.Contains(new Uri(value).Host);
        } catch { return false; }
    }
    public AppWindow() {
        Text="AniLux"; Width=1280; Height=850; MinimumSize=new Size(360,500);
        BackColor=Color.FromArgb(21,17,26);
        var icon=Path.Combine(assets,"icon.ico"); if(File.Exists(icon))Icon=new Icon(icon);
        Directory.CreateDirectory(profile);
        server=Origin(Convert.ToString(Parse(File.ReadAllText(Path.Combine(assets,"app.config.json")))["siteUrl"]));
        var preferences=Path.Combine(profile,"server.txt");
        if(File.Exists(preferences))try {server=Origin(File.ReadAllText(preferences));}catch {}
        menu.Items.Add("На главную",null,(s,e)=> {if(web.CoreWebView2!=null)web.CoreWebView2.Navigate(server);});
        menu.Items.Add("Обновить",null,(s,e)=> {if(web.CoreWebView2!=null)web.Reload();});
        menu.Items.Add("Адрес сайта",null,(s,e)=>ChangeServer());
        Controls.Add(web); web.Dock=DockStyle.Fill; Controls.Add(menu); MainMenuStrip=menu;
        Shown += async (s,e)=>await Initialize();
        FormClosed += (s,e)=>web.Dispose();
    }
    void ChangeServer() {
        using(var dialog=new Form {Text="Адрес AniLux",Width=480,Height=155,StartPosition=FormStartPosition.CenterParent,MinimizeBox=false,MaximizeBox=false}) {
            var input=new TextBox {Text=server,Left=16,Top=15,Width=430};
            var save=new Button {Text="Открыть",Left=330,Top=55,Width=115,DialogResult=DialogResult.OK};
            dialog.Controls.Add(input);dialog.Controls.Add(save);dialog.AcceptButton=save;
            if(dialog.ShowDialog(this)!=DialogResult.OK)return;
            try {
                var uri=new Uri(input.Text.Trim());
                if(uri.UserInfo!="" || uri.AbsolutePath!="/" || uri.Query!="" || uri.Fragment!="")throw new ArgumentException("Укажите адрес сайта без пути");
                server=Origin(uri.AbsoluteUri); File.WriteAllText(Path.Combine(profile,"server.txt"),server);
                contexts.Clear(); web.CoreWebView2.Navigate(server);
            } catch(Exception error) { MessageBox.Show(this,error.Message,"Адрес сайта"); }
        }
    }
    async Task<string> Protocol(string session,string method,object parameters) {
        var value=json.Serialize(parameters);
        return String.IsNullOrEmpty(session) ? await web.CoreWebView2.CallDevToolsProtocolMethodAsync(method,value)
            : await web.CoreWebView2.CallDevToolsProtocolMethodForSessionAsync(session,method,value);
    }
    async Task Initialize() {
        try {
            var environment=await CoreWebView2Environment.CreateAsync(null,Path.Combine(profile,"browser"));
            await web.EnsureCoreWebView2Async(environment);
            var core=web.CoreWebView2;
            core.Settings.AreDevToolsEnabled=false;
            core.ContainsFullScreenElementChanged+=(s,e)=> {
                if(core.ContainsFullScreenElement) {
                    restoredBounds=Bounds;restoredState=WindowState;menu.Visible=false;
                    WindowState=FormWindowState.Normal;FormBorderStyle=FormBorderStyle.None;WindowState=FormWindowState.Maximized;
                } else {
                    WindowState=FormWindowState.Normal;FormBorderStyle=FormBorderStyle.Sizable;
                    Bounds=restoredBounds;WindowState=restoredState;menu.Visible=true;
                }
            };
            core.NewWindowRequested+=(s,e)=>e.Handled=true;
            core.NavigationStarting+=(s,e)=> {
                try {if(Origin(e.Uri)==server)return;}catch {}
                e.Cancel=true;
                Uri url;
                if(e.IsUserInitiated && Uri.TryCreate(e.Uri,UriKind.Absolute,out url) && new [] {"https","mailto","tel"}.Contains(url.Scheme))
                    Process.Start(new ProcessStartInfo(e.Uri) {UseShellExecute=true});
            };
            core.NavigationCompleted+=(s,e)=> {
                if(!e.IsSuccess && e.WebErrorStatus!=CoreWebView2WebErrorStatus.OperationCanceled)
                    Text="AniLux - нет подключения. Проверьте сеть или адрес сайта";
                else Text="AniLux";
            };
            core.PermissionRequested+=(s,e)=> {
                bool own=false;try{own=Origin(e.Uri)==server;}catch{}
                bool media=e.PermissionKind==CoreWebView2PermissionKind.Camera||e.PermissionKind==CoreWebView2PermissionKind.Microphone;
                e.State=own && media && MessageBox.Show(this,"Разрешить сайту камеру или микрофон?", "AniLux",MessageBoxButtons.YesNo)==DialogResult.Yes
                    ? CoreWebView2PermissionState.Allow : CoreWebView2PermissionState.Deny;
            };
            core.DownloadStarting+=(s,e)=> {
                using(var picker=new SaveFileDialog {FileName=Path.GetFileName(e.ResultFilePath),InitialDirectory=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),"Downloads")}) {
                    e.Handled=true;
                    if(picker.ShowDialog(this)==DialogResult.OK)e.ResultFilePath=picker.FileName;else e.Cancel=true;
                }
            };
            core.GetDevToolsProtocolEventReceiver("Runtime.executionContextCreated").DevToolsProtocolEventReceived+=(s,e)=> {
                var context=(Dictionary<string,object>)Parse(e.ParameterObjectAsJson)["context"];
                object auxiliary;
                if(context.TryGetValue("auxData",out auxiliary)) {
                    var data=auxiliary as Dictionary<string,object>;
                    if(data!=null && data.ContainsKey("isDefault") && !Convert.ToBoolean(data["isDefault"]))return;
                }
                var id=Convert.ToInt32(context["id"]);
                if(Allowed(Convert.ToString(context["origin"])))contexts[e.SessionId+":"+id]=new MediaContext {Session=e.SessionId,Id=id};
            };
            core.GetDevToolsProtocolEventReceiver("Runtime.executionContextDestroyed").DevToolsProtocolEventReceived+=(s,e)=> {
                contexts.Remove(e.SessionId+":"+Convert.ToString(Parse(e.ParameterObjectAsJson)["executionContextId"]));
            };
            core.GetDevToolsProtocolEventReceiver("Runtime.executionContextsCleared").DevToolsProtocolEventReceived+=(s,e)=> {
                foreach(var key in contexts.Where(pair=>pair.Value.Session==e.SessionId).Select(pair=>pair.Key).ToArray())contexts.Remove(key);
            };
            core.GetDevToolsProtocolEventReceiver("Target.attachedToTarget").DevToolsProtocolEventReceived+=async(s,e)=> {
                try { var session=Convert.ToString(Parse(e.ParameterObjectAsJson)["sessionId"]);await Protocol(session,"Runtime.enable",new {}); }
                catch { /* A provider frame may navigate away during attachment. */ }
            };
            await Protocol("","Runtime.enable",new {});
            await Protocol("","Target.setAutoAttach",new {autoAttach=true,waitForDebuggerOnStart=false,flatten=true});
            await core.AddScriptToExecuteOnDocumentCreatedAsync(File.ReadAllText(Path.Combine(assets,"bridge.js")));
            core.WebMessageReceived+=async(s,e)=> {
                Dictionary<string,object> command;
                try {if(Origin(e.Source)!=server)return;command=Parse(e.WebMessageAsJson);}catch{return;}
                if(!command.ContainsKey("action") || Convert.ToString(command["action"])!="pip" || !command.ContainsKey("enabled") || !(command["enabled"] is bool))return;
                bool ok=false;
                var code=File.ReadAllText(Path.Combine(assets,(bool)command["enabled"]?"pip-enter.js":"pip-exit.js"));
                foreach(var context in contexts.Values.ToArray()) {
                    try {
                        var evaluated=Parse(await Protocol(context.Session,"Runtime.evaluate",new {expression=code,contextId=context.Id,userGesture=true,awaitPromise=true,returnByValue=true}));
                        object result;
                        if(evaluated.TryGetValue("result",out result)) {
                            var row=result as Dictionary<string,object>;
                            if(row!=null && row.ContainsKey("value") && row["value"] is bool && (bool)row["value"]){ok=true;break;}
                        }
                    } catch { /* Continue to the decoded video in another permitted frame. */ }
                }
                object id; if(command.TryGetValue("id",out id))core.PostWebMessageAsJson(json.Serialize(new {id=id,ok=ok}));
            };
            core.Navigate(server);
        } catch(WebView2RuntimeNotFoundException) {
            if(MessageBox.Show(this,"Для AniLux нужен Microsoft Edge WebView2. Открыть страницу установки?","AniLux",MessageBoxButtons.YesNo)==DialogResult.Yes)
                Process.Start(new ProcessStartInfo("https://developer.microsoft.com/microsoft-edge/webview2/"){UseShellExecute=true});
            Close();
        } catch(Exception error) {MessageBox.Show(this,"Не удалось запустить приложение: "+error.Message,"AniLux");Close();}
    }
    [STAThread] static int Main(string[] args) {
        if(args.Contains("--check-runtime"))try {CoreWebView2Environment.GetAvailableBrowserVersionString();return 0;}catch{return 2;}
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new AppWindow());return 0;
    }
}
