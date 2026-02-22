import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestFundaGateway(unittest.TestCase):
    def setUp(self):
        simple_http_server = types.ModuleType("simple_http_server")
        simple_http_server.PathValue = object
        simple_http_server.route = lambda *args, **kwargs: (lambda fn: fn)
        simple_http_server.server = types.SimpleNamespace(start=lambda **kwargs: None)

        basic_models = types.ModuleType("simple_http_server.basic_models")
        basic_models.Parameter = lambda *args, **kwargs: None

        funda_mod = types.ModuleType("funda")

        class DummyFunda:
            def __init__(self, *args, **kwargs):
                pass

        funda_mod.Funda = DummyFunda

        patcher = mock.patch.dict(
            sys.modules,
            {
                "simple_http_server": simple_http_server,
                "simple_http_server.basic_models": basic_models,
                "funda": funda_mod,
            },
        )
        self.addCleanup(patcher.stop)
        patcher.start()

        self.module = load_module(
            "funda_gateway_under_test", ROOT / "scripts" / "funda_gateway.py"
        )

    def test_fetch_public_id_extracts_last_path_segment(self):
        url = "https://www.funda.nl/detail/koop/amsterdam/appartement-aragohof-11-1/43242669/"
        self.assertEqual(self.module.fetch_public_id(url), "43242669")

    def test_parse_args_uses_defaults(self):
        with mock.patch.object(sys, "argv", ["funda_gateway.py"]):
            args = self.module.parse_args()

        self.assertEqual(args.port, 9090)
        self.assertEqual(args.timeout, 10)

    def test_parse_args_accepts_custom_values(self):
        with mock.patch.object(
            sys, "argv", ["funda_gateway.py", "--port", "8080", "--timeout", "5"]
        ):
            args = self.module.parse_args()

        self.assertEqual(args.port, 8080)
        self.assertEqual(args.timeout, 5)


class TestTlsClientShim(unittest.TestCase):
    def setUp(self):
        self.calls = []

        class FakeInnerSession:
            def __init__(inner_self, impersonate=None):
                self.calls.append(("init", impersonate))
                inner_self.impersonate = impersonate

            def get(inner_self, url, **kwargs):
                self.calls.append(("get", url, kwargs))
                return "GET_OK"

            def post(inner_self, url, **kwargs):
                self.calls.append(("post", url, kwargs))
                return "POST_OK"

            def put(inner_self, url, **kwargs):
                self.calls.append(("put", url, kwargs))
                return "PUT_OK"

            def delete(inner_self, url, **kwargs):
                self.calls.append(("delete", url, kwargs))
                return "DELETE_OK"

        requests_mod = types.SimpleNamespace(Session=FakeInnerSession)
        curl_cffi = types.ModuleType("curl_cffi")
        curl_cffi.requests = requests_mod

        patcher = mock.patch.dict(sys.modules, {"curl_cffi": curl_cffi})
        self.addCleanup(patcher.stop)
        patcher.start()

        self.module = load_module("tls_client_under_test", ROOT / "scripts" / "tls_client.py")

    def test_session_uses_client_identifier_for_impersonation(self):
        self.module.Session(client_identifier="chrome136")
        self.assertIn(("init", "chrome136"), self.calls)

    def test_http_methods_delegate_to_wrapped_session(self):
        session = self.module.Session()

        self.assertEqual(session.get("https://example.com", timeout=1), "GET_OK")
        self.assertEqual(session.post("https://example.com", json={"a": 1}), "POST_OK")
        self.assertEqual(session.put("https://example.com"), "PUT_OK")
        self.assertEqual(session.delete("https://example.com"), "DELETE_OK")

        self.assertIn(("init", "chrome"), self.calls)
        self.assertIn(("get", "https://example.com", {"timeout": 1}), self.calls)
        self.assertIn(("post", "https://example.com", {"json": {"a": 1}}), self.calls)


if __name__ == "__main__":
    unittest.main()
