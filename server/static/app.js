// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.getElementById('sidebarToggle');
  const backdrop = document.getElementById('sidebarBackdrop');
  const body = document.body;
  const sidebar = document.querySelector('.sidebar');

  // Set initial mobile sidebar state
  if (sidebar && window.innerWidth <= 1100) {
    sidebar.style.height = '0';
    sidebar.style.overflow = 'hidden';
  }

  if (toggle) {
    // Remove any existing listeners by cloning
    const newToggle = toggle.cloneNode(true);
    toggle.parentNode.replaceChild(newToggle, toggle);
    
    // Add new listener with capture phase (runs before bubble)
    newToggle.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      console.log('Hamburger clicked! Width:', window.innerWidth);
      
      const sidebar = document.querySelector('.sidebar');
      const isOpen = body.classList.contains('sidebar-open');
      
      console.log('Current state - isOpen:', isOpen);
      console.log('Sidebar element:', sidebar);
      
      if (isOpen) {
        // Close sidebar
        body.classList.remove('sidebar-open');
        body.classList.remove('sidebar-mobile-expanded'); // Remove old class too
        if (sidebar) {
          sidebar.style.height = '0';
          sidebar.style.overflow = 'hidden';
          sidebar.style.padding = '0';
          console.log('Sidebar closed');
        }
      } else {
        // Open sidebar
        body.classList.add('sidebar-open');
        body.classList.remove('sidebar-mobile-expanded'); // Remove old class
        if (sidebar) {
          sidebar.style.height = 'auto';
          sidebar.style.maxHeight = 'calc(100vh - 56px)';
          sidebar.style.overflow = 'auto';
          sidebar.style.overflowY = 'auto';
          sidebar.style.padding = '20px 16px';
          sidebar.style.display = 'block';
          console.log('Sidebar opened, height:', sidebar.style.height);
        }
      }
      
      console.log('New state - sidebar-open:', body.classList.contains('sidebar-open'));
      return false;
    }, true); // Use capture phase
  } else {
    console.log('Hamburger button not found!');
  }

  if (backdrop) {
    backdrop.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('Backdrop clicked!');
      body.classList.remove('sidebar-open');
      
      const sidebar = document.querySelector('.sidebar');
      if (sidebar && window.innerWidth <= 1100) {
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
      if (sidebar && window.innerWidth <= 1100) {
        sidebar.style.height = '0';
        sidebar.style.overflow = 'hidden';
      }
    }
  });

  // Close sidebar when clicking a link (mobile only)
  if (window.innerWidth <= 1100) {
    const sidebarLinks = document.querySelectorAll('.sidebar a');
    sidebarLinks.forEach(link => {
      link.addEventListener('click', function() {
        body.classList.remove('sidebar-open');
      });
    });
  }

  // Desktop sidebar collapse toggle (support both legacy and new IDs)
  const collapseBtn = document.getElementById('sidebarCollapseBtn') || document.getElementById('sidebarCollapse');
  const updateCollapseLabel = () => {
    if (!collapseBtn) return;
    const collapsed = body.classList.contains('sidebar-collapsed');
    // Update tooltip and accessible label without altering SVG content
    collapseBtn.setAttribute('data-tooltip', collapsed ? 'Genislet' : 'Daralt');
    collapseBtn.setAttribute('aria-label', collapsed ? 'Sidebar Genislet' : 'Sidebar Daralt');
  };
  if (collapseBtn) {
    collapseBtn.addEventListener('click', function() {
      // Ensure hidden state is cleared when toggling collapse
      body.classList.remove('sidebar-hidden');
      body.classList.toggle('sidebar-collapsed');

      // Save preference to localStorage
      if (body.classList.contains('sidebar-collapsed')) {
        localStorage.setItem('sidebarCollapsed', 'true');
      } else {
        localStorage.removeItem('sidebarCollapsed');
      }
      updateCollapseLabel();
    });

    // Restore sidebar state from localStorage
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
      body.classList.add('sidebar-collapsed');
    }
    // Initialize button text
    updateCollapseLabel();
  }
});
