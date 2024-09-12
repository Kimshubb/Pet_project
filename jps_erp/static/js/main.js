document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const body = document.body;

    // Create overlay div if it doesn't exist
    let overlay = document.querySelector('.overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.classList.add('overlay');
        body.appendChild(overlay);
    }

    function toggleSidebar() {
        sidebar.classList.toggle('active');
        content.classList.toggle('active');
        overlay.classList.toggle('active');
        body.classList.toggle('sidebar-active');

        // Store sidebar state
        localStorage.setItem('sidebarState', sidebar.classList.contains('active') ? 'closed' : 'open');
    }

    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function(event) {
            event.stopPropagation();
            toggleSidebar();
        });
    }

    // Close sidebar when clicking on the overlay
    overlay.addEventListener('click', function() {
        if (sidebar.classList.contains('active')) {
            toggleSidebar();
        }
    });

    // Close sidebar when clicking outside on any screen size
    document.addEventListener('click', function(event) {
        const targetElement = event.target;
        if (sidebar.classList.contains('active') && 
            !sidebar.contains(targetElement) && 
            !sidebarCollapse.contains(targetElement)) {
            toggleSidebar();
        }
    });

    // Collapsible menu functionality
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const submenu = this.nextElementSibling;
            submenu.classList.toggle('show');
            this.setAttribute('aria-expanded', submenu.classList.contains('show'));
        });
    });

    // Active link and submenu
    const navLinks = document.querySelectorAll('#sidebar ul li a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!this.classList.contains('dropdown-toggle')) {
                e.preventDefault();
                navLinks.forEach(navLink => navLink.classList.remove('active'));
                this.classList.add('active');

                // Close sidebar on mobile when a link is clicked
                if (window.innerWidth <= 768) {
                    toggleSidebar();
                }

                // Navigate to the link
                window.location.href = this.getAttribute('href');
            }
        });
    });

    // Responsive table
    const tables = document.querySelectorAll('.table-responsive table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            row.querySelectorAll('td').forEach((cell, index) => {
                cell.setAttribute('data-label', headers[index].textContent);
            });
        });
    });

    // Ensure sidebar state is consistent across pages
    const sidebarState = localStorage.getItem('sidebarState');
    if (sidebarState === 'closed') {
        sidebar.classList.add('active');
        content.classList.add('active');
        overlay.classList.add('active');
        body.classList.add('sidebar-active');
    }

    // Handle window resizing
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
            content.classList.remove('active');
            overlay.classList.remove('active');
            body.classList.remove('sidebar-active');
        }
    });
});