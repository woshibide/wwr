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
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


logger = logging.getLogger(__name__)

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
        logger.debug(f"Base URLs retrieved: {base_urls}")
        return base_urls

    except Exception as e:
        logger.error(f"Error getting Radio Browser base URLs: {e}")
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
        logger.info(f"Request to {uri} with Params: {param}")
    else:
        logger.info(f"Request to {uri} with no parameters")

    req = urllib.request.Request(uri, data=param_encoded)

    # Change the user agent to name your app and version
    req.add_header('User-Agent', 'MyApp/0.0.1')
    req.add_header('Content-Type', 'application/json')

    context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urllib.request.urlopen(req, context=context) as response:
            data = response.read()
            logger.debug(f"Data received from {uri}")
            return data
    except Exception as e:
        logger.error(f"Error downloading data from {uri}: {e}")
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
        logger.info(f"Attempt {i+1}: Trying server {server_base}")
        uri = server_base + path

        try:
            data = downloadUri(uri, param)
            return data
        except Exception as e:
            logger.warning(f"Unable to download from API URL: {uri}. Error: {e}")
            continue
    logger.error("Failed to retrieve data from all servers.")
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
        logger.debug(f"Stats received: {stats_json}")
        return stats_json
    else:
        logger.error("Failed to retrieve stats from all servers.")
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
        logger.debug(f"Stations received for country {countrycode}: {stations_json}")
        return stations_json
    else:
        logger.error(f"Failed to retrieve stations for country code {countrycode}")
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
        logger.debug(f"Stations received with name {name}: {stations_json}")
        return stations_json
    else:
        logger.error(f"Failed to retrieve stations with name {name}")
        return []

def check_station_status(station_url, timeout=2):
    """check if a radio station is live by testing its stream"""
    try:
        # configure session with retry strategy
        session = requests.Session()
        retries = Retry(total=1, backoff_factor=0.1)
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        
        # only get the headers to check if stream is accessible
        response = session.head(
            station_url, 
            timeout=timeout,
            allow_redirects=True
        )
        
        # check if response is successful and content type is audio
        is_live = (
            response.status_code == 200 and
            'audio' in response.headers.get('content-type', '').lower()
        )
        
        logger.debug(f"station status check - url: {station_url}, live: {is_live}")
        return is_live
        
    except Exception as e:
        logger.debug(f"failed to check station status - url: {station_url}, error: {str(e)}")
        return False

def check_stations_batch(stations, max_workers=10):
    """check multiple stations status in parallel"""
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_uuid = {
            executor.submit(check_station_status, station['url']): station['stationuuid']
            for station in stations
        }
        
        for future in as_completed(future_to_uuid):
            station_uuid = future_to_uuid[future]
            try:
                is_live = future.result()
                results[station_uuid] = is_live
            except Exception as e:
                logger.error(f"error checking station {station_uuid}: {e}")
                results[station_uuid] = False
    
    return results

if __name__ == "__main__":
    # Example usage and output
    logger.info("Stats")
    logger.info("------------")
    stats = downloadRadiobrowserStats()
    if stats:
        print(json.dumps(stats, indent=4))
    else:
        print("No stats available.")

    # Uncomment the following lines to fetch station info
    logger.info("Station Info")
    logger.info("------------")
    stations = downloadRadiobrowserStationsByName("Silver Rain")
    if stations:
        print(json.dumps(stations, indent=4))
    else:
        print("No station info available.")
