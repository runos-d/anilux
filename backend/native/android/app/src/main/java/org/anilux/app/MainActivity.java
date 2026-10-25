package org.anilux.app;

import android.Manifest;
import android.app.Activity;
import android.app.PictureInPictureParams;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.net.Uri;
import android.os.Bundle;
import android.util.Rational;
import android.webkit.*;
import android.widget.LinearLayout;
import android.widget.FrameLayout;
import android.view.View;
import androidx.webkit.WebViewCompat;
import androidx.webkit.WebViewFeature;
import java.util.*;
import org.json.JSONObject;

public class MainActivity extends Activity {
    private static final String BRIDGE_JS="(()=>{if(window.top!==window||window.aniluxNative||!window.AniLuxBridge)return;let next=0;const pending=new Map();AniLuxBridge.onmessage=e=>{const r=JSON.parse(e.data);const p=pending.get(r.id);if(p){pending.delete(r.id);r.ok?p.resolve():p.reject(Error('PiP failed'));}};window.aniluxNative={platform:'android',setPictureInPicture:enabled=>new Promise((resolve,reject)=>{const id=++next;pending.set(id,{resolve,reject});AniLuxBridge.postMessage(JSON.stringify({id,action:'pip',enabled}));setTimeout(()=>{if(pending.delete(id))reject(Error('PiP timeout'));},5000);})};})()";
    private WebView web;
    private String site;
    private ValueCallback<Uri[]> files;
    private PermissionRequest mediaPermission;
    private FrameLayout root;
    private View fullscreenVideo;
    private WebChromeClient.CustomViewCallback fullscreenCallback;
    private String origin(Uri uri) { return uri.getScheme()+"://"+uri.getAuthority(); }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        site=getString(org.anilux.app.R.string.site_url);
        root=new FrameLayout(this);root.setFitsSystemWindows(true);
        web=new WebView(this);root.addView(web,new FrameLayout.LayoutParams(-1,-1));setContentView(root);
        web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(true);
        web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.getSettings().setMediaPlaybackRequiresUserGesture(false);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web,true);
        if(WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            WebViewCompat.addWebMessageListener(web,"AniLuxBridge",Collections.singleton(site),(view,message,source,isMainFrame,reply)->{
                if(!isMainFrame||!origin(source).equals(site))return;
                try {
                    JSONObject command=new JSONObject(message.getData());
                    if(!command.optString("action").equals("pip"))return;
                    boolean enabled=command.getBoolean("enabled");
                    if(enabled&&!isInPictureInPictureMode()&&!enterPictureInPictureMode(new PictureInPictureParams.Builder().setAspectRatio(new Rational(16,9)).build()))throw new IllegalStateException("PiP unavailable");
                    else if(!enabled&&isInPictureInPictureMode())startActivity(new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT));
                    reply.postMessage(new JSONObject().put("id",command.getInt("id")).put("ok",true).toString());
                } catch(Exception ignored) {}
            });
        }
        if(WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT))
            WebViewCompat.addDocumentStartJavaScript(web,BRIDGE_JS,Collections.singleton(site));
        web.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){
                if(!request.isForMainFrame())return false;
                Uri uri=request.getUrl();if(origin(uri).equals(site))return false;
                if(request.hasGesture()&&Arrays.asList("https","http","mailto","tel").contains(uri.getScheme())){
                    try{startActivity(new Intent(Intent.ACTION_VIEW,uri));}catch(Exception ignored){}
                }
                return true;
            }
            @Override public void onPageFinished(WebView view,String url){
                if(!origin(Uri.parse(url)).equals(site))return;
                view.evaluateJavascript(BRIDGE_JS,null);
            }
        });
        web.setWebChromeClient(new WebChromeClient(){
            @Override public void onShowCustomView(View video,CustomViewCallback callback){
                if(fullscreenVideo!=null){callback.onCustomViewHidden();return;}
                fullscreenVideo=video;fullscreenCallback=callback;web.setVisibility(View.GONE);
                root.addView(video,new FrameLayout.LayoutParams(-1,-1));
            }
            @Override public void onHideCustomView(){hideFullscreen();}
            @Override public boolean onShowFileChooser(WebView view,ValueCallback<Uri[]> callback,FileChooserParams params){
                if(files!=null)files.onReceiveValue(null);files=callback;
                try{startActivityForResult(params.createIntent(),42);return true;}catch(Exception error){files=null;return false;}
            }
            @Override public void onPermissionRequest(PermissionRequest request){
                if(!origin(request.getOrigin()).equals(site)){request.deny();return;}
                if(mediaPermission!=null)mediaPermission.deny();
                mediaPermission=request;List<String> permissions=new ArrayList<>();
                for(String resource:request.getResources()){
                    if(resource.equals(PermissionRequest.RESOURCE_AUDIO_CAPTURE))permissions.add(Manifest.permission.RECORD_AUDIO);
                    if(resource.equals(PermissionRequest.RESOURCE_VIDEO_CAPTURE))permissions.add(Manifest.permission.CAMERA);
                }
                if(permissions.isEmpty()){request.deny();return;}requestPermissions(permissions.toArray(new String[0]),43);
            }
            @Override public void onPermissionRequestCanceled(PermissionRequest request){if(mediaPermission==request)mediaPermission=null;}
        });
        web.setDownloadListener((url,agent,disposition,mime,size)->{if(origin(Uri.parse(url)).equals(site))startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)));});
        if(state==null)web.loadUrl(site);else web.restoreState(state);
    }
    @Override public void onSaveInstanceState(Bundle state){web.saveState(state);super.onSaveInstanceState(state);}
    @Override public void onActivityResult(int code,int result,Intent data){super.onActivityResult(code,result,data);if(code==42&&files!=null){files.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result,data));files=null;}}
    @Override public void onRequestPermissionsResult(int code,String[] permissions,int[] results){super.onRequestPermissionsResult(code,permissions,results);if(code!=43||mediaPermission==null)return;List<String> granted=new ArrayList<>();for(String resource:mediaPermission.getResources()){String permission=resource.equals(PermissionRequest.RESOURCE_AUDIO_CAPTURE)?Manifest.permission.RECORD_AUDIO:resource.equals(PermissionRequest.RESOURCE_VIDEO_CAPTURE)?Manifest.permission.CAMERA:null;if(permission!=null&&checkSelfPermission(permission)==PackageManager.PERMISSION_GRANTED)granted.add(resource);}mediaPermission.grant(granted.toArray(new String[0]));mediaPermission=null;}
    @Override public void onPictureInPictureModeChanged(boolean active,Configuration config){super.onPictureInPictureModeChanged(active,config);web.evaluateJavascript("window.dispatchEvent(new CustomEvent('anilux-native-pip',{detail:"+active+"}))",null);}
    private void hideFullscreen(){if(fullscreenVideo==null)return;root.removeView(fullscreenVideo);fullscreenVideo=null;web.setVisibility(View.VISIBLE);if(fullscreenCallback!=null)fullscreenCallback.onCustomViewHidden();fullscreenCallback=null;}
    @Override public void onBackPressed(){if(fullscreenVideo!=null)hideFullscreen();else if(web.canGoBack())web.goBack();else super.onBackPressed();}
    @Override public void onDestroy(){if(mediaPermission!=null)mediaPermission.deny();if(files!=null)files.onReceiveValue(null);web.destroy();super.onDestroy();}
}
