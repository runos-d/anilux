const {app, BrowserWindow, ipcMain, Menu, shell, dialog} = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const config = require('./app.config.json');
let main;
let server;
const offline = pathToFileURL(path.join(__dirname, 'offline.html')).href;
function normalize(value) {
  const url = new URL(value);
  if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.pathname!=='/'||url.search||url.hash)
    throw new Error('Укажите адрес сайта без пути, например https://example.org');
  return url.origin;
}
function trusted(event) {
  return event.sender === main?.webContents && event.senderFrame === main.webContents.mainFrame &&
    (new URL(event.senderFrame.url).origin === server || event.senderFrame.url === offline);
}
function loadSite() { main.loadURL(server).catch(()=>main.loadURL(offline)); }
const pipCode = enabled => enabled ? `(() => {
 const videos=[...document.querySelectorAll('video')];
 const v=videos.find(v=>!v.paused&&v.readyState>=2&&v.videoWidth>0)||videos.find(v=>v.readyState>=2&&v.videoWidth>0);
 if(!v)return false;
 return v.requestPictureInPicture().then(()=>true);
})()` : `document.pictureInPictureElement ? document.exitPictureInPicture().then(()=>true) : false`;
app.whenReady().then(()=>{
  const preference = path.join(app.getPath('userData'), 'server.json');
  try {server=normalize(JSON.parse(fs.readFileSync(preference, 'utf8')).siteUrl);}catch{server=normalize(config.siteUrl);}
  main=new BrowserWindow({width:1280,height:850,minWidth:360,minHeight:500,backgroundColor:'#15111a',
    icon:path.join(__dirname,'icon.png'),webPreferences:{preload:path.join(__dirname,'preload.cjs'),
      nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true}});
  main.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  main.webContents.on('will-navigate',(event,url)=>{
    if(new URL(url).origin!==server){event.preventDefault();if(url.startsWith('https:'))void shell.openExternal(url);}
  });
  main.webContents.session.setPermissionRequestHandler((contents,permission,callback,details)=>{
    let own=false;
    try{own=contents===main.webContents&&new URL(details.requestingUrl).origin===server;}catch{}
    if(!own){callback(false);return;}
    if(permission==='notifications'){callback(true);return;}
    if(permission==='media'){
      void dialog.showMessageBox(main,{type:'question',buttons:['Не разрешать','Разрешить'],defaultId:0,cancelId:0,
        title:'Разрешение AniLux',message:'Разрешить сайту использовать камеру или микрофон?',detail:server}).then(result=>callback(result.response===1));
      return;
    }
    callback(false);
  });
  main.webContents.on('did-fail-load',(_event,code,_description,url,isMainFrame)=>{
    if(isMainFrame&&code!==-3&&url!==offline)void main.loadURL(offline);
  });
  ipcMain.handle('anilux:server',event=>{if(!trusted(event))throw Error('Untrusted frame');return server;});
  ipcMain.handle('anilux:configure-server',(event,value)=>{
    if(!trusted(event)||event.senderFrame.url!==offline)throw Error('Untrusted frame');
    server=normalize(value);fs.writeFileSync(preference,JSON.stringify({siteUrl:server}));loadSite();
  });
  ipcMain.handle('anilux:pip',async(event,enabled)=>{
    if(!trusted(event)||typeof enabled!=='boolean'||event.senderFrame.url===offline)throw Error('Untrusted frame');
    const frames=main.webContents.mainFrame.framesInSubtree.filter(frame=>{
      try {const u=new URL(frame.url);return u.origin===server||['kodikplayer.com','kodik.cc','kodik.info','kodik.biz','kodikai.com'].includes(u.hostname);}catch{return false;}
    });
    let failure;
    for(const frame of frames){
      try{if(await frame.executeJavaScript(pipCode(enabled),true))return;}catch(error){failure=error;}
    }
    if(failure)throw failure;
    throw Error(enabled?'Сначала запустите видео.':'Окно уже закрыто.');
  });
  Menu.setApplicationMenu(Menu.buildFromTemplate([{label:'AniLux',submenu:[
    {label:'На главную',click:loadSite},{label:'Адрес сайта',click:()=>main.loadURL(offline)},
    {type:'separator'},{role:'reload',label:'Обновить'},{role:'togglefullscreen',label:'Полный экран'},
    {type:'separator'},{role:'quit',label:'Выйти'}]}]));
  loadSite();
});
app.on('window-all-closed',()=>app.quit());
