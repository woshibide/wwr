document.addEventListener('DOMContentLoaded', function () {
    const menuToggle = document.getElementById('menu-toggle');
    const navMenu = document.getElementById('nav-menu');

    menuToggle.addEventListener('click', () => {
        menuToggle.classList.toggle('active');

        if (navMenu.classList.contains('show')) {
            // Start slide-out animation
            navMenu.classList.remove('show');
            navMenu.classList.add('hide');

            // After animation ends, hide the menu
            navMenu.addEventListener('animationend', function handler() {
                navMenu.style.display = 'none';
                navMenu.classList.remove('hide');
                navMenu.removeEventListener('animationend', handler);
            });
        } else {
            // Display menu and start slide-in animation
            navMenu.style.display = 'flex';
            navMenu.classList.add('show');
        }
    });
});
