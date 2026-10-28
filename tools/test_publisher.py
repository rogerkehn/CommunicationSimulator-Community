"""Offline checks for untrusted submission validation; no GitHub access/secrets."""
import base64
import gzip
import hashlib
import json
import unittest
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


if __name__ == '__main__':
    unittest.main()
