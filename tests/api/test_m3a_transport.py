import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from verdictkit.api.server import create_app, VERSION
from verdictkit.plugin import Registry


def test_local_health_is_honest():
    with patch.dict(os.environ, {'VK_ISOLATION':'', 'VK_EXAMINER_SOCKET':''}):
        with TestClient(create_app(Registry(), judge_mode=False)) as c:
            r=c.get('/api/v1/health')
            assert r.status_code == 200
            assert r.headers['X-VerdictKit-Contract'] == VERSION
            assert r.json()['isolationMode'] == 'UNENFORCED'
            assert r.json()['judgeMode'] is False


def test_judge_refuses_environment_spoof():
    with patch.dict(os.environ, {'VK_ISOLATION':'enforced', 'VK_EXAMINER_SOCKET':''}):
        with pytest.raises(RuntimeError):
            create_app(Registry(), judge_mode=True)


def test_workflow_rejects_without_fabricating_case():
    with TestClient(create_app(Registry(), judge_mode=False)) as c:
        r=c.post('/api/v1/cases',json={'claimType':'quote.finance.v1','dataMode':'LIVE_EVIDENCE','form':{'params':{},'outcomes':{}}})
        assert r.status_code == 503
        assert r.json()['error']['code'] == 'HTTP_WORKFLOW_NOT_YET_IMPLEMENTED'
        assert 'caseId' not in str(r.json())


def test_body_limit():
    with TestClient(create_app(Registry(), judge_mode=False)) as c:
        r=c.post('/api/v1/cases',content=b'x'*(256*1024+1),headers={'content-type':'application/json'})
        assert r.status_code == 413


def test_registered_types_shape():
    with TestClient(create_app(Registry(), judge_mode=False)) as c:
        r=c.get('/api/v1/claim-types')
        assert r.status_code==200 and r.json()==[]
