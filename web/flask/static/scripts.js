document.addEventListener('DOMContentLoaded', () => {
    // dark mode functionality based on time
    function checkTimeAndSetTheme() {
        const now = new Date();
        const hour = now.getHours();
        
        // dark mode between 6 PM (18:00) and 6 AM (06:00)
        const isDarkTime = hour >= 18 || hour < 6;
        
        // check if user has manually overridden the theme
        const manualTheme = localStorage.getItem('manualTheme');
        
        if (manualTheme) {
            // user has manually set theme, use that
            if (manualTheme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.documentElement.removeAttribute('data-theme');
            }
        } else {
            // use automatic time-based theme
            if (isDarkTime) {
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.documentElement.removeAttribute('data-theme');
            }
        }
    }
    
    // manual theme toggle functionality
    const themeToggle = document.getElementById('dark-mode-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const manualTheme = localStorage.getItem('manualTheme');
            
            if (currentTheme === 'dark') {
                // switch to light mode
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('manualTheme', 'light');
            } else {
                // switch to dark mode
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('manualTheme', 'dark');
            }
        });
    }
    
    // reset to automatic theme after 1 hour of manual override
    const manualThemeTime = localStorage.getItem('manualThemeTime');
    if (manualThemeTime) {
        const oneHour = 60 * 60 * 1000; // 1 hour in milliseconds
        if (Date.now() - parseInt(manualThemeTime) > oneHour) {
            localStorage.removeItem('manualTheme');
            localStorage.removeItem('manualThemeTime');
        }
    }
    
    // store time when manual theme is set
    const manualTheme = localStorage.getItem('manualTheme');
    if (manualTheme && !manualThemeTime) {
        localStorage.setItem('manualThemeTime', Date.now().toString());
    }
    
    // set initial theme
    checkTimeAndSetTheme();
    
    // check every minute for time changes
    setInterval(checkTimeAndSetTheme, 60000);

    // menu toggle
    const menuToggle = document.getElementById('menu-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            
            if (navMenu.classList.contains('show')) {
                // start slide-out animation
                navMenu.classList.remove('show');
                navMenu.classList.add('hide');
                
                // after animation ends, hide the menu
                navMenu.addEventListener('animationend', function handler() {
                    navMenu.style.display = 'none';
                    navMenu.classList.remove('hide');
                    navMenu.removeEventListener('animationend', handler);
                });
            } else {
                // display menu and start slide-in animation
                navMenu.style.display = 'flex';
                navMenu.classList.add('show');
            }
        });
    }

    // now playing panel
    const nowPlayingPanel = document.querySelector('.now-playing-panel');
    const nowPlayingToggle = document.getElementById('now-playing-toggle');
    const pauseButton = document.getElementById('pauseButton');
    const volumeSlider = document.getElementById('volumeSlider');
    const nowPlayingMarquee = document.getElementById('nowPlayingMarquee');
    
    // add no-animation class on page load
    nowPlayingPanel.classList.add('no-animation');
    
    // check stored state on page load
    // get stored panel state
    const isPanelOpen = localStorage.getItem('nowPlayingPanelOpen') === 'true';
    
    // apply stored state
    if (isPanelOpen) {
        nowPlayingPanel.classList.add('active');
    }
    
    // update now playing info
    async function updateNowPlaying() {
        try {
            const response = await fetch('/now_playing');
            const data = await response.json();
            const station = data.current_station;
            
            // update station info
            if (station.name) {
                nowPlayingMarquee.textContent = station.name;
                nowPlayingPanel.classList.add('has-content');
            } else {
                nowPlayingMarquee.textContent = 'Nothing playing';
                nowPlayingPanel.classList.remove('has-content');
            }
            
            // update play/pause state
            const pauseIcon = pauseButton.querySelector('.pause-icon');
            pauseIcon.classList.toggle('playing', !station.is_playing);
            
            // update toggle button animation
            nowPlayingToggle.classList.toggle('playing', station.is_playing);
            
            // update volume
            volumeSlider.value = station.volume;
        } catch (error) {
            console.debug('Error updating now playing:', error);
        }
    }
    
    // update now playing info periodically
    updateNowPlaying();
    setInterval(updateNowPlaying, 1000);
    
    // toggle panel and store state
    nowPlayingToggle?.addEventListener('click', () => {
        nowPlayingPanel.classList.toggle('active');
        
        // remove no-animation class when toggled
        nowPlayingPanel.classList.remove('no-animation');
        
        // store current state
        const isOpen = nowPlayingPanel.classList.contains('active');
        localStorage.setItem('nowPlayingPanelOpen', isOpen);
    });
    
    // handle pause/play
    pauseButton?.addEventListener('click', async () => {
        try {
            const response = await fetch('/now_playing');
            const data = await response.json();
            const isCurrentlyPlaying = data.current_station.is_playing;
            
            let result;
            if (isCurrentlyPlaying) {
                // if playing, stop it
                result = await fetch('/audio/stop', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
            } else {
                // if stopped, play it using existing radio endpoint
                const stations = await fetch('/state/station_scope.json').then(r => r.json());
                const stationUuid = data.current_station.stationuuid;
                const stationIndex = stations.findIndex(s => s.stationuuid === stationUuid);
                
                if (stationIndex !== -1) {
                    result = await fetch(`/radios/play/${stationIndex + 1}`);
                } else {
                    throw new Error('station not found');
                }
            }
            
            if (result.ok) {
                updateNowPlaying();
            }
        } catch (error) {
            console.error('Error toggling playback:', error);
        }
    });
    
    // handle volume
    let volumeTimeout;
    volumeSlider?.addEventListener('input', (e) => {
        const value = e.target.value;
        
        // update display immediately
        if (document.getElementById('volume-display')) {
            document.getElementById('volume-display').textContent = `${value}%`;
        }
        
        // update now playing state
        fetch('/now_playing').then(response => response.json())
            .then(data => {
                data.current_station.volume = parseInt(value);
                return fetch('/state/now_playing.json', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            })
            .catch(error => console.debug('Error updating now playing volume:', error));
        
        // debounce volume api call
        clearTimeout(volumeTimeout);
        volumeTimeout = setTimeout(() => {
            fetch('/audio/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ volume: parseInt(value) })
            });
        }, 100);
    });

    // page transitions
    const overlay = document.querySelector('.page-overlay');
    
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', e => {
            // only handle internal links
            if (link.hostname === window.location.hostname) {
                e.preventDefault();
                overlay.style.opacity = '1';
                
                setTimeout(() => {
                    window.location.href = link.href;
                }, 300);
            }
        });
    });

    // fade in on page load
    window.addEventListener('pageshow', () => {
        overlay.style.opacity = '0';
    });

    // add these with your other event listeners
    document.getElementById('previousButton').addEventListener('click', async () => {
        try {
            const response = await fetch('/radios/previous', {
                method: 'POST',
            });
            
            if (!response.ok) {
                throw new Error('Failed to change station');
            }
            
            // update now playing info after changing station
            await updateNowPlaying();
        } catch (error) {
            console.error('Error changing to previous station:', error);
        }
    });

    document.getElementById('nextButton').addEventListener('click', async () => {
        try {
            const response = await fetch('/radios/next', {
                method: 'POST',
            });
            
            if (!response.ok) {
                throw new Error('Failed to change station');
            }
            
            // update now playing info after changing station
            await updateNowPlaying();
        } catch (error) {
            console.error('Error changing to next station:', error);
        }
    });

    // helper function to update now playing display
    async function updateNowPlaying() {
        try {
            const response = await fetch('/now_playing');
            const data = await response.json();
            
            const marquee = document.getElementById('nowPlayingMarquee');
            const stationName = data.current_station.personal_title || data.current_station.name;
            marquee.textContent = stationName;
        } catch (error) {
            console.error('Error updating now playing info:', error);
        }
    }
    
    // infinite scroll functionality for radios page
    if (window.location.pathname === '/radios' && window.radioConfig) {
        const radiosList = document.getElementById('radiosList');
        const loadingIndicator = document.getElementById('loadingIndicator');
        const endOfList = document.getElementById('endOfList');
        
        let currentIndex = window.radioConfig.currentIndex;
        const totalStations = window.radioConfig.totalStations;
        const batchSize = window.radioConfig.batchSize;
        let isLoading = false;
        
        // function to load more stations
        async function loadMoreStations() {
            if (isLoading || currentIndex >= totalStations) return;
            
            isLoading = true;
            loadingIndicator.style.display = 'block';
            
            try {
                const response = await fetch('/radios/batch/' + currentIndex + '/' + batchSize);
                const data = await response.json();
                
                if (data.stations && data.stations.length > 0) {
                    // add new stations to the list
                    data.stations.forEach(station => {
                        const li = document.createElement('li');
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.id = 'radio-play-text';
                        button.textContent = station.name;
                        button.onclick = function() {
                            window.location.href = '/radios/play/' + station.radio_num;
                        };
                        
                        const link = document.createElement('a');
                        link.href = '/radios/' + station.radio_num;
                        link.className = 'radio-details-link';
                        link.textContent = '?';
                        
                        li.appendChild(button);
                        li.appendChild(link);
                        radiosList.appendChild(li);
                    });
                    
                    currentIndex += data.stations.length;
                    
                    // check if we've loaded all stations
                    if (!data.has_more || currentIndex >= totalStations) {
                        endOfList.style.display = 'block';
                    }
                }
            } catch (error) {
                console.error('error loading more stations:', error);
            } finally {
                isLoading = false;
                loadingIndicator.style.display = 'none';
            }
        }
        
        // infinite scroll detection
        function handleScroll() {
            const scrollPosition = window.innerHeight + window.scrollY;
            const documentHeight = document.documentElement.offsetHeight;
            
            // load more when user is near bottom (within 200px)
            if (scrollPosition >= documentHeight - 200) {
                loadMoreStations();
            }
        }
        
        // throttle scroll events
        let scrollTimeout;
        window.addEventListener('scroll', function() {
            if (scrollTimeout) {
                clearTimeout(scrollTimeout);
            }
            scrollTimeout = setTimeout(handleScroll, 100);
        });
    }
});
