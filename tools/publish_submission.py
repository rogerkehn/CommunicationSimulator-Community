"""Trusted repository workflow: validate public issue data, never execute it."""
import base64
import gzip
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET

MAX_XML = 1024 * 1024
PREFIX = 'SIMULATOR-SHARE/1\n'


def validate(body):
    if not isinstance(body, str) or not body.startswith(PREFIX) or len(body) > 60000:
        raise ValueError('Use the application upload window; submission format/size is invalid.')
    data = json.loads(body[len(PREFIX):])
    if set(data) != {'name', 'comment', 'content', 'sha256'}:
        raise ValueError('Unexpected submission fields.')
    if not isinstance(data['name'], str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', data['name']):
        raise ValueError('Name must be 1-64 lowercase letters, numbers or hyphens.')
    if not isinstance(data['comment'], str) or not 1 <= len(data['comment'].strip()) <= 2000:
        raise ValueError('A posting comment of 1-2000 characters is required.')
    if not isinstance(data['content'], str) or len(data['content']) > 56000:
        raise ValueError('Compressed file is too large.')
    compressed = base64.b64decode(data['content'], validate=True)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        xml = stream.read(MAX_XML + 1)
    if not xml or len(xml) > MAX_XML:
        raise ValueError('File exceeds the 1 MiB sharing limit.')
    # XML encodings other than UTF-8 are not accepted in the wire format.
    text = xml.decode('utf-8', errors='strict')
    if re.search(r'<!\s*(DOCTYPE|ENTITY)', text, re.I):
        raise ValueError('XML entities and document types are forbidden.')
    root = ET.fromstring(text)
    if root.tag != 'CommunicationSimulatorSettings':
        raise ValueError('This is not a simulator configuration.')
    if any(element.tag.split('}')[-1].startswith('AI_') or element.tag.split('}')[-1] == 'AiConversation' for element in root.iter()):
        raise ValueError('Remove AI conversations and AI preferences before sharing.')
    digest = hashlib.sha256(xml).hexdigest()
    if data['sha256'] != digest:
        raise ValueError('File checksum does not match.')
    return data, xml, digest


def api(method, path, data=None):
    request = urllib.request.Request('https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + path,
        data=json.dumps(data).encode() if data is not None else None, method=method,
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'CommunicationSimulatorCommunity', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    event = json.loads(pathlib.Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    if 'issue' in event:
        number = event['issue']['number']
    else:
        number = int(event['inputs']['issue'])
    issue = api('GET', '/issues/' + str(number))
    if not issue.get('body', '').startswith(PREFIX):
        return
    try:
        data, xml, digest = validate(issue['body'])
    except (ValueError, TypeError, KeyError, OSError, ET.ParseError):
        api('POST', '/issues/' + str(number) + '/comments', {'body': 'Upload rejected: invalid submission, missing comment, unsafe XML, checksum mismatch or sharing limit exceeded. Please submit again from the application. No file was published.'})
        return
    author = issue['user']['login'].lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,38}', author):
        raise ValueError('Invalid GitHub author.')
    relative = f'simulators/{author}/{data["name"]}/{number}.simulator'
    target = pathlib.Path(relative)
    catalog_path = pathlib.Path('catalog.json')
    subprocess.run(['git', 'config', 'user.name', 'Community Publisher'], check=True)
    subprocess.run(['git', 'config', 'user.email', 'community-publisher@users.noreply.github.com'], check=True)
    # A normal push is compare-and-swap. Rebuild against the newest main on conflict;
    # no force push and no Actions concurrency group that could discard pending uploads.
    for attempt in range(8):
        subprocess.run(['git', 'fetch', 'origin', 'main'], check=True)
        # Only used inside the ephemeral, trusted workflow checkout.
        subprocess.run(['git', 'reset', '--hard', 'origin/main'], check=True)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError('Published revisions are immutable. Submit a new version.')
            break
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
        if catalog.get('schema') != 1 or len(catalog['versions']) >= 20000:
            raise ValueError('Catalog requires maintainer attention.')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(xml)
        catalog['versions'].append({'author': author, 'name': data['name'], 'version': number,
            'comment': data['comment'].strip(), 'created': issue['created_at'],
            'path': relative, 'sha256': digest, 'bytes': len(xml), 'issue': issue['html_url']})
        catalog['versions'].sort(key=lambda version: version['version'])
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        subprocess.run(['git', 'add', '--', relative, 'catalog.json'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Share {author}/{data["name"]} revision {number}', '-m', data['comment']], check=True)
        if subprocess.run(['git', 'push', 'origin', 'HEAD:main']).returncode == 0:
            break
        time.sleep(min(attempt + 1, 5))
    else:
        raise RuntimeError('Concurrent publication busy; retry this issue using Run workflow.')
    api('POST', '/issues/' + str(number) + '/comments', {'body': f'Published **{author}/{data["name"]}**, revision **{number}**. Refresh Community Simulators in the application to download it. SHA-256: `{digest}`.'})
    api('PATCH', '/issues/' + str(number), {'state': 'closed', 'state_reason': 'completed'})


if __name__ == '__main__':
    main()
