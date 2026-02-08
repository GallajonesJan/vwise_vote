// Store votes for each position
const votes = {
    president: null,
    'vice-president': null,
    secretary: null,
    treasurer: null
};

// Get all vote buttons
const voteButtons = document.querySelectorAll('.vote-btn');
const submitButton = document.getElementById('submit-vote-btn');

// Handle vote button clicks
voteButtons.forEach(button => {
    button.addEventListener('click', function() {
        const position = this.getAttribute('data-position');
        const candidate = this.getAttribute('data-candidate');
        
        // Remove selected class from all cards in this position
        const positionCards = document.querySelectorAll(`[data-position="${position}"]`)
            .forEach(btn => {
                btn.closest('.candidate-card').classList.remove('selected');
            });
        
        // Add selected class to clicked card
        this.closest('.candidate-card').classList.add('selected');
        
        // Store the vote
        votes[position] = {
            candidate: candidate,
            name: this.closest('.candidate-card').querySelector('.candidate-name').textContent,
            party: this.closest('.candidate-card').querySelector('.candidate-party').textContent
        };
        
        // Check if all positions have votes
        checkAllVotesCast();
    });
});

// Check if all positions have been voted for
function checkAllVotesCast() {
    const allVoted = Object.values(votes).every(vote => vote !== null);
    submitButton.disabled = !allVoted;
}

// Handle submit vote
submitButton.addEventListener('click', function() {
    // Check if all votes are cast
    if (Object.values(votes).every(vote => vote !== null)) {
        // Create confirmation message
        let confirmMessage = 'Please confirm your votes:\n\n';
        confirmMessage += `President: ${votes.president.name} (${votes.president.party})\n`;
        confirmMessage += `Vice President: ${votes['vice-president'].name} (${votes['vice-president'].party})\n`;
        confirmMessage += `Secretary: ${votes.secretary.name} (${votes.secretary.party})\n`;
        confirmMessage += `Treasurer: ${votes.treasurer.name} (${votes.treasurer.party})\n`;
        confirmMessage += '\nAre you sure you want to submit? This action cannot be undone.';
        
        if (confirm(confirmMessage)) {
            // Here you would send the votes to your backend
            console.log('Votes submitted:', votes);
            
            // Show success message
            alert('Your vote has been successfully submitted! Thank you for participating.');
            
            // Disable all vote buttons
            voteButtons.forEach(btn => btn.disabled = true);
            submitButton.disabled = true;
            submitButton.textContent = 'Vote Submitted';
            
            // Optional: Redirect to home page after a delay
            setTimeout(() => {
                window.location.href = 'userhome.html';
            }, 2000);
        }
    } else {
        alert('Please vote for all positions before submitting.');
    }
});

// Initialize: Disable submit button on load
submitButton.disabled = true;