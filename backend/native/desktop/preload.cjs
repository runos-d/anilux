const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('aniluxNative',{
  platform:'desktop',setPictureInPicture:enabled=>ipcRenderer.invoke('anilux:pip',enabled),
  server:()=>ipcRenderer.invoke('anilux:server'),configureServer:url=>ipcRenderer.invoke('anilux:configure-server',url)
});
