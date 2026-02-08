// Get sidebar and toggle button elements
const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('toggle-btn');
const lightModeBtn = document.getElementById('light-mode-btn');
const toggleSwitch = document.querySelector('.toggle-switch');
const logoutBtn = document.getElementById('logout-btn');

// Check if we're on mobile/tablet
function isMobile() {
  return window.innerWidth <= 1024;
}

// Toggle sidebar collapse
toggleBtn.addEventListener('click', () => {
  sidebar.classList.toggle('collapsed');
  
  // Save sidebar state to localStorage
  const isCollapsed = sidebar.classList.contains('collapsed');
  localStorage.setItem('sidebarCollapsed', isCollapsed);
});

// Expand sidebar on hover when collapsed (desktop only)
let wasCollapsedBeforeHover = false;

sidebar.addEventListener('mouseenter', () => {
  if (!isMobile() && sidebar.classList.contains('collapsed')) {
    wasCollapsedBeforeHover = true;
    sidebar.classList.remove('collapsed');
  } else {
    wasCollapsedBeforeHover = false;
  }
});

sidebar.addEventListener('mouseleave', () => {
  if (!isMobile() && wasCollapsedBeforeHover) {
    sidebar.classList.add('collapsed');
    wasCollapsedBeforeHover = false;
  }
});

// Handle window resize
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (isMobile()) {
      // On mobile, remove collapsed class
      sidebar.classList.remove('collapsed');
    } else {
      // On desktop, restore saved state
      const savedCollapsed = localStorage.getItem('sidebarCollapsed');
      if (savedCollapsed === 'true') {
        sidebar.classList.add('collapsed');
      }
    }
  }, 250);
});

// Light/Dark mode toggle
lightModeBtn.addEventListener('click', () => {
  toggleSwitch.classList.toggle('active');
  document.body.classList.toggle('light-mode');
  document.body.classList.toggle('dark-mode');
  
  // Save preference to localStorage
  const isDarkMode = document.body.classList.contains('dark-mode');
  localStorage.setItem('darkMode', isDarkMode);
  
  // Update icon and text
  const icon = lightModeBtn.querySelector('svg path');
  const text = lightModeBtn.querySelector('span');
  
  if (isDarkMode) {
    text.textContent = 'Light Mode';
    // Sun icon path
    icon.setAttribute('d', 'M480-360q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35Zm0 80q-83 0-141.5-58.5T280-480q0-83 58.5-141.5T480-680q83 0 141.5 58.5T680-480q0 83-58.5 141.5T480-280ZM200-440H40v-80h160v80Zm720 0H760v-80h160v80ZM440-760v-160h80v160h-80Zm0 720v-160h80v160h-80ZM256-650l-101-97 57-59 96 100-52 56Zm492 496-97-101 53-55 101 97-57 59Zm-98-550 97-101 59 57-100 96-56-52ZM154-212l101-97 55 53-97 101-59-57Z');
  } else {
    text.textContent = 'Night Mode';
    // Moon icon path
    icon.setAttribute('d', 'M560-80q-82 0-155-31.5t-127.5-86Q223-252 191.5-325T160-480q0-83 31.5-155.5t86-127Q332-817 405-848.5T560-880q54 0 105 14t95 40q-91 53-145.5 143.5T560-480q0 112 54.5 202.5T760-134q-44 26-95 40T560-80Zm0-80h21q10 0 19-2-57-66-88.5-147.5T480-480q0-89 31.5-170.5T600-798q-9-2-19-2h-21q-133 0-226.5 93.5T240-480q0 133 93.5 226.5T560-160Zm-80-320Z');
  }
});

// Logout button
logoutBtn.addEventListener('click', () => {
  if (confirm('Are you sure you want to logout?')) {
    // Clear all stored data
    localStorage.clear();
    
    // Redirect to login page
    window.location.href = 'login.html';
  }
});

// Load saved preferences on page load
window.addEventListener('DOMContentLoaded', () => {
  // Load dark mode preference
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode === 'true') {
    document.body.classList.add('dark-mode');
    toggleSwitch.classList.add('active');
    
    const text = lightModeBtn.querySelector('span');
    text.textContent = 'Light Mode';
  }
  
  // Load sidebar collapsed state (desktop only)
  if (!isMobile()) {
    const savedCollapsed = localStorage.getItem('sidebarCollapsed');
    if (savedCollapsed === 'true') {
      sidebar.classList.add('collapsed');
    }
  }
  
  // Close sidebar on mobile by default
  if (isMobile()) {
    sidebar.classList.remove('collapsed');
  }
});

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
  if (isMobile()) {
    const isClickInsideSidebar = sidebar.contains(e.target);
    const isToggleBtn = e.target.closest('#toggle-btn');
    
    if (!isClickInsideSidebar && !isToggleBtn && !sidebar.classList.contains('collapsed')) {
      // Don't auto-collapse on mobile - let user control it
    }
  }
});

// Handle navigation clicks
document.querySelectorAll('.href').forEach(link => {
  link.addEventListener('click', (e) => {
    // Remove active class from all items
    document.querySelectorAll('#sidebar li').forEach(li => {
      li.classList.remove('active');
    });
    
    // Add active class to clicked item
    link.parentElement.classList.add('active');
    
    // On mobile, collapse sidebar after navigation
    if (isMobile()) {
      sidebar.classList.add('collapsed');
    }
  });
});

// Smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// Add swipe gesture support for mobile
let touchStartX = 0;
let touchEndX = 0;

function handleSwipe() {
  if (touchEndX < touchStartX - 50) {
    // Swipe left - collapse sidebar
    sidebar.classList.add('collapsed');
  }
  if (touchEndX > touchStartX + 50 && sidebar.classList.contains('collapsed')) {
    // Swipe right - expand sidebar
    sidebar.classList.remove('collapsed');
  }
}

sidebar.addEventListener('touchstart', e => {
  touchStartX = e.changedTouches[0].screenX;
}, { passive: true });

sidebar.addEventListener('touchend', e => {
  touchEndX = e.changedTouches[0].screenX;
  handleSwipe();
}, { passive: true });

// Update main content margin based on sidebar state
function updateMainMargin() {
  const main = document.querySelector('main');
  if (main) {
    if (isMobile()) {
      main.style.marginLeft = '0';
    } else if (sidebar.classList.contains('collapsed')) {
      main.style.marginLeft = '80px';
    } else {
      main.style.marginLeft = '250px';
    }
  }
}

// Observer for sidebar class changes
const observer = new MutationObserver(() => {
  updateMainMargin();
});

observer.observe(sidebar, {
  attributes: true,
  attributeFilter: ['class']
});

// Initial margin update
updateMainMargin();

// Accessibility: Handle keyboard navigation
toggleBtn.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    toggleBtn.click();
  }
});

lightModeBtn.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    lightModeBtn.click();
  }
});

logoutBtn.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    logoutBtn.click();
  }
});

// Add focus visible styles for accessibility
document.querySelectorAll('button, a').forEach(element => {
  element.addEventListener('focus', () => {
    element.style.outline = '2px solid #3b82f6';
    element.style.outlineOffset = '2px';
  });
  
  element.addEventListener('blur', () => {
    element.style.outline = 'none';
  });
});