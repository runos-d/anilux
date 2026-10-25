import shutil
import subprocess
from pathlib import Path
import tempfile


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def build(unpacked, icon, output):
    branch = '26.08'
    base = 'org.electronjs.Electron2.BaseApp//'+branch
    run(['flatpak','remote-add','--user','--if-not-exists','flathub','https://dl.flathub.org/repo/flathub.flatpakrepo'])
    ref = 'app/'+base.replace('//','/x86_64/')
    commit = subprocess.check_output(['flatpak','remote-info','--user','--show-commit','flathub',base], text=True).strip()
    import os, re
    if not re.fullmatch(r'[a-f0-9]{64}',commit):raise RuntimeError('Invalid BaseApp commit')
    repo = Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'flatpak/repo'
    # Pull the named ref so OSTree can use Flathub's static deltas. Pulling the
    # resolved commit directly falls back to object URLs that Flathub rejects.
    run(['ostree','--repo='+str(repo),'pull','flathub',ref])
    with tempfile.TemporaryDirectory(prefix='anilux-flatpak-') as temporary:
        work=Path(temporary); app=work/'application'; files=app/'files'
        run(['ostree','--repo='+str(repo),'checkout','--user-mode','--force-copy',commit,str(work/'base')])
        shutil.copytree(work/'base/files', files, symlinks=True)
        zypak=files/'bin/zypak-wrapper'
        if zypak.is_symlink() and os.readlink(zypak)=='/app/bin/zypak-wrapper.sh':
            zypak.unlink();zypak.symlink_to('zypak-wrapper.sh')
        if not zypak.is_file():raise RuntimeError('BaseApp is missing Zypak')
        program=files/'lib/org.anilux.app'
        shutil.copytree(unpacked, program, symlinks=True)
        executable=next((name for name in ('anilux','anilux-app','AniLux') if (program/name).is_file()), None)
        if not executable: raise RuntimeError('Electron executable missing')
        sandbox=program/'chrome-sandbox'
        if sandbox.exists(): sandbox.chmod(0o755)
        wrapper=files/'bin/anilux'; wrapper.parent.mkdir(exist_ok=True)
        wrapper.write_text('#!/bin/sh\nexport TMPDIR="$XDG_RUNTIME_DIR/app/$FLATPAK_ID"\nexec /app/bin/zypak-wrapper /app/lib/org.anilux.app/'+executable+' "$@"\n')
        wrapper.chmod(0o755)
        desktop=files/'share/applications/org.anilux.app.desktop'
        desktop.parent.mkdir(parents=True, exist_ok=True)
        desktop.write_text('[Desktop Entry]\nType=Application\nName=AniLux\nExec=anilux %U\nIcon=org.anilux.app\nTerminal=false\nCategories=AudioVideo;Network;\n')
        icons=files/'share/icons/hicolor/512x512/apps'; icons.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(icon, icons/'org.anilux.app.png')
        (app/'metadata').write_text('[Application]\nname=org.anilux.app\nruntime=org.freedesktop.Platform/x86_64/'+branch+'\ncommand=anilux\n[Context]\nshared=network;ipc;\nsockets=x11;wayland;pulseaudio;\ndevices=dri;\n[Session Bus Policy]\norg.freedesktop.Notifications=talk\n')
        (app/'var').mkdir()
        run(['flatpak','build-finish',str(app)])
        from PIL import Image
        with Image.open(icon) as image:image.verify()
        run(['flatpak','build-export','--disable-sandbox','--arch=x86_64',str(work/'repo'),str(app),'stable'])
        run(['flatpak','build-bundle','--runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo',str(work/'repo'),str(output),'org.anilux.app','stable'])
