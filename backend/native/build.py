import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUFFIXES={'windows':'.exe','android':'.apk','deb':'.deb','appimage':'.AppImage','flatpak':'.flatpak'}


def artifact_cache(args):
    if args.target=='ios':return None
    inputs={
        'windows':['windows','build_windows.py','desktop/icon.png'],
        'android':['android','build_android.py','desktop/icon.png'],
        'deb':['desktop'], 'appimage':['desktop'], 'flatpak':['desktop','build_flatpak.py'],
    }[args.target]+['build.py','builder.Dockerfile']
    digest=hashlib.sha256(json.dumps([args.target,args.site_url,args.version]).encode())
    files=set()
    for relative in inputs:
        entry=ROOT/relative
        if entry.is_file():files.add(entry)
        else:
            for base,dirs,names in os.walk(entry):
                dirs[:]=sorted(d for d in dirs if d not in ('node_modules','dist','build','.gradle','__pycache__'))
                files.update(Path(base)/name for name in names)
    for file in sorted(files):
        digest.update(file.relative_to(ROOT).as_posix().encode());digest.update(file.read_bytes())
    data=Path(os.environ.get('DATA_DIR',ROOT.parent/'data'))
    if args.target=='android':
        keystore=data/'native_signing/android-release.jks'
        digest.update(keystore.read_bytes() if keystore.exists() else b'no-signing-key')
    return data/'native_cache/installers'/args.target/digest.hexdigest()/('installer'+SUFFIXES[args.target])


def cached(args):
    file=artifact_cache(args)
    if file is None:return False
    try:
        metadata=json.loads(file.with_suffix('.json').read_text())
        with file.open('rb') as stream:checksum=hashlib.file_digest(stream,'sha256').hexdigest()
        if checksum!=metadata['sha256'] or file.stat().st_size!=metadata['size']:return False
        shutil.copyfile(file,args.output)
        print('Reused verified '+args.target+' installer for this site and source',flush=True)
        return True
    except (OSError,ValueError,KeyError):return False


def remember(args):
    file=artifact_cache(args)
    if file is None:return
    if args.output.stat().st_size<1024:raise RuntimeError('Installer output is incomplete')
    file.parent.mkdir(parents=True,exist_ok=True)
    temporary=file.with_name(file.name+'.'+str(os.getpid())+'.tmp')
    shutil.copyfile(args.output,temporary);temporary.replace(file)
    with file.open('rb') as stream:checksum=hashlib.file_digest(stream,'sha256').hexdigest()
    metadata=file.with_suffix('.json');temporary=metadata.with_suffix('.'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps({'sha256':checksum,'size':file.stat().st_size}));temporary.replace(metadata)

def run(args,**kwargs):
    subprocess.run(args,check=True,**kwargs)

def desktop(args):
    with tempfile.TemporaryDirectory(prefix='anilux-desktop-') as temp:
        work=Path(temp)
        shutil.copytree(ROOT/'desktop',work,dirs_exist_ok=True,ignore=shutil.ignore_patterns('node_modules','dist'))
        config=json.loads((work/'package.json').read_text())
        config['version']=args.version
        config['homepage']=args.site_url
        (work/'package.json').write_text(json.dumps(config))
        (work/'app.config.json').write_text(json.dumps({'siteUrl':args.site_url}))
        env={**os.environ,'ELECTRON_SKIP_BINARY_DOWNLOAD':'1'}
        run(['npm.cmd' if os.name=='nt' else 'npm','ci','--omit=optional','--omit=peer',
             '--no-audit','--no-fund'],cwd=work,env=env)
        platform=['--linux',{'deb':'deb','appimage':'AppImage','flatpak':'dir'}[args.target]]
        run(['npx.cmd' if os.name=='nt' else 'npx','--no-install','electron-builder',*platform,'--x64','--publish','never'],cwd=work)
        if args.target=='flatpak':
            from build_flatpak import build
            build(work/'dist/linux-unpacked',ROOT/'desktop/icon.png',args.output)
            return
        suffix={'windows':'.exe','deb':'.deb','appimage':'.AppImage','flatpak':'.flatpak'}[args.target]
        installers=list((work/'dist').glob('*'+suffix))
        if len(installers)!=1:raise RuntimeError('Expected one installer, got '+str(installers))
        shutil.copyfile(installers[0],args.output)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--target',required=True);parser.add_argument('--site-url',required=True);parser.add_argument('--version',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if cached(args):raise SystemExit(0)
    if args.target=='windows':
        from build_windows import build
        build(args)
    elif args.target in ('deb','appimage','flatpak'):desktop(args)
    elif args.target=='android':
        from build_android import build
        build(args)
    elif args.target=='ios':
        import shlex
        command=shlex.split(os.environ['NATIVE_MAC_BUILD_COMMAND'])
        run([*command,'--site-url',args.site_url,'--version',args.version,'--output',str(args.output)])
    else:raise ValueError('Unknown installer target')
    remember(args)
