(() => {
  if (window.top !== window || !window.chrome?.webview) return;
  let sequence = 0;
  const pending = new Map();
  window.chrome.webview.addEventListener('message', event => {
    const result = event.data;
    const request = pending.get(result?.id);
    if (!request) return;
    clearTimeout(request.timer); pending.delete(result.id);
    result.ok ? request.resolve() : request.reject(Error('PiP unavailable'));
  });
  window.aniluxNative = Object.freeze({platform:'desktop', setPictureInPicture(enabled) {
    if(typeof enabled !== 'boolean')return Promise.reject(Error('Invalid PiP action'));
    return new Promise((resolve,reject) => {
      const id=++sequence;
      const timer=setTimeout(()=>{pending.delete(id);reject(Error('PiP timeout'));},5000);
      pending.set(id,{resolve,reject,timer});
      window.chrome.webview.postMessage({id,action:'pip',enabled});
    });
  }});
})();
