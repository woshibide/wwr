// dashboard.js - provides functionality for the radio dashboard

document.addEventListener('DOMContentLoaded', () => {
    // elements
    const stationName = document.getElementById('stationName');
    const stationMetadata = document.getElementById('stationMetadata');
    const stationDetailsLink = document.getElementById('stationDetailsLink');
    const stationLocation = document.getElementById('stationLocation');
    const stationTime = document.getElementById('stationTime');
    const stationWeatherText = document.getElementById('stationWeatherText');
    const localWeather = document.getElementById('localWeather');
    const localTime = document.getElementById('localTime');
    const localDate = document.getElementById('localDate');
    const favoritesList = document.getElementById('favoritesList');
    const dogImage = document.getElementById('dogImage');
    
    // keep legacy elements for compatibility
    const stationWeather = document.getElementById('stationWeather');
    
    // update local time
    function updateLocalTime() {
        const now = new Date();
        const timeOptions = { hour: '2-digit', minute: '2-digit', hour12: false };
        const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        
        localTime.textContent = now.toLocaleTimeString([], timeOptions);
        localDate.textContent = now.toLocaleDateString([], dateOptions);
    }
    
    // update local weather using direct api calls (simplified and robust)
    async function updateLocalWeather() {
        const titleElement = document.getElementById('localWeatherTitle');
        
        try {
            titleElement.textContent = 'fetching weather data...';
            console.log('starting weather update...');
            
            // get weather data directly
            const weatherData = await fetchWeatherDirectly();
            
            if (!weatherData) {
                console.warn('no weather data received, using placeholder');
                setPlaceholderLocalWeather();
                return;
            }
            
            console.log('weather data received:', weatherData);
            
            // validate required fields
            if (!weatherData.temperature || !weatherData.condition) {
                console.warn('incomplete weather data, using placeholder');
                setPlaceholderLocalWeather();
                return;
            }
            
            // get appropriate weather icon and generate dynamic title
            const weatherIcon = getWeatherIcon(weatherData.weather_code);
            const dynamicTitle = generateWeatherTitle(
                weatherIcon, 
                weatherData.location, 
                weatherData.temperature, 
                weatherData.humidity,
                weatherData.feels_like
            );
            
            titleElement.textContent = dynamicTitle;
            
            // update weather display with detailed information
            const weatherMain = localWeather.querySelector('.weather-main');
            const weatherDetails = localWeather.querySelector('.weather-details');
            
            if (weatherMain) {
                weatherMain.innerHTML = `
                    <div class="weather-icon">${weatherIcon}</div>
                    <div class="weather-temp">${weatherData.temperature}°C</div>
                `;
            }
            
            if (weatherDetails) {
                weatherDetails.innerHTML = `
                    <div class="weather-condition">${weatherData.condition.toLowerCase()}</div>
                    <div class="weather-location">${weatherData.location}</div>
                    <div class="weather-humidity">humidity: ${weatherData.humidity}%</div>
                    <div class="weather-feels-like">feels like: ${weatherData.feels_like}°C</div>
                `;
            }
            
            console.log('weather display updated successfully');
            
        } catch (error) {
            console.error('error updating local weather:', error);
            setPlaceholderLocalWeather();
        }
    }
    
    // direct api fallback function (improved with better error handling)
    async function fetchWeatherDirectly() {
        console.log('fetching weather data directly...');
        
        try {
            // step 1: get location data
            let locationData = null;
            let cityName = 'the hague'; // default fallback
            let locationDisplay = 'the hague, netherlands';
            
            try {
                console.log('getting location data...');
                const locationResponse = await fetch('https://ipapi.co/json/', { timeout: 5000 });
                if (locationResponse.ok) {
                    locationData = await locationResponse.json();
                    console.log('location data:', locationData);
                    
                    if (locationData.city) {
                        cityName = locationData.city.toLowerCase();
                        locationDisplay = `${locationData.city.toLowerCase()}, ${(locationData.country_name || 'unknown').toLowerCase()}`;
                    }
                }
            } catch (locationError) {
                console.warn('location api failed, using default:', locationError);
            }
            
            console.log(`using city: ${cityName}, display: ${locationDisplay}`);
            
            // step 2: fetch weather data
            console.log('fetching weather from wttr.in...');
            const weatherUrl = `https://wttr.in/${encodeURIComponent(cityName)}?format=j1`;
            console.log('weather url:', weatherUrl);
            
            const weatherResponse = await fetch(weatherUrl, { timeout: 10000 });
            
            if (!weatherResponse.ok) {
                throw new Error(`weather api returned status ${weatherResponse.status}`);
            }
            
            const responseText = await weatherResponse.text();
            console.log('weather response length:', responseText.length);
            
            // validate json response
            if (!responseText.trim().startsWith('{')) {
                console.error('non-json response:', responseText.substring(0, 200));
                throw new Error('weather api returned non-json response');
            }
            
            let weatherData;
            try {
                weatherData = JSON.parse(responseText);
            } catch (jsonError) {
                console.error('json parse error:', jsonError);
                throw new Error('failed to parse weather json');
            }
            
            console.log('parsed weather data:', weatherData);
            
            // validate data structure
            if (!weatherData.current_condition || !weatherData.current_condition[0]) {
                console.error('invalid weather data structure');
                throw new Error('missing current_condition in weather data');
            }
            
            const current = weatherData.current_condition[0];
            console.log('current condition:', current);
            
            // validate required fields
            if (!current.temp_C || !current.weatherDesc || !current.weatherDesc[0]) {
                console.error('missing required weather fields');
                throw new Error('incomplete weather data');
            }
            
            const result = {
                temperature: current.temp_C,
                feels_like: current.FeelsLikeC || current.temp_C,
                humidity: current.humidity || '0',
                condition: current.weatherDesc[0].value || 'unknown',
                weather_code: current.weatherCode || '113',
                location: locationDisplay
            };
            
            console.log('returning weather result:', result);
            return result;
            
        } catch (error) {
            console.error('fetchWeatherDirectly failed:', error);
            return null;
        }
    }
    
    // generate dynamic weather title
    function generateWeatherTitle(emoji, location, temp, humidity, feelsLike) {
        const timeOfDay = getTimeOfDay();
        const tempDescription = getTempDescription(temp);
        
        return `it is now ${emoji} ${tempDescription} in your ${location.toLowerCase()}, temperature is ${temp}°c, humidity is ${humidity}%. but it feels like ${feelsLike}°c`;
    }
    
    // get time of day description
    function getTimeOfDay() {
        const hour = new Date().getHours();
        if (hour >= 5 && hour < 12) return 'morning';
        if (hour >= 12 && hour < 17) return 'afternoon';
        if (hour >= 17 && hour < 21) return 'evening';
        return 'night';
    }
    
    // get temperature description
    function getTempDescription(temp) {
        const temperature = parseInt(temp);
        if (temperature <= 0) return 'freezing';
        if (temperature <= 10) return 'cold';
        if (temperature <= 20) return 'chilly';
        if (temperature <= 25) return 'pleasant';
        if (temperature <= 30) return 'warm';
        return 'hot';
    }
    
    // set placeholder local weather data when api fails
    function setPlaceholderLocalWeather() {
        console.error('setting placeholder weather data');
        const titleElement = document.getElementById('localWeatherTitle');
        titleElement.textContent = 'weather apis failed - check console for details';
        
        const weatherMain = localWeather.querySelector('.weather-main');
        const weatherDetails = localWeather.querySelector('.weather-details');
        
        if (weatherMain) {
            weatherMain.innerHTML = `
                <div class="weather-icon">❌</div>
                <div class="weather-temp">--°C</div>
            `;
        }
        
        if (weatherDetails) {
            weatherDetails.innerHTML = `
                <div class="weather-condition">api error</div>
                <div class="weather-location">the hague, netherlands (fallback)</div>
                <div class="weather-humidity">humidity: --%</div>
                <div class="weather-feels-like">feels like: --°C</div>
            `;
        }
    }
    
    // update station weather based on station location
    async function updateStationWeather(stationCountry, stationState, stationCity) {
        try {
            // if we don't have location info, use a default city or placeholder
            let city = stationCity || stationState || stationCountry || 'london';
            let locationDisplay = formatLocationDisplay(stationCity, stationState, stationCountry);
            
            if (!city) {
                setPlaceholderStationWeather(locationDisplay);
                return;
            }
            
            // clean city name - remove potentially problematic characters
            city = city.toString().trim();
            if (city.length === 0) {
                setPlaceholderStationWeather(locationDisplay);
                return;
            }
            
            // fetch weather data from wttr.in
            const response = await fetch(`https://wttr.in/${encodeURIComponent(city)}?format=j1`);
            
            if (!response.ok) {
                console.warn(`weather api returned status ${response.status} for city: ${city}`);
                setPlaceholderStationWeather();
                return;
            }
            
            // get response text first to check if it's valid json
            const responseText = await response.text();
            
            // check if response looks like json
            if (!responseText.trim().startsWith('{') && !responseText.trim().startsWith('[')) {
                console.warn('weather api returned non-json response:', responseText.substring(0, 200));
                setPlaceholderStationWeather();
                return;
            }
            
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (jsonError) {
                console.warn('failed to parse weather api json response:', jsonError.message);
                console.warn('response text:', responseText.substring(0, 500));
                setPlaceholderStationWeather();
                return;
            }
            
            // check if we have the expected data structure
            if (!data.current_condition || !data.current_condition[0]) {
                console.warn('unexpected weather api response structure:', data);
                setPlaceholderStationWeather();
                return;
            }
            
            const currentCondition = data.current_condition[0];
            
            // update station weather display
            const temp = currentCondition.temp_C;
            const weatherCode = currentCondition.weatherCode;
            const weatherIcon = getWeatherIcon(weatherCode);
            
            // update legacy weather display (if exists)
            if (stationWeather) {
                stationWeather.innerHTML = `
                    <div class="weather-icon">${weatherIcon}</div>
                    <div class="weather-temp">${temp}°C</div>
                `;
            }
            
            // update new text-based elements
            if (stationLocation) {
                stationLocation.textContent = locationDisplay;
            }
            
            if (stationWeatherText) {
                const feelsLike = currentCondition.FeelsLikeC || temp;
                const weatherDescription = currentCondition.weatherDesc?.[0]?.value?.toLowerCase() || 'unknown weather';
                stationWeatherText.textContent = `${weatherIcon} ${feelsLike}°c and ${weatherDescription}`;
            }
            
            // update station time based on location information
            updateStationTimeFromWeatherData(data, currentCondition);
        } catch (error) {
            console.error('error updating station weather:', error);
            setPlaceholderStationWeather();
        }
    }
    
    // set placeholder station weather
    function setPlaceholderStationWeather(locationDisplay = '') {
        // legacy elements for backward compatibility
        stationWeather.innerHTML = `
            <div class="weather-temp">--°C</div>
        `;
        
        // set placeholder time
        stationTime.textContent = '--:--';
        
        // new text-based elements
        if (stationLocation) {
            stationLocation.textContent = locationDisplay || 'location unknown';
        }
        if (stationTime) {
            stationTime.textContent = '--:--';
        }
        if (stationWeatherText) {
            stationWeatherText.textContent = '~no idea~';
        }
    }
    
    // update station time from a time string
    function updateStationTimeFromString(timeString) {
        try {
            if (!timeString || typeof timeString !== 'string') {
                stationTime.textContent = '--:--';
                return;
            }
            
            // extract time portion if it's a full datetime string
            const timePart = timeString.split(' ')[1] || timeString;
            const timeComponents = timePart.split(':');
            
            if (timeComponents.length >= 2) {
                const hours = timeComponents[0].padStart(2, '0');
                const minutes = timeComponents[1].padStart(2, '0');
                stationTime.textContent = `${hours}:${minutes}`;
            } else {
                stationTime.textContent = '--:--';
            }
        } catch (error) {
            console.error('error parsing station time:', error);
            stationTime.textContent = '--:--';
        }
    }
    
    // format location display for station info
    function formatLocationDisplay(city, state, country) {
        const parts = [city, state, country].filter(part => part && part.trim().length > 0);
        if (parts.length === 0) return 'somewhere in the world';
        return parts.join(', ').toLowerCase();
    }

    // set station details link
    function setStationDetailsLink(stationUuid) {
        if (!stationDetailsLink || !stationUuid) return;
        
        // try to find the station index for the details link
        fetch('/state/station_scope.json')
            .then(response => response.json())
            .then(stations => {
                const radioIndex = stations.findIndex(s => s.stationuuid === stationUuid);
                if (radioIndex !== -1) {
                    stationDetailsLink.href = `/radios/${radioIndex + 1}`;
                } else {
                    stationDetailsLink.href = '#';
                }
            })
            .catch(error => {
                console.debug('error setting station details link:', error);
                stationDetailsLink.href = '#';
            });
    }

    // update station time based on weather data
    function updateStationTimeFromWeatherData(data, currentCondition) {
        try {
            // use the location data from wttr.in to determine time zone
            if (data.time_zone && data.time_zone[0] && data.time_zone[0].localtime) {
                const localTimeStr = data.time_zone[0].localtime;
                updateStationTimeFromString(localTimeStr);
            } else {
                // fallback to estimating timezone from weather data
                if (currentCondition.localObsDateTime) {
                    try {
                        // try to parse as epoch timestamp first
                        const localTimeEpoch = parseInt(currentCondition.localObsDateTime, 10);
                        if (!isNaN(localTimeEpoch) && localTimeEpoch > 0) {
                            const stationDate = new Date(localTimeEpoch * 1000);
                            const hours = stationDate.getHours().toString().padStart(2, '0');
                            const minutes = stationDate.getMinutes().toString().padStart(2, '0');
                            if (stationTime) stationTime.textContent = `${hours}:${minutes}`;
                        } else {
                            // try to parse as date string
                            const stationDate = new Date(currentCondition.localObsDateTime);
                            if (!isNaN(stationDate.getTime())) {
                                const hours = stationDate.getHours().toString().padStart(2, '0');
                                const minutes = stationDate.getMinutes().toString().padStart(2, '0');
                                if (stationTime) stationTime.textContent = `${hours}:${minutes}`;
                            } else {
                                if (stationTime) stationTime.textContent = '--:--';
                            }
                        }
                    } catch (timeError) {
                        console.warn('error parsing station time:', timeError);
                        if (stationTime) stationTime.textContent = '--:--';
                    }
                } else {
                    if (stationTime) stationTime.textContent = '--:--';
                }
            }
        } catch (error) {
            console.warn('error updating station time:', error);
            if (stationTime) stationTime.textContent = '--:--';
        }
    }
    
    // get emoji for weather code with more comprehensive mapping
    function getWeatherIcon(weatherCode) {
        // weather codes from wttr.in/weatherCode
        const code = parseInt(weatherCode, 10);
        
        // clear/sunny
        if ([113].includes(code)) return '☀️';
        
        // partly cloudy
        if ([116, 119].includes(code)) return '⛅';
        
        // cloudy/overcast
        if ([122].includes(code)) return '☁️';
        
        // fog/mist
        if ([143, 248, 260].includes(code)) return '🌫️';
        
        // light rain/drizzle
        if ([176, 263, 266, 293, 296].includes(code)) return '🌦️';
        
        // moderate to heavy rain
        if ([299, 302, 305, 308, 311, 314, 317, 320].includes(code)) return '🌧️';
        
        // rain with thunder
        if ([281, 284].includes(code)) return '⛈️';
        
        // thunderstorm
        if ([200, 386, 389, 392, 395].includes(code)) return '⛈️';
        
        // light snow
        if ([179, 227, 323, 326, 368].includes(code)) return '🌨️';
        
        // moderate to heavy snow
        if ([182, 185, 230, 329, 332, 335, 338, 350, 371, 374, 377].includes(code)) return '❄️';
        
        // sleet/ice
        if ([317, 320, 350, 377].includes(code)) return '🧊';
        
        // windy
        if ([200, 395].includes(code)) return '💨';
        
        // default for unknown codes
        return '🌥️';
    }
    
    // fetch and display random dog image
    async function updateDogImage() {
        if (!dogImage) return;
        
        try {
            console.log('fetching cute dog image...');
            
            // add loading state
            dogImage.style.opacity = '0.5';
            
            // use dog.ceo api for random dog images
            const response = await fetch('https://dog.ceo/api/breeds/image/random', {
                cache: 'no-cache' // ensure we get a new image each time
            });
            
            if (!response.ok) {
                throw new Error(`dog api responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success' && data.message) {
                // preload the image to avoid layout shifts
                const img = new Image();
                img.onload = () => {
                    dogImage.src = data.message;
                    dogImage.style.display = 'block';
                    dogImage.style.opacity = '1';
                    console.log('cute dog image loaded successfully');
                };
                img.onerror = () => {
                    throw new Error('failed to load dog image');
                };
                img.src = data.message;
            } else {
                throw new Error('unexpected dog api response format');
            }
            
        } catch (error) {
            console.error('error fetching dog image:', error);
            // restore opacity even on error
            dogImage.style.opacity = '1';
            // fallback to hiding the image or keeping the previous one
            if (!dogImage.src) {
                dogImage.style.display = 'none';
            }
        }
    }
    
    // set loading state for station
    function setLoadingState(isLoading) {
        if (isLoading) {
            stationName.innerHTML = `
                <div class="loading-station">
                    <span class="loading-dot"></span>
                    <span class="loading-dot"></span>
                    <span class="loading-dot"></span>
                </div>
            `;
            stationMetadata.textContent = 'loading station...';
        }
    }
    
    // load favorite stations
    async function loadFavorites() {
        try {
            const response = await fetch('/state/user_settings.json');
            const data = await response.json();
            const favorites = data['Favourite Stations'] || [];
            
            if (favorites.length === 0) {
                favoritesList.innerHTML = '<p style="text-transform: lowercase; font-size: 1.5rem; color: black;">no favorites yet</p>';
                return;
            }
            
            // get currently playing station
            const nowPlayingResponse = await fetch('/now_playing');
            const nowPlaying = await nowPlayingResponse.json();
            const currentStationUuid = nowPlaying.current_station.stationuuid;
            
            // render favorites
            favoritesList.innerHTML = favorites.map(station => `
                <div class="favorite-station ${station.stationuuid === currentStationUuid ? 'active' : ''}" 
                     data-uuid="${station.stationuuid}">
                    <div class="favorite-station-info">
                        <div class="favorite-name">${station.name}</div>
                        <div class="favorite-title">${station.personal_title || station.name}</div>
                    </div>
                    <div class="dashboard-station-live-indicator ${station.is_it_live ? 'live' : ''}"></div>
                </div>
            `).join('');
            
            // add click event to favorites
            document.querySelectorAll('.favorite-station').forEach(element => {
                element.addEventListener('click', async () => {
                    const stationUuid = element.dataset.uuid;
                    
                    // find station index
                    let stationIndex = -1;
                    try {
                        const stationsResponse = await fetch('/state/station_scope.json');
                        if (stationsResponse.ok) {
                            const stations = await stationsResponse.json();
                            stationIndex = stations.findIndex(s => s.stationuuid === stationUuid);
                        }
                    } catch (error) {
                        console.error('Error fetching station scope:', error);
                    }
                    
                    // If we can't find the station in the scope, use its direct uuid for playing
                    if (stationIndex === -1) {
                        // Try to play directly using the station UUID
                        await fetch(`/radios/play/uuid/${stationUuid}`);
                        return;
                    }
                    
                    if (stationIndex !== -1) {
                        try {
                            // set loading state
                            setLoadingState(true);
                            
                            // play the station
                            await fetch(`/radios/play/${stationIndex + 1}`);
                            
                            // update active status
                            document.querySelectorAll('.favorite-station').forEach(el => {
                                el.classList.toggle('active', el.dataset.uuid === stationUuid);
                            });
                            
                            // update now playing info
                            updateNowPlaying();
                        } catch (error) {
                            console.error(`error playing station: ${error}`);
                        } finally {
                            // remove loading state
                            setLoadingState(false);
                        }
                    }
                });
            });
            
        } catch (error) {
            console.error('error loading favorites:', error);
            favoritesList.innerHTML = '<p style="text-transform: lowercase; font-size: 1.5rem; color: black;">failed to load favorites</p>';
        }
    }
    
    // update now playing info
    async function updateNowPlaying() {
        try {
            const response = await fetch('/now_playing');
            const data = await response.json();
            const station = data.current_station;
            
            // update station info
            if (station.name) {
                stationName.textContent = station.personal_title || station.name;
                stationMetadata.textContent = station.name;
                
                // get extended station info to find location data and radio number for details link
                try {
                    // try to get station location from station data
                    // first check if we have a direct city or country attribute in the station object
                    if (station.city || station.country || station.state) {
                        updateStationWeather(station.country, station.state, station.city);
                        // try to find radio number for details link
                        setStationDetailsLink(station.stationuuid);
                        return;
                    }
                    
                    // if not, try to fetch from station_scope.json
                    const stationsResponse = await fetch('/state/station_scope.json');
                    if (!stationsResponse.ok) {
                        // if we can't load the file, use placeholders
                        setPlaceholderStationWeather();
                        return;
                    }
                    
                    const stations = await stationsResponse.json();
                    
                    // find current station in the full station list
                    const currentStation = stations.find(s => s.stationuuid === station.stationuuid);
                    
                    if (currentStation) {
                        // get location data
                        const country = currentStation.country || '';
                        const state = currentStation.state || '';
                        const city = currentStation.city || '';
                        
                        // update station weather based on location
                        updateStationWeather(country, state, city);
                        
                        // set radio details link
                        const radioIndex = stations.findIndex(s => s.stationuuid === station.stationuuid);
                        if (radioIndex !== -1 && stationDetailsLink) {
                            stationDetailsLink.href = `/radios/${radioIndex + 1}`;
                        }
                    } else {
                        // if we can't find station data, try using the name as a location hint
                        updateStationWeather('', '', station.name.split(' ')[0]);
                        setStationDetailsLink(station.stationuuid);
                    }
                } catch (error) {
                    console.debug('error getting station location:', error);
                    setPlaceholderStationWeather();
                }
            } else {
                stationName.textContent = 'select a station';
                stationMetadata.textContent = 'no station playing';
                if (stationDetailsLink) {
                    stationDetailsLink.href = '#';
                }
                setPlaceholderStationWeather();
            }
        } catch (error) {
            console.debug('error updating now playing:', error);
        }
    }
    
    // update station live indicators
    async function updateStationsStatus() {
        try {
            const response = await fetch('/check_stations_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                console.warn('failed to check stations status');
                return;
            }
            
            const statusResults = await response.json();
            
            // update live indicators
            Object.entries(statusResults).forEach(([stationuuid, isLive]) => {
                const stationElement = document.querySelector(`[data-uuid="${stationuuid}"]`);
                if (stationElement) {
                    const indicator = stationElement.querySelector('.dashboard-station-live-indicator');
                    if (indicator) {
                        if (isLive) {
                            indicator.classList.add('live');
                        } else {
                            indicator.classList.remove('live');
                        }
                    }
                }
            });
        } catch (error) {
            console.error('error checking stations status:', error);
        }
    }
    
    // check station status
    async function checkStationsStatus() {
        try {
            // show checking status indicator
            const statusIndicator = document.createElement('div');
            statusIndicator.className = 'status-check-indicator';
            statusIndicator.textContent = 'checking station status...';
            statusIndicator.style.position = 'absolute';
            statusIndicator.style.bottom = '10px';
            statusIndicator.style.right = '10px';
            statusIndicator.style.fontSize = '0.8rem';
            statusIndicator.style.color = '#777';
            statusIndicator.style.padding = '5px 10px';
            statusIndicator.style.borderRadius = '4px';
            statusIndicator.style.backgroundColor = 'rgba(0,0,0,0.1)';
            document.querySelector('.favorites-panel').appendChild(statusIndicator);
            
            // check status
            await fetch('/check_stations_status', { method: 'POST' });
            
            // reload favorites to show updated status
            await loadFavorites();
            
            // update indicator
            statusIndicator.textContent = 'status updated';
            statusIndicator.style.backgroundColor = 'rgba(46, 204, 113, 0.2)';
            
            // remove indicator after 2 seconds
            setTimeout(() => {
                statusIndicator.remove();
            }, 2000);
        } catch (error) {
            console.error('error checking station status:', error);
        }
    }
    
    // initialize dashboard
    function initDashboard() {
        // initial load
        updateLocalTime();
        updateLocalWeather();
        updateNowPlaying();
        loadFavorites();
        updateDogImage();
        
        // check station status once at startup
        setTimeout(() => {
            checkStationsStatus();
            updateStationsStatus(); // also update live indicators
        }, 2000);
        
        // set up periodic updates
        setInterval(updateLocalTime, 1000); // update local time every second
        setInterval(updateLocalWeather, 15 * 60 * 1000); // update weather every 15 minutes
        setInterval(updateNowPlaying, 5000); // update now playing every 5 seconds
        setInterval(checkStationsStatus, 5 * 60 * 1000); // check station status every 5 minutes
        setInterval(updateStationsStatus, 10 * 60 * 1000); // update station live indicators every 10 minutes
        setInterval(updateDogImage, 60 * 1000); // update dog image every minute
    }
    
    // start dashboard
    initDashboard();
});
