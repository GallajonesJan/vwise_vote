// Partylist Registration Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('partylist-form');

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Get form data
        const formData = {
            partylist_name: document.getElementById('partylist-name').value.trim(),
            platform: document.getElementById('platform').value.trim(),
            president_name: document.getElementById('president-name').value.trim(),
            president_student_id: document.getElementById('president-student-id').value.trim(),
            contact_email: document.getElementById('contact-email').value.trim(),
            contact_number: document.getElementById('contact-number').value.trim()
        };

        // Validate all required fields
        const requiredFields = ['partylist_name', 'platform', 'president_name', 
                                'president_student_id', 'contact_email'];
        
        for (const field of requiredFields) {
            if (!formData[field]) {
                alert('Please fill in all required fields.');
                return;
            }
        }

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.contact_email)) {
            alert('Please enter a valid email address.');
            return;
        }

        // Disable submit button
        const submitBtn = form.querySelector('.btn-primary');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        try {
            const response = await fetch('/submit-partylist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                alert(result.message || 'Partylist registration submitted successfully!');
                // Redirect to home page
                window.location.href = 'userhome.html';
            } else {
                throw new Error(result.error || 'Failed to submit registration');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error submitting registration: ' + error.message);
            
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Registration';
        }
    });
});