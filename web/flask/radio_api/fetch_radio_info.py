import json
import requests
import logging

logging.basicConfig(level=logging.INFO)

def fetch_stations(limit=50):
    url = f"https://de1.api.radio-browser.info/json/stations/search?limit={limit}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()   
    else:
        logging.error(f"Failed to retrieve data: {response.status_code}")
        return []

def save_stations_to_json(stations, filename='../state/station_scope.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(stations, f, ensure_ascii=False, indent=4)
    logging.info(f"Saved {len(stations)} stations to {filename}")



def main():
    logging.info("Fetching radio stations...")
    stations = fetch_stations(limit=100)  
    if stations:
        save_stations_to_json(stations)
    else:
        logging.warning("No stations found.")

if __name__ == "__main__":
    main()
