#!/usr/bin/env python
"""
This module is meant to return the list of available radios at a time.
It is intended to be run daily to get a fresh list of radios.
"""

import urllib.request
import certifi
import socket
import random
import urllib
import json
import ssl
import logging

logging.basicConfig(
    # INFO, DEBUG, ERROR
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_radiobrowser_base_urls():
    """
    Get all base URLs of all currently available Radio Browser servers.

    Returns:
        list: A list of strings representing the base URLs.
    """
    hosts = []
    # Get all hosts from DNS
    try:
        ips = socket.getaddrinfo('all.api.radio-browser.info', 80, 0, 0, socket.IPPROTO_TCP)
        for ip_tuple in ips:
            ip = ip_tuple[4][0]

            # Do a reverse lookup on every IP to have a nice name for it
            host_addr = socket.gethostbyaddr(ip)
            # Add the name to the list if not already in there
            if host_addr[0] not in hosts:
                hosts.append(host_addr[0])

        # Sort list of names
        hosts.sort()
        # Add "https://" in front to make it a URL
        base_urls = list(map(lambda x: "https://" + x, hosts))
        logging.debug(f"Base URLs retrieved: {base_urls}")
        return base_urls

    except Exception as e:
        logging.error(f"Error getting Radio Browser base URLs: {e}")
        return []

def downloadUri(uri, param):
    """
    Download data from a given URI with optional parameters.

    Args:
        uri (str): The URI to download data from.
        param (dict or None): Optional parameters for the request.

    Returns:
        bytes: The data retrieved from the URI.
    """
    param_encoded = None
    if param is not None:
        param_encoded = json.dumps(param).encode('utf-8')
        logging.info(f"Request to {uri} with Params: {param}")
    else:
        logging.info(f"Request to {uri} with no parameters")

    req = urllib.request.Request(uri, data=param_encoded)

    # Change the user agent to name your app and version
    req.add_header('User-Agent', 'MyApp/0.0.1')
    req.add_header('Content-Type', 'application/json')

    context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urllib.request.urlopen(req, context=context) as response:
            data = response.read()
            logging.debug(f"Data received from {uri}")
            return data
    except Exception as e:
        logging.error(f"Error downloading data from {uri}: {e}")
        raise

def downloadRadiobrowser(path, param):
    """
    Download file with relative URL from a random API server.
    Retry with other API servers if failed.

    Args:
        path (str): The relative path to download.
        param (dict or None): Optional parameters for the request.

    Returns:
        bytes or None: The data retrieved, or None if all servers fail.
    """
    servers = get_radiobrowser_base_urls()
    random.shuffle(servers)
    for i, server_base in enumerate(servers):
        logging.info(f"Attempt {i+1}: Trying server {server_base}")
        uri = server_base + path

        try:
            data = downloadUri(uri, param)
            return data
        except Exception as e:
            logging.warning(f"Unable to download from API URL: {uri}. Error: {e}")
            continue
    logging.error("Failed to retrieve data from all servers.")
    return None  # To indicate failure

def downloadRadiobrowserStats():
    """
    Download statistics from the Radio Browser API.

    Returns:
        dict or None: The statistics data as a dictionary, or None if failed.
    """
    stats = downloadRadiobrowser("/json/stats", None)
    if stats is not None:
        stats_json = json.loads(stats)
        logging.debug(f"Stats received: {stats_json}")
        return stats_json
    else:
        logging.error("Failed to retrieve stats from all servers.")
        return None

def downloadRadiobrowserStationsByCountry(countrycode):
    """
    Download stations by country code.

    Args:
        countrycode (str): The country code.

    Returns:
        list: A list of stations.
    """
    stations = downloadRadiobrowser(f"/json/stations/bycountrycodeexact/{countrycode}", None)
    if stations:
        stations_json = json.loads(stations)
        logging.debug(f"Stations received for country {countrycode}: {stations_json}")
        return stations_json
    else:
        logging.error(f"Failed to retrieve stations for country code {countrycode}")
        return []

def downloadRadiobrowserStationsByName(name):
    """
    Download stations by name.

    Args:
        name (str): The name of the station.

    Returns:
        list: A list of stations matching the name.
    """
    stations = downloadRadiobrowser("/json/stations/search", {"name": name})
    if stations:
        stations_json = json.loads(stations)
        logging.debug(f"Stations received with name {name}: {stations_json}")
        return stations_json
    else:
        logging.error(f"Failed to retrieve stations with name {name}")
        return []

if __name__ == "__main__":
    # Example usage and output
    logging.info("Stats")
    logging.info("------------")
    stats = downloadRadiobrowserStats()
    if stats:
        print(json.dumps(stats, indent=4))
    else:
        print("No stats available.")

    # Uncomment the following lines to fetch station info
    logging.info("Station Info")
    logging.info("------------")
    stations = downloadRadiobrowserStationsByName("Silver Rain")
    if stations:
        print(json.dumps(stations, indent=4))
    else:
        print("No station info available.")
