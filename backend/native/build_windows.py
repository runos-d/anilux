import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
SDK_VERSION = '1.0.4258.31'
SDK_SHA256 = '56f7f4b8bf9aee4b8efefbbdd4f67d5f74ebd1b100ed0806da71bf76af481aa9'


def download(url, path, sha256=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix('.download')
        with urllib.request.urlopen(url, timeout=120) as source, temporary.open('wb') as output:
            shutil.copyfileobj(source, output)
        temporary.replace(path)
    if sha256 and hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
        raise RuntimeError('Dependency checksum mismatch: '+path.name)


def compile_host(site_url, destination, source_path=None):
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    cache = Path(os.environ.get('DATA_DIR', ROOT.parent / 'data')) / 'native_cache/windows'
    sdk = cache / ('webview2-'+SDK_VERSION+'.nupkg')
    download('https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/'+SDK_VERSION+'/microsoft.web.webview2.'+SDK_VERSION+'.nupkg', sdk, SDK_SHA256)
    libraries = ['Microsoft.Web.WebView2.Core.dll', 'Microsoft.Web.WebView2.WinForms.dll']
    with zipfile.ZipFile(sdk) as archive:
        for name in libraries:
            (destination / name).write_bytes(archive.read('lib/net462/'+name))
        (destination / 'WebView2Loader.dll').write_bytes(archive.read('runtimes/win-x64/native/WebView2Loader.dll'))
        for name in archive.namelist():
            if '/' not in name and ('LICENSE' in name.upper() or 'NOTICE' in name.upper()):
                (destination / name).write_bytes(archive.read(name))
    for name in ('bridge.js', 'pip-enter.js', 'pip-exit.js'):
        shutil.copyfile(ROOT / 'windows' / name, destination / name)
    (destination / 'app.config.json').write_text(json.dumps({'siteUrl': site_url}))
    from PIL import Image
    with Image.open(ROOT / 'desktop/icon.png') as icon:
        icon.save(destination / 'icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(256,256)])
    references = ['System.Windows.Forms.dll', 'System.Drawing.dll', 'System.Web.Extensions.dll',
                  *[str(destination / name) for name in libraries]]
    source = str(source_path or ROOT / 'windows/Program.cs')
    output = str(destination / 'anilux.exe')
    if os.name == 'nt':
        compiler = str(Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe')
        command = [compiler, '/nologo', '/target:winexe', '/platform:x64', '/out:'+output,
                   '/win32icon:'+str(destination / 'icon.ico'), *['/reference:'+ref for ref in references], source]
    else:
        command = ['mcs', '-target:winexe', '-platform:x64', '-out:'+output,
                   '-win32icon:'+str(destination / 'icon.ico'), *['-r:'+ref for ref in references], source]
    subprocess.run(command, check=True)


def build(args):
    with tempfile.TemporaryDirectory(prefix='anilux-windows-') as temporary:
        work = Path(temporary)
        compile_host(args.site_url, work)
        bootstrap = Path(os.environ.get('DATA_DIR', ROOT.parent / 'data')) / 'native_cache/windows/WebView2Setup.exe'
        download('https://go.microsoft.com/fwlink/p/?LinkId=2124703', bootstrap)
        shutil.copyfile(bootstrap, work / 'WebView2Setup.exe')
        script = (ROOT / 'windows/installer.nsi').read_text(encoding='utf-8')
        script = script.replace('@DIRECTORY@', work.as_posix()).replace('@OUTPUT@', args.output.resolve().as_posix()).replace('@VERSION@', args.version)
        (work / 'installer.nsi').write_text(script, encoding='utf-8')
        subprocess.run(['makensis', str(work / 'installer.nsi')], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--site-url', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    compile_host(args.site_url, args.directory)
