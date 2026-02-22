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

    def test_fetch_public_id_handles_url_without_trailing_slash(self):
        url = "https://www.funda.nl/detail/koop/utrecht/huis-test/12345678"
        self.assertEqual(self.module.fetch_public_id(url), "12345678")

    def test_as_list_param_splits_csv_string(self):
        self.assertEqual(self.module._as_list_param("A,B,C"), ["A", "B", "C"])

    def test_as_list_param_keeps_list_and_splits_nested_csv_items(self):
        self.assertEqual(
            self.module._as_list_param(["house", "apartment,villa", ""]),
            ["house", "apartment", "villa"],
        )

    def test_as_list_param_handles_none_and_non_string_items(self):
        self.assertEqual(self.module._as_list_param(None), [])
        self.assertEqual(self.module._as_list_param([1, None, "A"]), ["1", "A"])

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

    def test_spin_up_server_search_listings_returns_public_id_keyed_dict(self):
        routes = {}

        def fake_route(path, method=None):
            def decorator(fn):
                routes[path] = fn
                return fn

            return decorator

        started = {}

        class FakeListing(dict):
            def to_dict(self):
                return {"address": "Amsterdam"}

        class FakeFunda:
            def __init__(self, timeout):
                self.timeout = timeout
                self.search_kwargs = None

            def get_listing(self, path_part):
                raise AssertionError("not used in this test")

            def get_price_history(self, listing):
                raise AssertionError("not used in this test")

            def search_listing(self, **kwargs):
                self.search_kwargs = kwargs
                return [
                    FakeListing(
                        detail_url="https://www.funda.nl/detail/koop/amsterdam/huis/43242669/"
                    )
                ]

        funda_instance = {}

        def fake_funda_factory(timeout):
            instance = FakeFunda(timeout)
            funda_instance["value"] = instance
            return instance

        with mock.patch.object(self.module, "route", fake_route), mock.patch.object(
            self.module,
            "server",
            types.SimpleNamespace(
                start=lambda host, port: started.update({"host": host, "port": port})
            ),
        ), mock.patch.object(self.module, "Funda", fake_funda_factory):
            self.module.spin_up_server(server_port=9001, funda_timeout=7)

        response = routes["/search_listings"](
            location="Amsterdam",
            offering_type="buy",
            radius_km="10",
            price_min="100000",
            price_max="800000",
            area_min="50",
            area_max="150",
            plot_min="0",
            plot_max="200",
            object_type=["house"],
            energy_label=["A"],
            sort="newest",
            page="2",
        )

        self.assertEqual(started["port"], 9001)
        self.assertEqual(started["host"], "127.0.0.1")
        self.assertEqual(response, {"43242669": {"address": "Amsterdam"}})
        self.assertEqual(funda_instance["value"].timeout, 7)
        self.assertEqual(funda_instance["value"].search_kwargs["radius_km"], 10)
        self.assertEqual(funda_instance["value"].search_kwargs["page"], 2)
        self.assertEqual(funda_instance["value"].search_kwargs["price_min"], 100000)

    def test_spin_up_server_price_history_is_keyed_by_date(self):
        routes = {}

        def fake_route(path, method=None):
            def decorator(fn):
                routes[path] = fn
                return fn

            return decorator

        class FakeListing:
            pass

        class FakeFunda:
            def __init__(self, timeout):
                self.timeout = timeout

            def get_listing(self, path_part):
                self.path_part = path_part
                return FakeListing()

            def get_price_history(self, listing):
                self.history_listing = listing
                return [
                    {"date": "2024-01-01", "price": 500000},
                    {"date": "2024-02-01", "price": 495000},
                ]

            def search_listing(self, **kwargs):
                raise AssertionError("not used in this test")

        funda_instance = {}

        def fake_funda_factory(timeout):
            instance = FakeFunda(timeout)
            funda_instance["value"] = instance
            return instance

        with mock.patch.object(self.module, "route", fake_route), mock.patch.object(
            self.module, "server", types.SimpleNamespace(start=lambda host, port: None)
        ), mock.patch.object(self.module, "Funda", fake_funda_factory):
            self.module.spin_up_server(server_port=9001, funda_timeout=7)

        response = routes["/get_price_history/{path_part}"](path_part="43242669")

        self.assertEqual(funda_instance["value"].path_part, "43242669")
        self.assertEqual(
            response,
            {
                "2024-01-01": {"date": "2024-01-01", "price": 500000},
                "2024-02-01": {"date": "2024-02-01", "price": 495000},
            },
        )

if __name__ == "__main__":
    unittest.main()
