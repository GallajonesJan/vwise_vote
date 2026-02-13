// Candidacy Form Handler with Photo Upload
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('candidacy-form');
    const affiliationSelect = document.getElementById('affiliation-type');
    const partylistGroup = document.getElementById('partylist-group');
    const partylistSelect = document.getElementById('partylist');
    const photoInput = document.getElementById('candidate-photo');
    const photoPreview = document.getElementById('photo-preview');
    const previewImage = document.getElementById('preview-image');

    let photoBase64 = null;

    // Photo upload and preview
    if (photoInput) {
        photoInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            
            if (!file) {
                hidePhotoPreview();
                return;
            }

            // Validate file type
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                alert('Please upload a JPG or PNG image.');
                photoInput.value = '';
                hidePhotoPreview();
                return;
            }

            // Validate file size (5MB max)
            const maxSize = 5 * 1024 * 1024; // 5MB in bytes
            if (file.size > maxSize) {
                alert('Image size must be less than 5MB. Please choose a smaller image.');
                photoInput.value = '';
                hidePhotoPreview();
                return;
            }

            // Read and preview the image
            const reader = new FileReader();
            reader.onload = function(event) {
                photoBase64 = event.target.result;
                previewImage.src = photoBase64;
                photoPreview.style.display = 'block';
                console.log('Photo loaded, size:', (photoBase64.length / 1024).toFixed(2), 'KB');
            };
            reader.onerror = function() {
                alert('Error reading file. Please try again.');
                hidePhotoPreview();
            };
            reader.readAsDataURL(file);
        });
    }

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

    // Load partylists from database
    async function loadPartylists() {
        try {
            const response = await fetch('/get-partylists');
            
            if (!response.ok) {
                throw new Error('Failed to fetch partylists from server');
            }
            
            const partylists = await response.json();
            
            // Clear existing options except the first one
            partylistSelect.innerHTML = '<option value="">Select Partylist</option>';
            
            // Check if there are any approved partylists
            if (partylists.length === 0) {
                partylistSelect.innerHTML = '<option value="">No approved partylists available</option>';
                partylistSelect.disabled = true;
                console.warn('No approved partylists found in database');
                return;
            }
            
            // Enable select and add partylists to dropdown
            partylistSelect.disabled = false;
            partylists.forEach(party => {
                const option = document.createElement('option');
                option.value = party.id;
                option.textContent = party.name || party.partylist_name;
                partylistSelect.appendChild(option);
            });
            
            console.log(`Loaded ${partylists.length} partylists successfully`);
        } catch (error) {
            console.error('Error loading partylists:', error);
            partylistSelect.innerHTML = '<option value="">Error loading partylists</option>';
            partylistSelect.disabled = true;
        }
    }

    // Remove photo function (global for onclick in HTML)
    window.removePhoto = function() {
        if (photoInput) {
            photoInput.value = '';
        }
        photoBase64 = null;
        hidePhotoPreview();
    };

    function hidePhotoPreview() {
        if (photoPreview) {
            photoPreview.style.display = 'none';
        }
        if (previewImage) {
            previewImage.src = '';
        }
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Validate photo is uploaded
        if (!photoBase64) {
            alert('Please upload your candidate photo.');
            return;
        }

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
            platform: document.getElementById('platform').value.trim(),
            photo: photoBase64  // Add photo base64 string
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
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading...';

        try {
            console.log('Submitting candidacy application with photo...');
            console.log('Photo size:', (photoBase64.length / 1024).toFixed(2), 'KB');
            
            const response = await fetch('/submit-candidacy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                alert(result.message || 'Application submitted successfully!');
                // Redirect to home page
                window.location.href = 'userhome.html';
            } else {
                throw new Error(result.error || result.message || 'Failed to submit application');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error submitting application: ' + error.message);
            
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
});