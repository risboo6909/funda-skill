import argparse
import socket
import time

from simple_http_server import PathValue, route, server
from simple_http_server.basic_models import Parameter

from funda import Funda

MULTI_PAGE_REQUEST_DELAY_SECONDS = 0.3


def parse_args():
    parser = argparse.ArgumentParser(description="Funda Gateway")
    parser.add_argument(
        "--port", type=int, default=9090, help="Port to run the server on"
    )
    parser.add_argument(
        "--timeout", type=int, default=10, help="Timeout for Funda API calls in seconds"
    )
    return parser.parse_args()


def fetch_public_id(url):
    """Extract the public ID from a Funda listing URL."""
    # Example URL: https://www.funda.nl/detail/koop/amsterdam/appartement-aragohof-11-1/43242669/
    # The public ID is the number after the last hyphen and before the trailing slash.
    try:
        return url.rstrip("/").split("/")[-1]
    except IndexError:
        raise ValueError(f"Invalid Funda listing URL: {url}")


def _as_list_param(value):
    if isinstance(value, list):
        items = value
    elif value is None:
        return []
    else:
        items = [value]

    result = []
    for item in items:
        if isinstance(item, str):
            result.extend(part.strip() for part in item.split(",") if part.strip())
        elif item is not None:
            result.append(str(item))
    return result


def _as_optional_int(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return int(text)


def _as_optional_str(value):
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        value = value[0]
    text = str(value).strip()
    return text or None


def is_port_listening(port, host="127.0.0.1", timeout=0.5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, int(port))) == 0


def spin_up_server(server_port, funda_timeout):
    if is_port_listening(server_port):
        raise RuntimeError(f"Gateway already running on 127.0.0.1:{server_port}")

    f = Funda(timeout=funda_timeout)

    @route("/get_listing/{path_part}", method=["GET"])
    def get_listing(path_part=PathValue()):
        return f.get_listing(path_part).to_dict()

    @route("/get_price_history/{path_part}", method=["GET"])
    def get_price_history(path_part=PathValue()):
        listing = f.get_listing(path_part)
        return {item["date"]: item for item in f.get_price_history(listing)}

    @route("/search_listings", method=["GET", "POST"])
    def search_listings(
        location=Parameter("location", default="Amsterdam"),  # City or area name
        offering_type=Parameter("offering_type", default=""),  # "buy" or "rent"
        availability=Parameter("availability", default=""),  # available/negotiations/sold
        radius_km=Parameter("radius_km", default=""),  # Search radius in kilometers
        price_min=Parameter("price_min", default=""),  # Minimum price
        price_max=Parameter("price_max", default=""),  # Maximum price
        area_min=Parameter("area_min", default=""),  # Minimum living area (m²)
        area_max=Parameter("area_max", default=""),  # Maximum living area (m²)
        plot_min=Parameter("plot_min", default=""),  # Minimum plot area (m²)
        plot_max=Parameter("plot_max", default=""),  # Maximum plot area (m²)
        object_type=Parameter("object_type", default=""),  # Property types
        energy_label=Parameter("energy_label", default=""),  # Energy labels
        sort=Parameter("sort", default="newest"),  # Sort order
        page=Parameter("page", default=""),  # Backward-compatible single page alias
        pages=Parameter("pages", default="0"),  # Page numbers (15 results per page)
    ):
        object_type = _as_list_param(object_type) or None
        energy_label = _as_list_param(energy_label) or None
        availability = _as_list_param(availability) or None
        pages = _as_list_param(pages)
        if not pages:
            single_page = _as_optional_int(page)
            pages = [str(single_page)] if single_page is not None else ["0"]
        pages = list(map(int, pages))
        offering_type = _as_optional_str(offering_type) or "buy"
        sort = _as_optional_str(sort)

        response = {}

        for index, page in enumerate(pages):
            search_kwargs = {
                "location": location,
                "offering_type": offering_type,
                "availability": availability,
                "radius_km": _as_optional_int(radius_km),
                "price_min": _as_optional_int(price_min),
                "price_max": _as_optional_int(price_max),
                "area_min": _as_optional_int(area_min),
                "area_max": _as_optional_int(area_max),
                "plot_min": _as_optional_int(plot_min),
                "plot_max": _as_optional_int(plot_max),
                "object_type": object_type,
                "energy_label": energy_label,
                "sort": sort,
                "page": page,
            }
            print(f"[funda_gateway] search_listing kwargs: {search_kwargs}")
            results = f.search_listing(**search_kwargs)
            response.update(
                {
                    fetch_public_id(item["detail_url"]): item.to_dict()
                    for item in results
                }
            )
            if index < len(pages) - 1:
                time.sleep(MULTI_PAGE_REQUEST_DELAY_SECONDS)

        return response

    server.start(host="127.0.0.1", port=server_port)


if __name__ == "__main__":
    args = parse_args()
    spin_up_server(args.port, args.timeout)
