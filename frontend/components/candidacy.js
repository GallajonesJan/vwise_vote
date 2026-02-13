// Candidacy Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('candidacy-form');
    const affiliationSelect = document.getElementById('affiliation-type');
    const partylistGroup = document.getElementById('partylist-group');
    const partylistSelect = document.getElementById('partylist');

    // Show/hide partylist dropdown based on affiliation type
    affiliationSelect.addEventListener('change', function() {
        if (this.value === 'partylist') {
            partylistGroup.style.display = 'block';
            partylistSelect.required = true;
            loadPartylists();
        } else {
            partylistGroup.style.display = 'none';
            partylistSelect.required = false;
            partylistSelect.value = '';
        }
    });

    // Load partylists from database (you'll need to create this endpoint)
    async function loadPartylists() {
        try {
            const response = await fetch('/get-partylists');
            const partylists = await response.json();
            
            // Clear existing options except the first one
            partylistSelect.innerHTML = '<option value="">Select Partylist</option>';
            
            // Add partylists to dropdown
            partylists.forEach(party => {
                const option = document.createElement('option');
                option.value = party.id;
                option.textContent = party.name;
                partylistSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading partylists:', error);
        }
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Get form data
        const formData = {
            first_name: document.getElementById('first-name').value.trim(),
            last_name: document.getElementById('last-name').value.trim(),
            student_id: document.getElementById('student-id').value.trim(),
            email: document.getElementById('email').value.trim(),
            college: document.getElementById('college').value,
            year_level: document.getElementById('year-level').value,
            position: document.getElementById('position').value,
            affiliation_type: document.getElementById('affiliation-type').value,
            platform: document.getElementById('platform').value.trim()
        };

        // Add partylist_id if applicable
        if (formData.affiliation_type === 'partylist') {
            formData.partylist_id = document.getElementById('partylist').value;
            
            if (!formData.partylist_id) {
                alert('Please select a partylist.');
                return;
            }
        }

        // Validate all required fields
        const requiredFields = ['first_name', 'last_name', 'student_id', 'email', 
                                'college', 'year_level', 'position', 'affiliation_type', 'platform'];
        
        for (const field of requiredFields) {
            if (!formData[field]) {
                alert('Please fill in all required fields.');
                return;
            }
        }

        // Disable submit button
        const submitBtn = form.querySelector('.btn-primary');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        try {
            const response = await fetch('/submit-candidacy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                alert(result.message || 'Application submitted successfully!');
                // Redirect to home page
                window.location.href = 'userhome.html';
            } else {
                throw new Error(result.error || 'Failed to submit application');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error submitting application: ' + error.message);
            
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Application';
        }
    });
});