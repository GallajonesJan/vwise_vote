// Get sidebar and toggle button elements
const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('toggle-btn');
const toggleIcon = toggleBtn.querySelector('svg');
const lightModeBtn = document.getElementById('light-mode-btn');
const toggleSwitch = document.querySelector('.toggle-switch');
const logoutBtn = document.getElementById('logout-btn');

// Toggle sidebar on button click
toggleBtn.addEventListener('click', () => {
  sidebar.classList.toggle('close');
  
  // Rotate the arrow icon
  if (sidebar.classList.contains('close')) {
    toggleIcon.style.rotate = '180deg';
  } else {
    toggleIcon.style.rotate = '0deg';
  }
});

// Expand sidebar on hover when closed
// Collapse sidebar when mouse leaves (only if it was previously closed)
let wasClosedBeforeHover = false;

sidebar.addEventListener('mouseenter', () => {
  if (sidebar.classList.contains('close')) {
    wasClosedBeforeHover = true;
    sidebar.classList.remove('close');
    toggleIcon.style.rotate = '0deg';
  } else {
    wasClosedBeforeHover = false;
  }
});

sidebar.addEventListener('mouseleave', () => {
  if (wasClosedBeforeHover) {
    sidebar.classList.add('close');
    toggleIcon.style.rotate = '180deg';
    wasClosedBeforeHover = false;
  }
});

// Light mode toggle
lightModeBtn.addEventListener('click', () => {
  toggleSwitch.classList.toggle('active');
  document.body.classList.toggle('light-mode');
  
  // Save preference to localStorage
  const isLightMode = document.body.classList.contains('light-mode');
  localStorage.setItem('lightMode', isLightMode);
});

// Load saved light mode preference
window.addEventListener('DOMContentLoaded', () => {
  const savedMode = localStorage.getItem('lightMode');
  if (savedMode === 'true') {
    document.body.classList.add('light-mode');
    toggleSwitch.classList.add('active');
  }
});

// Logout button
logoutBtn.addEventListener('click', () => {
  // Add your logout logic here
  if (confirm('Are you sure you want to logout?')) {
    // Redirect to login page or perform logout action
    window.location.href = 'login.html';
  }
});

// Dropdown toggle functionality
const dropdownToggle = document.querySelector('.dropdown-toggle');
const dropdown = document.querySelector('.dropdown');

if (dropdownToggle && dropdown) {
  dropdownToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
      dropdown.classList.remove('open');
    }
  });

  // Close dropdown when sidebar is closed
  toggleBtn.addEventListener('click', () => {
    if (sidebar.classList.contains('close')) {
      dropdown.classList.remove('open');
    }
  });
}