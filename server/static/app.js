// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.getElementById('sidebarToggle');
  const backdrop = document.getElementById('sidebarBackdrop');
  const body = document.body;
  const sidebar = document.querySelector('.sidebar');

  // Set initial mobile sidebar state
  if (sidebar && window.innerWidth <= 768) {
    sidebar.style.height = '0';
    sidebar.style.overflow = 'hidden';
  }

  if (toggle) {
    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      console.log('Hamburger clicked!');
      
      const sidebar = document.querySelector('.sidebar');
      const isOpen = body.classList.contains('sidebar-open');
      
      if (isOpen) {
        // Close sidebar
        body.classList.remove('sidebar-open');
        if (sidebar && window.innerWidth <= 768) {
          sidebar.style.height = '0';
          sidebar.style.overflow = 'hidden';
        }
      } else {
        // Open sidebar
        body.classList.add('sidebar-open');
        if (sidebar && window.innerWidth <= 768) {
          sidebar.style.height = 'auto';
          sidebar.style.maxHeight = 'calc(100vh - 56px)';
          sidebar.style.overflow = 'auto';
          sidebar.style.padding = '20px 16px';
        }
      }
      
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
      
      const sidebar = document.querySelector('.sidebar');
      if (sidebar && window.innerWidth <= 768) {
        sidebar.style.height = '0';
        sidebar.style.overflow = 'hidden';
      }
    });
  } else {
    console.log('Backdrop not found!');
  }

  // Close sidebar on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && body.classList.contains('sidebar-open')) {
      body.classList.remove('sidebar-open');
      
      const sidebar = document.querySelector('.sidebar');
      if (sidebar && window.innerWidth <= 768) {
        sidebar.style.height = '0';
        sidebar.style.overflow = 'hidden';
      }
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
