from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from server.src.main import app
from server.src.middlewares.rate_limit import client_address

client = TestClient(app)


def _request(forwarded=None, peer="10.0.0.9") -> Request:
    headers = []
    if forwarded is not None:
        headers.append((b"x-forwarded-for", forwarded.encode("ascii")))
    return Request({
        "type": "http", "headers": headers, "client": (peer, 443),
    })


def test_without_a_proxy_the_address_is_the_peer():
    assert client_address(_request("1.2.3.4"), trusted_hops=0) == "10.0.0.9"


def test_behind_one_proxy_the_address_is_the_one_it_appended():
    request = _request("203.0.113.7, 198.51.100.20")

    assert client_address(request, trusted_hops=1) == "198.51.100.20"


def test_a_forged_header_does_not_move_the_address():
    request = _request("1.1.1.1, 2.2.2.2, 198.51.100.20")

    assert client_address(request, trusted_hops=1) == "198.51.100.20"


def test_two_proxies_skip_the_last_hop():
    request = _request("198.51.100.20, 172.16.0.3")

    assert client_address(request, trusted_hops=2) == "198.51.100.20"


@pytest.mark.parametrize("forwarded", [None, "", "198.51.100.20"])
def test_fewer_hops_than_expected_falls_back_to_the_peer(forwarded):
    assert client_address(_request(forwarded), trusted_hops=2) == "10.0.0.9"


def test_something_that_is_not_an_address_falls_back_to_the_peer():
    request = _request("x" * 200)

    assert client_address(request, trusted_hops=1) == "10.0.0.9"


def test_ipv6_addresses_are_kept():
    request = _request("2001:db8::1")

    assert client_address(request, trusted_hops=1) == "2001:db8::1"


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_counts_the_address_behind_the_proxy(
    mock_get_employee, rate_limit_window
):
    mock_get_employee.return_value = None

    with patch("server.src.middlewares.rate_limit.TRUSTED_PROXY_HOPS", 1):
        client.post(
            "/auth/login",
            json={"email": "ana@cen.com", "password": "clave123"},
            headers={"X-Forwarded-For": "1.1.1.1, 198.51.100.20"},
        )

    assert rate_limit_window.call_args[0][1] == "198.51.100.20"
