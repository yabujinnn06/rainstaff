// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.getElementById('sidebarToggle');
  const backdrop = document.getElementById('sidebarBackdrop');
  const body = document.body;

  if (toggle) {
    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('Hamburger clicked!');
      body.classList.toggle('sidebar-open');
      console.log('Sidebar open:', body.classList.contains('sidebar-open'));
    });
  } else {
    console.log('Hamburger button not found!');
  }

  if (backdrop) {
    backdrop.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('Backdrop clicked!');
      body.classList.remove('sidebar-open');
    });
  } else {
    console.log('Backdrop not found!');
  }

  // Close sidebar on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && body.classList.contains('sidebar-open')) {
      body.classList.remove('sidebar-open');
    }
  });

  // Close sidebar when clicking a link (mobile only)
  if (window.innerWidth <= 768) {
    const sidebarLinks = document.querySelectorAll('.sidebar a');
    sidebarLinks.forEach(link => {
      link.addEventListener('click', function() {
        body.classList.remove('sidebar-open');
      });
    });
  }

  // Desktop sidebar collapse toggle
  const collapseBtn = document.getElementById('sidebarCollapseBtn');
  if (collapseBtn) {
    collapseBtn.addEventListener('click', function() {
      body.classList.toggle('sidebar-collapsed');
      
      // Save preference to localStorage
      if (body.classList.contains('sidebar-collapsed')) {
        localStorage.setItem('sidebarCollapsed', 'true');
      } else {
        localStorage.removeItem('sidebarCollapsed');
      }
    });

    // Restore sidebar state from localStorage
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
      body.classList.add('sidebar-collapsed');
    }
  }
});
