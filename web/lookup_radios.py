"""
this is meant to return the list of available radios at a time

this is meant to be run daily to get fresh list of radios

"""

#!/bin/env python
import urllib.request
import certifi
import socket
import random
import urllib
import urllib.request
import json
import ssl


def get_radiobrowser_base_urls():
    """
    Get all base urls of all currently available radiobrowser servers

    Returns: 
    list: a list of strings

    """
    hosts = []
    # get all hosts from DNS
    ips = socket.getaddrinfo('all.api.radio-browser.info',
                             80, 0, 0, socket.IPPROTO_TCP)
    for ip_tupple in ips:
        ip = ip_tupple[4][0]

        # do a reverse lookup on every one of the ips to have a nice name for it
        host_addr = socket.gethostbyaddr(ip)
        # add the name to a list if not already in there
        if host_addr[0] not in hosts:
            hosts.append(host_addr[0])

    # sort list of names
    hosts.sort()
    # add "https://" in front to make it an url
    return list(map(lambda x: "https://" + x, hosts))

def downloadUri(uri, param):
    paramEncoded = None
    if param is not None:
        paramEncoded = json.dumps(param).encode('utf-8')
        print('Request to ' + uri + ' Params: ' + ','.join(param))
    else:
        print('Request to ' + uri)

    req = urllib.request.Request(uri, data=paramEncoded)
    
    # TODO: Change the user agent to name your app and version
    req.add_header('User-Agent', 'MyApp/0.0.1')
    req.add_header('Content-Type', 'application/json')

    context = ssl.create_default_context(cafile=certifi.where())

    response = urllib.request.urlopen(req, context=context)
    data = response.read()
    response.close()
    return data


def downloadRadiobrowser(path, param):
    """
    Download file with relative url from a random api server.
    Retry with other api servers if failed.

    Returns: 
    a string result

    """

    servers = get_radiobrowser_base_urls()
    random.shuffle(servers)
    for i, server_base in enumerate(servers):
        print(f'Random server: {server_base} Try: {i}')
        uri = server_base + path

        try:
            data = downloadUri(uri, param)
            return data
        except Exception as e:
            print(f"Unable to download from api url: {uri}", e)
            continue  
    return None  # to indicate failure

def downloadRadiobrowserStats():
    stats = downloadRadiobrowser("/json/stats", None)
    if stats is not None:
        return json.loads(stats)
    else:
        print("Failed to retrieve stats from all servers.")
        return None

def downloadRadiobrowserStationsByCountry(countrycode):
    stations = downloadRadiobrowser("/json/stations/bycountrycodeexact/" + countrycode, None)
    return json.loads(stations)

def downloadRadiobrowserStationsByName(name):
    stations = downloadRadiobrowser("/json/stations/search", {"name":name})
    return json.loads(stations)

# print list of names
print("All available urls")
print("------------------")
for host in get_radiobrowser_base_urls():
    print(host)
print("")

print("Stats")
print("------------")
print(json.dumps(downloadRadiobrowserStats(), indent=4))

"""

expected output:

Request to https://at1.api.radio-browser.info/json/stats
{
    "supported_version": 1,
    "software_version": "0.7.28",
    "status": "OK",
    "stations": 51946,
    "stations_broken": 373,
    "tags": 11178,
    "clicks_last_hour": 7699,
    "clicks_last_day": 156481,
    "languages": 749,
    "countries": 221
}

"""