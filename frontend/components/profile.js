// Profile JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadProfile();
    setupForm();
});

// Load user profile on page load
async function loadProfile() {
    const loadingDiv = document.getElementById('loading');
    const contentDiv = document.getElementById('profile-content');
    const alertContainer = document.getElementById('alert-container');
    
    try {
        // Clear any previous alerts
        alertContainer.innerHTML = '';
        
        const response = await fetch('/get-user-profile');
        
        if (!response.ok) {
            throw new Error('Failed to fetch profile');
        }
        
        const user = await response.json();
        
        // Populate form fields
        document.getElementById('firstname').value = user.firstname || '';
        document.getElementById('middlename').value = user.middlename || '';
        document.getElementById('lastname').value = user.lastname || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('studentNumber').value = user.studentNumber || '';
        document.getElementById('yearlevel').value = user.yearlevel || '';
        document.getElementById('department').value = user.department || '';
        
        // Clear password field
        document.getElementById('password').value = '';
        
        // Show content, hide loading
        loadingDiv.style.display = 'none';
        contentDiv.style.display = 'block';
        
    } catch (error) {
        console.error('Error loading profile:', error);
        loadingDiv.innerHTML = '<p style="color: #f44336;">Error loading profile. Please try again.</p>';
        showAlert('Error loading profile. Please try again.', 'error');
    }
}

// Setup form submission handler
function setupForm() {
    const form = document.getElementById('profile-form');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';
        
        // Get form data
        const formData = {
            firstname: document.getElementById('firstname').value,
            middlename: document.getElementById('middlename').value,
            lastname: document.getElementById('lastname').value,
            email: document.getElementById('email').value,
            yearlevel: document.getElementById('yearlevel').value,
            department: document.getElementById('department').value,
            password: document.getElementById('password').value
        };
        
        try {
            const response = await fetch('/update-user-profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showAlert(result.message || 'Profile updated successfully!', 'success');
                // Clear password field after successful update
                document.getElementById('password').value = '';
            } else {
                throw new Error(result.error || 'Failed to update profile');
            }
            
        } catch (error) {
            console.error('Error updating profile:', error);
            showAlert(error.message || 'Error updating profile. Please try again.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        }
    });
}

// Show alert message
function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alertDiv);
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}
