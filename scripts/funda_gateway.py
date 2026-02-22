import argparse

from simple_http_server import PathValue, route, server
from simple_http_server.basic_models import Parameter

from funda import Funda


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


def spin_up_server(server_port, funda_timeout):
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
        offering_type=Parameter("offering_type", default="buy"),  # "buy" or "rent"
        radius_km=Parameter("radius_km", default="5"),  # Search radius in kilometers
        price_min=Parameter("price_min", default="0"),  # Minimum price
        price_max=Parameter("price_max", default="500000"),  # Maximum price
        area_min=Parameter("area_min", default="40"),  # Minimum living area (m²)
        area_max=Parameter("area_max", default="100"),  # Maximum living area (m²)
        plot_min=Parameter("plot_min", default="100"),  # Minimum plot area (m²)
        plot_max=Parameter("plot_max", default="150"),  # Maximum plot area (m²)
        object_type=["house"],  # Property types (default: house, apartment)
        energy_label=["A", "A+"],  # energy_label=['A', 'A+']
        sort="newest",  # Sort order
        page=0,  # Page number (15 results per page)
    ):
        results = f.search_listing(
            location=location,
            offering_type=offering_type,
            radius_km=int(radius_km),
            price_min=int(price_min),
            price_max=int(price_max),
            area_min=int(area_min),
            area_max=int(area_max),
            plot_min=int(plot_min),
            plot_max=int(plot_max),
            object_type=object_type,
            energy_label=energy_label,
            sort=sort,
            page=int(page),
        )
        response = {
            fetch_public_id(item["detail_url"]): item.to_dict() for item in results
        }
        return response

    server.start(port=server_port)


if __name__ == "__main__":
    args = parse_args()
    spin_up_server(args.port, args.timeout)
