document.addEventListener('DOMContentLoaded', function() {
    const profileMenu = document.querySelector('.profile-menu');
    const profileMenuLink = profileMenu.querySelector('a');
    const submenu = profileMenu.querySelector('.menu-links');
    
    submenu.style.display = 'none';
    
    profileMenuLink.addEventListener('click', function(e) {
        e.preventDefault();
        submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
    });
    
    profileMenu.addEventListener('mouseleave', function() {
        submenu.style.display = 'none';
    });
});