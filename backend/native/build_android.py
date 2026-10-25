import json,os,secrets,shutil,subprocess,tempfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parent

def build(args):
    data=Path(os.environ.get('DATA_DIR','/app/data'))
    signing=data/'native_signing';signing.mkdir(parents=True,exist_ok=True,mode=0o700)
    password_file=signing/'android-password'
    if not password_file.exists():
        fd=os.open(password_file,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as out:out.write(secrets.token_urlsafe(40))
    password=password_file.read_text()
    keystore=signing/'android-release.jks'
    env={**os.environ,'ANILUX_KEYSTORE_PASSWORD':password,'ANILUX_KEYSTORE_PATH':str(keystore)}
    if not keystore.exists():
        subprocess.run(['keytool','-genkeypair','-keystore',str(keystore),'-storepass:env','ANILUX_KEYSTORE_PASSWORD','-keypass:env','ANILUX_KEYSTORE_PASSWORD','-alias','anilux','-keyalg','RSA','-keysize','3072','-validity','10000','-dname','CN=AniLux'],env=env,check=True)
        keystore.chmod(0o600)
    with tempfile.TemporaryDirectory(prefix='anilux-android-') as temporary:
        work=Path(temporary)
        shutil.copytree(ROOT/'android',work,dirs_exist_ok=True,ignore=shutil.ignore_patterns('build','.gradle'))
        resources=work/'app/src/main/res';(resources/'values').mkdir(parents=True,exist_ok=True)
        (resources/'values/strings.xml').write_text('<resources><string name="site_url">'+escape(args.site_url)+'</string></resources>',encoding='utf-8')
        (resources/'drawable').mkdir(exist_ok=True);shutil.copyfile(ROOT/'desktop/icon.png',resources/'drawable/icon.png')
        parts=[int(p) for p in args.version.split('.')]
        if len(parts)!=3 or any(p<0 or p>999 for p in parts):raise ValueError('Use a three-part numeric version')
        version_code=parts[0]*1000000+parts[1]*1000+parts[2]+1
        gradle=work/'app/build.gradle';gradle.write_text(gradle.read_text().replace("versionName '0.1.0'",f"versionName '{args.version}'").replace('versionCode 1;',f'versionCode {version_code};'))
        subprocess.run(['gradle','--no-daemon','--max-workers=2','--console=plain','--info',
            '-Djava.net.preferIPv4Stack=true','-Dorg.gradle.internal.http.connectionTimeout=20000',
            '-Dorg.gradle.internal.http.socketTimeout=120000','assembleRelease'],cwd=work,env=env,check=True)
        apk=work/'app/build/outputs/apk/release/app-release.apk'
        subprocess.run([str(Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0/apksigner'),'verify','--verbose',str(apk)],check=True)
        shutil.copyfile(apk,args.output)
