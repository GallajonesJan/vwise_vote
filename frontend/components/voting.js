// Stores votes dynamically by position name
const votes = {};

const submitButton = document.getElementById('submit-vote-btn');
const positionsWrapper = document.getElementById('positions-wrapper');

console.log('=== VOTING PAGE DEBUG ===');
console.log('Submit button:', submitButton);
console.log('Positions wrapper:', positionsWrapper);

// Fetch candidates and render them
async function loadCandidates() {
    console.log('🔄 Loading candidates...');
    
    try {
        const response = await fetch('/get-candidates');
        console.log('📡 Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const candidatesByPosition = await response.json();
        console.log('📦 Candidates data:', candidatesByPosition);
        console.log('📊 Number of positions:', Object.keys(candidatesByPosition).length);

        // Clear existing content
        positionsWrapper.innerHTML = '';

        if (Object.keys(candidatesByPosition).length === 0) {
            positionsWrapper.innerHTML = `
                <div class="error-message" style="text-align: center; padding: 3rem; background: #fff3cd; border-radius: 8px; margin: 2rem;">
                    <h3 style="color: #856404;">No Approved Candidates Yet</h3>
                    <p style="color: #856404;">There are currently no approved candidates for voting. Please check back later or contact the administrator.</p>
                </div>
            `;
            console.warn('⚠️ No candidates found!');
            return;
        }

        // Define position order
        const positionOrder = [
            'President',
            'Vice President',
            'Secretary',
            'Assistant Secretary',
            'Treasurer',
            'Auditor',
            'PIO (Public Information Officer)',
            'COE Representative',
            'CBAA Representative',
            'CTE Representative',
            'CCS Representative',
            'CCJE Representative',
            'CIT Representative',
            'CAS Representative',
            'CHMT Representative'
        ];

        // Sort positions according to the defined order
        const sortedPositions = Object.keys(candidatesByPosition).sort((a, b) => {
            const indexA = positionOrder.indexOf(a);
            const indexB = positionOrder.indexOf(b);
            
            // If both positions are in the order list, sort by their index
            if (indexA !== -1 && indexB !== -1) {
                return indexA - indexB;
            }
            // If only A is in the list, it comes first
            if (indexA !== -1) return -1;
            // If only B is in the list, it comes first
            if (indexB !== -1) return 1;
            // If neither is in the list, sort alphabetically
            return a.localeCompare(b);
        });

        console.log('📋 Sorted positions:', sortedPositions);

        // Render each position in sorted order
        for (const position of sortedPositions) {
            const candidates = candidatesByPosition[position];
            console.log(`📝 Rendering position: ${position} with ${candidates.length} candidates`);
            
            if (candidates.length === 0) {
                console.warn(`⚠️ Position "${position}" has no candidates`);
                continue;
            }
            
            const positionContainer = createPositionSection(position, candidates);
            positionsWrapper.appendChild(positionContainer);
        }

        checkAllVotesCast();
        console.log('✅ Candidates loaded successfully!');
        
    } catch (error) {
        console.error('❌ Error loading candidates:', error);
        positionsWrapper.innerHTML = `
            <div class="error-message" style="text-align: center; padding: 3rem; background: #f8d7da; border-radius: 8px; margin: 2rem;">
                <h3 style="color: #721c24;">Failed to Load Candidates</h3>
                <p style="color: #721c24;">Error: ${error.message}</p>
                <p style="color: #721c24; font-size: 0.9rem; margin-top: 1rem;">Please check your browser console for more details.</p>
                <button onclick="location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Reload Page
                </button>
            </div>
        `;
    }
}

// Create a position section with candidate cards
function createPositionSection(position, candidates) {
    const container = document.createElement('div');
    container.className = 'position-container';

    const header = document.createElement('div');
    header.className = 'position-header';
    header.innerHTML = `
        <h2>${position}</h2>
        <p class="vote-instruction">Select one candidate (${candidates.length} candidate${candidates.length !== 1 ? 's' : ''})</p>
    `;

    const grid = document.createElement('div');
    grid.className = 'candidates-grid';

    candidates.forEach(candidate => {
        const card = createCandidateCard(candidate, position);
        grid.appendChild(card);
    });

    container.appendChild(header);
    container.appendChild(grid);

    return container;
}

// Create individual candidate card
function createCandidateCard(candidate, position) {
    const card = document.createElement('div');
    card.className = 'candidate-card';

    const radioId = `candidate-${candidate.id}`;

    card.innerHTML = `
        <div class="candidate-info">
            <h3 class="candidate-name">${candidate.full_name}</h3>
            <p class="candidate-party">${candidate.party}</p>
        </div>
        <button class="vote-btn" type="button">
            <input type="radio" 
                   name="${position}" 
                   value="${candidate.id}" 
                   id="${radioId}">
            <label for="${radioId}">Vote</label>
        </button>
    `;

    return card;
}

// Delegate clicks (works for dynamically created elements)
document.addEventListener('click', function (e) {
    if (e.target.closest('.vote-btn')) {
        const voteBtn = e.target.closest('.vote-btn');
        const card = voteBtn.closest('.candidate-card');
        const radio = voteBtn.querySelector('input[type="radio"]');
        
        if (!radio) return;

        const position = radio.name;
        const candidateId = radio.value;

        console.log(`🗳️ Vote selected: ${position} - Candidate ID: ${candidateId}`);

        // Remove "selected" class from all cards in this position
        document
            .querySelectorAll(`input[name="${position}"]`)
            .forEach(input => {
                input.closest('.candidate-card').classList.remove('selected');
            });

        // Mark selected card
        card.classList.add('selected');
        radio.checked = true;

        // Store vote
        votes[position] = {
            candidate_id: candidateId,
            name: card.querySelector('.candidate-name').textContent,
            party: card.querySelector('.candidate-party').textContent
        };

        console.log('Current votes:', votes);
        checkAllVotesCast();
    }
});

// Enable submit only if every position has a vote
function checkAllVotesCast() {
    const totalPositions = document.querySelectorAll('.position-container').length;
    const votedPositions = Object.keys(votes).length;

    console.log(`📊 Voted: ${votedPositions}/${totalPositions} positions`);
    submitButton.disabled = votedPositions !== totalPositions;
}

// Submit votes to Flask backend
submitButton.addEventListener('click', function () {
    const totalPositions = document.querySelectorAll('.position-container').length;

    if (Object.keys(votes).length !== totalPositions) {
        alert('Please vote for all positions before submitting.');
        return;
    }

    // Build confirmation message
    let confirmMessage = 'Please confirm your votes:\n\n';

    Object.entries(votes).forEach(([position, vote]) => {
        confirmMessage += `${position}: ${vote.name} (${vote.party})\n`;
    });

    confirmMessage += '\nAre you sure you want to submit? This action cannot be undone.';

    if (!confirm(confirmMessage)) return;

    console.log('🚀 Submitting votes:', votes);

    // Send votes to Flask
    fetch('/submit-vote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(votes)
    })
    .then(res => res.json())
    .then(data => {
        console.log('📬 Server response:', data);
        
        if (data.success) {
            alert('Your vote has been successfully submitted!');

            // Disable all inputs
            document
                .querySelectorAll('input[type="radio"]')
                .forEach(input => input.disabled = true);

            submitButton.disabled = true;
            submitButton.textContent = 'Vote Submitted';

            setTimeout(() => {
                window.location.href = '/userdashboard';
            }, 2000);
        } else {
            alert(data.error || data.message || 'Failed to submit vote.');
        }
    })
    .catch(err => {
        console.error('❌ Submit error:', err);
        alert('An error occurred while submitting your vote.');
    });
});

// Initial state
submitButton.disabled = true;

// Load candidates when page loads
console.log('🚀 Starting candidate load...');
loadCandidates();