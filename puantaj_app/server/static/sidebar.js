/**
 * Rainstaff Pro Sidebar - JavaScript Interactions
 * Handles sidebar collapse, toggle, menu interactions
 */

const SIDEBAR_CONFIG = {
  ANIMATION_DURATION: 300,
  COLLAPSE_BREAKPOINT: 768 // Mobile breakpoint
};

class Rainstaff_Sidebar {
  constructor() {
    this.sidebarEl = document.getElementById('sidebar');
    this.btnCollapse = document.getElementById('btn-collapse');
    this.btnToggle = document.getElementById('btn-toggle');
    this.overlay = document.getElementById('overlay');
    
    this.firstSubMenus = document.querySelectorAll(
      '.menu > ul > .menu-item.sub-menu > a'
    );
    this.innerSubMenus = document.querySelectorAll(
      '.menu > ul > .menu-item.sub-menu .menu-item.sub-menu > a'
    );
    
    this.init();
  }

  init() {
    if (!this.sidebarEl) return;
    
    this.attachEventListeners();
    this.initDefaultMenus();
    this.handleWindowResize();
  }

  /**
   * Attach all event listeners
   */
  attachEventListeners() {
    // Collapse button (desktop only)
    if (this.btnCollapse) {
      this.btnCollapse.addEventListener('click', () => this.toggleCollapse());
    }

    // Toggle button (mobile only)
    if (this.btnToggle) {
      this.btnToggle.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleSidebar();
      });
    }

    // Overlay click to close sidebar
    if (this.overlay) {
      this.overlay.addEventListener('click', () => this.toggleSidebar());
    }

    // First level submenu clicks
    this.firstSubMenus.forEach((element) => {
      element.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleFirstLevelSubmenu(element);
      });
    });

    // Inner submenu clicks
    this.innerSubMenus.forEach((element) => {
      element.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleInnerSubmenu(element);
      });
    });

    // Window resize handler
    window.addEventListener('resize', () => this.handleWindowResize());
  }

  /**
   * Toggle sidebar collapse state (desktop)
   */
  toggleCollapse() {
    if (!this.sidebarEl) return;
    
    this.sidebarEl.classList.toggle('collapsed');
    
    // Close all open submenus when collapsing
    if (this.sidebarEl.classList.contains('collapsed')) {
      this.firstSubMenus.forEach((element) => {
        const parent = element.parentElement;
        if (parent.classList.contains('open')) {
          parent.classList.remove('open');
          const subMenuList = element.nextElementSibling;
          if (subMenuList) {
            this.slideUp(subMenuList);
          }
        }
      });
    }
  }

  /**
   * Toggle sidebar visibility (mobile)
   */
  toggleSidebar() {
    if (!this.sidebarEl) return;
    
    this.sidebarEl.classList.toggle('toggled');
  }

  /**
   * Handle first-level submenu clicks
   */
  handleFirstLevelSubmenu(element) {
    if (!this.sidebarEl) return;
    
    const parentMenu = element.closest('.menu.open-current-submenu');
    const submenuList = element.nextElementSibling;
    
    if (!submenuList) return;

    // If collapsed, show popper menu
    if (this.sidebarEl.classList.contains('collapsed')) {
      const isVisible = submenuList.style.visibility === 'visible';
      submenuList.style.visibility = isVisible ? 'hidden' : 'visible';
    } else {
      // Normal expand/collapse
      if (parentMenu) {
        // Close other open submenus
        parentMenu.querySelectorAll(':scope > ul > .menu-item.sub-menu > a').forEach((el) => {
          const nextElement = el.nextElementSibling;
          if (nextElement && window.getComputedStyle(nextElement).display !== 'none') {
            if (el !== element) {
              this.slideUp(nextElement);
              el.parentElement.classList.remove('open');
            }
          }
        });
      }

      // Toggle current submenu
      if (submenuList.parentElement.classList.contains('open')) {
        this.slideUp(submenuList);
        submenuList.parentElement.classList.remove('open');
      } else {
        this.slideDown(submenuList);
        submenuList.parentElement.classList.add('open');
      }
    }
  }

  /**
   * Handle inner (nested) submenu clicks
   */
  handleInnerSubmenu(element) {
    const submenuList = element.nextElementSibling;
    
    if (!submenuList) return;

    if (submenuList.parentElement.classList.contains('open')) {
      this.slideUp(submenuList);
      submenuList.parentElement.classList.remove('open');
    } else {
      this.slideDown(submenuList);
      submenuList.parentElement.classList.add('open');
    }
  }

  /**
   * Smooth slide down animation
   */
  slideDown(target, duration = SIDEBAR_CONFIG.ANIMATION_DURATION) {
    const parent = target.parentElement;
    if (parent) {
      parent.classList.add('open');
    }

    target.style.removeProperty('display');
    let display = window.getComputedStyle(target).display;
    if (display === 'none') display = 'block';

    target.style.display = display;
    const height = target.offsetHeight;

    target.style.overflow = 'hidden';
    target.style.height = '0';
    target.style.paddingTop = '0';
    target.style.paddingBottom = '0';
    target.style.marginTop = '0';
    target.style.marginBottom = '0';

    // Trigger reflow
    target.offsetHeight;

    target.style.boxSizing = 'border-box';
    target.style.transitionProperty = 'height, margin, padding';
    target.style.transitionDuration = `${duration}ms`;
    target.style.height = `${height}px`;
    target.style.removeProperty('padding-top');
    target.style.removeProperty('padding-bottom');
    target.style.removeProperty('margin-top');
    target.style.removeProperty('margin-bottom');

    setTimeout(() => {
      target.style.removeProperty('height');
      target.style.removeProperty('overflow');
      target.style.removeProperty('transition-duration');
      target.style.removeProperty('transition-property');
    }, duration);
  }

  /**
   * Smooth slide up animation
   */
  slideUp(target, duration = SIDEBAR_CONFIG.ANIMATION_DURATION) {
    const parent = target.parentElement;
    if (parent) {
      parent.classList.remove('open');
    }

    target.style.transitionProperty = 'height, margin, padding';
    target.style.transitionDuration = `${duration}ms`;
    target.style.boxSizing = 'border-box';
    target.style.height = `${target.offsetHeight}px`;

    // Trigger reflow
    target.offsetHeight;

    target.style.overflow = 'hidden';
    target.style.height = '0';
    target.style.paddingTop = '0';
    target.style.paddingBottom = '0';
    target.style.marginTop = '0';
    target.style.marginBottom = '0';

    setTimeout(() => {
      target.style.display = 'none';
      target.style.removeProperty('height');
      target.style.removeProperty('padding-top');
      target.style.removeProperty('padding-bottom');
      target.style.removeProperty('margin-top');
      target.style.removeProperty('margin-bottom');
      target.style.removeProperty('overflow');
      target.style.removeProperty('transition-duration');
      target.style.removeProperty('transition-property');
    }, duration);
  }

  /**
   * Initialize default open menus
   */
  initDefaultMenus() {
    const defaultOpenMenus = document.querySelectorAll(
      '.menu-item.sub-menu.open'
    );

    defaultOpenMenus.forEach((element) => {
      const submenuList = element.lastElementChild;
      if (submenuList && submenuList.classList.contains('sub-menu-list')) {
        submenuList.style.display = 'block';
      }
    });
  }

  /**
   * Handle window resize - toggle collapse button visibility
   */
  handleWindowResize() {
    if (!this.btnCollapse) return;

    const isMobile = window.innerWidth <= SIDEBAR_CONFIG.COLLAPSE_BREAKPOINT;
    
    if (isMobile) {
      this.btnCollapse.style.display = 'none';
    } else {
      this.btnCollapse.style.display = 'flex';
    }
  }

  /**
   * Programmatic method to close sidebar (useful after clicking a menu item)
   */
  closeSidebar() {
    if (this.sidebarEl) {
      this.sidebarEl.classList.remove('toggled');
    }
  }

  /**
   * Set active menu item based on current URL
   */
  setActiveMenu(currentUrl) {
    const menuItems = document.querySelectorAll('.menu-item a');
    
    menuItems.forEach((item) => {
      const href = item.getAttribute('href');
      if (href && currentUrl.includes(href)) {
        item.closest('.menu-item').classList.add('active');
      } else {
        item.closest('.menu-item').classList.remove('active');
      }
    });
  }
}

// Initialize sidebar when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.rainstaffSidebar = new Rainstaff_Sidebar();
  
  // Set active menu based on current URL
  if (window.rainstaffSidebar && window.location.pathname) {
    window.rainstaffSidebar.setActiveMenu(window.location.pathname);
  }
});

// Close sidebar when clicking on a menu link (mobile)
document.addEventListener('click', (e) => {
  const link = e.target.closest('a[href]');
  const sidebar = document.getElementById('sidebar');
  
  if (link && sidebar && sidebar.classList.contains('toggled')) {
    // Don't close if it's a submenu toggle
    if (!link.closest('.menu-item.sub-menu')) {
      sidebar.classList.remove('toggled');
    }
  }
});
