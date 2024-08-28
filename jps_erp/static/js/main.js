document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const body = document.body;

    // Create overlay div
    const overlay = document.createElement('div');
    overlay.classList.add('overlay');
    body.appendChild(overlay);

    function toggleSidebar() {
        sidebar.classList.toggle('active');
        content.classList.toggle('active');
        overlay.classList.toggle('active');
        body.classList.toggle('sidebar-active');
    }

    sidebarCollapse.addEventListener('click', function(event) {
        event.stopPropagation();
        toggleSidebar();
    });

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
            !sidebar.contains(targetElement) && !sidebarCollapse.contains(targetElement)) {
            toggleSidebar();
        }
    });

    // Active link
    const navLinks = document.querySelectorAll('#sidebar ul li a');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.forEach(navLink => navLink.classList.remove('active'));
            this.classList.add('active');
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
});
