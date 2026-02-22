# Local shim to replace tls_client with curl_cffi.requests
from curl_cffi import requests as crequests


class Session:
    def __init__(self, *args, **kwargs):
        # common tls_client kw: client_identifier, random_tls_extension_order, etc.
        self._impersonate = kwargs.get("client_identifier", "chrome")
        self._session = crequests.Session(impersonate=self._impersonate)

    def get(self, url, **kwargs):
        return self._session.get(url, **kwargs)

    def post(self, url, **kwargs):
        return self._session.post(url, **kwargs)

    def put(self, url, **kwargs):
        return self._session.put(url, **kwargs)

    def delete(self, url, **kwargs):
        return self._session.delete(url, **kwargs)
