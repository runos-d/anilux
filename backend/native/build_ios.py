import argparse
import json
import os
import sys
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit


def build(args):
    if sys.platform != 'darwin':
        raise RuntimeError('Signed IPA requires a macOS build runner')
    url = urlsplit(args.site_url)
    if url.scheme != 'https' or not url.hostname:
        raise ValueError('iOS release requires an HTTPS site origin')
    team = os.environ['IOS_TEAM_ID']
    with tempfile.TemporaryDirectory(prefix='anilux-ios-') as temporary:
        work = Path(temporary)
        shutil.copytree(Path(__file__).parent / 'ios', work, dirs_exist_ok=True)
        (work / 'Site.json').write_text(json.dumps({'siteUrl': args.site_url}))
        icons = work / 'Assets.xcassets' / 'AppIcon.appiconset'
        icons.mkdir(parents=True)
        subprocess.run(['sips', '-z', '1024', '1024', str(Path(__file__).parent / 'desktop' / 'icon.png'), '--out', str(icons / 'icon.png')], check=True)
        (icons / 'Contents.json').write_text(json.dumps({'images': [{'idiom':'universal','platform':'ios','size':'1024x1024','filename':'icon.png'}], 'info':{'author':'xcode','version':1}}))
        archive = work / 'AniLux.xcarchive'
        subprocess.run(['xcodegen', 'generate'], cwd=work, check=True)
        subprocess.run(['xcodebuild', '-project', 'AniLux.xcodeproj', '-scheme', 'AniLux',
            '-configuration', 'Release', '-destination', 'generic/platform=iOS',
            '-archivePath', str(archive), 'archive', f'DEVELOPMENT_TEAM={team}',
            f'MARKETING_VERSION={args.version}', f'CURRENT_PROJECT_VERSION={os.environ.get("IOS_BUILD_NUMBER", "1")}'], cwd=work, check=True)
        options = {'method': os.environ.get('IOS_EXPORT_METHOD', 'release-testing'), 'teamID': team,
                   'signingStyle': 'automatic'}
        with (work / 'ExportOptions.plist').open('wb') as output: plistlib.dump(options, output)
        subprocess.run(['xcodebuild', '-exportArchive', '-archivePath', str(archive),
            '-exportOptionsPlist', str(work / 'ExportOptions.plist'), '-exportPath', str(work / 'export')], check=True)
        artifacts = list((work / 'export').glob('*.ipa'))
        if len(artifacts) != 1: raise RuntimeError('Expected one signed IPA')
        shutil.copyfile(artifacts[0], args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--site-url', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args())
