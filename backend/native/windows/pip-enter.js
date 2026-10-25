(() => {
  const videos=[...document.querySelectorAll('video')];
  const video=videos.find(v=>!v.paused&&v.readyState>=2&&v.videoWidth>0)||videos.find(v=>v.readyState>=2&&v.videoWidth>0);
  if(!video)return false;
  return video.requestPictureInPicture().then(()=>true);
})();
