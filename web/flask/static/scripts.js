document.addEventListener('DOMContentLoaded', () => {
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
});
