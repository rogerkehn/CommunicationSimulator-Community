"""Offline checks for untrusted submission validation; no GitHub access/secrets."""
import base64
import gzip
import hashlib
import json
import unittest
import os
import pathlib
import subprocess
import tempfile
from unittest.mock import patch
import publish_submission
from publish_submission import validate, PREFIX, MAX_XML


def submission(xml=b'<CommunicationSimulatorSettings><Notes>fixture</Notes></CommunicationSimulatorSettings>', **updates):
    data = dict(name='bench-device', comment='First version: temperature \u03a9',
                content=base64.b64encode(gzip.compress(xml)).decode(), sha256=hashlib.sha256(xml).hexdigest())
    data.update(updates)
    return PREFIX + json.dumps(data)


class ValidatorTests(unittest.TestCase):
    def test_roundtrip(self):
        data, xml, digest = validate(submission())
        self.assertEqual(data['name'], 'bench-device')
        self.assertEqual(hashlib.sha256(xml).hexdigest(), digest)

    def test_rejections(self):
        bad = [submission(name='../x'), submission(name='A'), submission(name='-'), submission(name='x' * 65),
               submission(comment=' '), submission(comment='x' * 2001), submission(comment=42), submission(content='!!!'),
               submission(sha256='wrong'), submission(extra='field'), '{}', PREFIX + '{}', submission(content='x' * 56001),
               submission(b'<other/>'), submission(b'<CommunicationSimulatorSettings>'),
               submission(b'<!DOCTYPE x [<!ENTITY x "private">]><CommunicationSimulatorSettings>&x;</CommunicationSimulatorSettings>'),
               submission(b'<CommunicationSimulatorSettings><AI_AllowMcp>true</AI_AllowMcp></CommunicationSimulatorSettings>'),
               submission(b'<CommunicationSimulatorSettings><AiConversation>private chat</AiConversation></CommunicationSimulatorSettings>'),
               submission(b'<CommunicationSimulatorSettings>' + b'x' * MAX_XML + b'</CommunicationSimulatorSettings>')]
        for body in bad:
            with self.subTest(body=body[:80]):
                with self.assertRaises(Exception):
                    validate(body)

    def test_real_git_publication_and_retry(self):
        # Only fixture XML is published into an isolated local bare Git repository.
        with tempfile.TemporaryDirectory(prefix='community-publisher-') as temporary:
            base = pathlib.Path(temporary)
            remote = base / 'remote.git'
            checkout = base / 'checkout'
            def git(*args, cwd=None):
                return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)
            git('init', '--bare', '--initial-branch=main', str(remote))
            git('clone', str(remote), str(checkout))
            git('config', 'user.name', 'Fixture', cwd=checkout)
            git('config', 'user.email', 'fixture@example.invalid', cwd=checkout)
            (checkout / 'catalog.json').write_text('{"schema":1,"versions":[]}')
            git('add', 'catalog.json', cwd=checkout)
            git('commit', '-m', 'Fixture catalog', cwd=checkout)
            git('push', 'origin', 'main', cwd=checkout)
            event_path = base / 'event.json'
            event_path.write_text(json.dumps({'issue': {'number': 12}}))
            issue = {'body': submission(), 'number': 12, 'user': {'login': 'Fixture-User'},
                     'created_at': '2026-10-28T12:00:00Z', 'html_url': 'https://github.com/fixture/repo/issues/12'}
            calls = []
            def api(method, path, data=None):
                calls.append((method, path, data))
                return issue if method == 'GET' else {}
            previous = pathlib.Path.cwd()
            try:
                os.chdir(checkout)
                with patch.dict(os.environ, {'GITHUB_EVENT_PATH': str(event_path)}), patch.object(publish_submission, 'api', api):
                    publish_submission.main()
                    catalog = json.loads((checkout / 'catalog.json').read_text(encoding='utf-8'))
                    self.assertEqual(len(catalog['versions']), 1)
                    entry = catalog['versions'][0]
                    self.assertEqual(entry['author'], 'fixture-user')
                    self.assertTrue((checkout / entry['path']).exists())
                    self.assertEqual(entry['comment'], 'First version: temperature \u03a9')
                    commit = git('rev-parse', 'HEAD', cwd=checkout).stdout
                    publish_submission.main()
                    self.assertEqual(git('rev-parse', 'HEAD', cwd=checkout).stdout, commit)
                    self.assertEqual(len(json.loads((checkout / 'catalog.json').read_text(encoding='utf-8'))['versions']), 1)
                    self.assertTrue(any(call[0] == 'PATCH' and call[2]['state'] == 'closed' for call in calls))
                    issue['body'] = submission(b'<CommunicationSimulatorSettings><Notes>changed</Notes></CommunicationSimulatorSettings>')
                    with self.assertRaises(ValueError):
                        publish_submission.main()
                    # Another version, published with a lower issue number, stays available.
                    event_path.write_text(json.dumps({'issue': {'number': 3}}))
                    issue['number'] = 3
                    issue['html_url'] = 'https://github.com/fixture/repo/issues/3'
                    publish_submission.main()
                    self.assertEqual([v['version'] for v in json.loads((checkout / 'catalog.json').read_text(encoding='utf-8'))['versions']], [3, 12])
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
