// View Candidates JavaScript

// Position mapping
const POSITIONS = {
    '1': 'President',
    '2': 'Vice President',
    '3': 'Secretary',
    '4': 'Assistant Secretary',
    '5': 'Treasurer',
    '6': 'Auditor',
    '7': 'PIO (Public Information Officer)',
    '8': 'COE Representative',
    '9': 'CBAA Representative',
    '10': 'CTE Representative',
    '11': 'CCS Representative',
    '12': 'CCJE Representative',
    '13': 'CIT Representative',
    '14': 'CAS Representative',
    '15': 'CHMT Representative'
};

let allCandidates = [];
let partylists = {};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCandidates();
    setupFilters();
});

// Setup filter event listeners
function setupFilters() {
    const positionFilter = document.getElementById('position-filter');
    const affiliationFilter = document.getElementById('affiliation-filter');

    positionFilter.addEventListener('change', filterCandidates);
    affiliationFilter.addEventListener('change', filterCandidates);
}

// Fetch candidates and partylists from API
async function loadCandidates() {
    const loadingDiv = document.getElementById('loading');
    const containerDiv = document.getElementById('candidates-container');
    const noCandidatesDiv = document.getElementById('no-candidates');

    try {
        // Show loading state
        loadingDiv.style.display = 'block';
        containerDiv.style.display = 'none';
        noCandidatesDiv.style.display = 'none';

        // Fetch partylists first
        const partylistsResponse = await fetch('/get-partylists');
        const partylistsData = await partylistsResponse.json();
        
        // Create partylists lookup
        partylistsData.forEach(party => {
            partylists[party.id] = party.name;
        });

        // Fetch candidates
        const response = await fetch('/get-candidates');
        
        if (!response.ok) {
            throw new Error('Failed to fetch candidates');
        }

        allCandidates = await response.json();
        
        // Hide loading, show content
        loadingDiv.style.display = 'none';

        if (allCandidates.length === 0) {
            noCandidatesDiv.style.display = 'block';
        } else {
            containerDiv.style.display = 'block';
            displayCandidates(allCandidates);
        }

    } catch (error) {
        console.error('Error loading candidates:', error);
        loadingDiv.style.display = 'none';
        noCandidatesDiv.style.display = 'block';
        noCandidatesDiv.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" height="64px" viewBox="0 -960 960 960" width="64px" fill="#999">
                <path d="M480-280q17 0 28.5-11.5T520-320q0-17-11.5-28.5T480-360q-17 0-28.5 11.5T440-320q0 17 11.5 28.5T480-280Zm-40-160h80v-240h-80v240Zm40 360q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Z"/>
            </svg>
            <p>Error loading candidates. Please try again later.</p>
        `;
    }
}

// Filter candidates based on selected filters
function filterCandidates() {
    const positionFilter = document.getElementById('position-filter').value;
    const affiliationFilter = document.getElementById('affiliation-filter').value;

    let filtered = allCandidates;

    // Filter by position
    if (positionFilter !== 'all') {
        filtered = filtered.filter(c => c.position === positionFilter);
    }

    // Filter by affiliation
    if (affiliationFilter !== 'all') {
        filtered = filtered.filter(c => c.affiliation_type === affiliationFilter);
    }

    displayCandidates(filtered);
}

// Display candidates organized by party and position
function displayCandidates(candidates) {
    const container = document.getElementById('candidates-container');
    const noCandidatesDiv = document.getElementById('no-candidates');

    if (candidates.length === 0) {
        container.style.display = 'none';
        noCandidatesDiv.style.display = 'block';
        return;
    }

    container.style.display = 'block';
    noCandidatesDiv.style.display = 'none';

    // Group candidates by partylist
    const grouped = groupCandidates(candidates);

    // Build HTML
    let html = '';

    // Display partylist groups first
    const partylistGroups = Object.entries(grouped.partylists).sort((a, b) => {
        return a[1].name.localeCompare(b[1].name);
    });

    partylistGroups.forEach(([partylistId, data]) => {
        html += createPartyGroup(data.name, data.candidates, false);
    });

    // Display independent candidates
    if (grouped.independent.length > 0) {
        html += createPartyGroup('Independent Candidates', grouped.independent, true);
    }

    container.innerHTML = html;

    // Add event listeners to view details buttons
    addViewDetailsListeners();
}

// Group candidates by partylist and position
function groupCandidates(candidates) {
    const result = {
        partylists: {},
        independent: []
    };

    candidates.forEach(candidate => {
        if (candidate.affiliation_type === 'partylist' && candidate.partylist_id) {
            const partylistId = candidate.partylist_id;
            const partylistName = partylists[partylistId] || `Partylist ${partylistId}`;

            if (!result.partylists[partylistId]) {
                result.partylists[partylistId] = {
                    name: partylistName,
                    candidates: []
                };
            }
            result.partylists[partylistId].candidates.push(candidate);
        } else {
            result.independent.push(candidate);
        }
    });

    // Sort candidates within each group by position
    Object.values(result.partylists).forEach(group => {
        group.candidates.sort((a, b) => parseInt(a.position) - parseInt(b.position));
    });
    result.independent.sort((a, b) => parseInt(a.position) - parseInt(b.position));

    return result;
}

// Create HTML for a party group
function createPartyGroup(name, candidates, isIndependent) {
    const iconSvg = isIndependent 
        ? '<svg xmlns="http://www.w3.org/2000/svg" height="32px" viewBox="0 -960 960 960" width="32px" fill="white"><path d="M480-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47ZM160-160v-112q0-34 17.5-62.5T224-378q62-31 126-46.5T480-440q66 0 130 15.5T736-378q29 15 46.5 43.5T800-272v112H160Z"/></svg>'
        : '<svg xmlns="http://www.w3.org/2000/svg" height="32px" viewBox="0 -960 960 960" width="32px" fill="white"><path d="M240-320q-33 0-56.5-23.5T160-400q0-33 23.5-56.5T240-480q33 0 56.5 23.5T320-400q0 33-23.5 56.5T240-320Zm480 0q-33 0-56.5-23.5T640-400q0-33 23.5-56.5T720-480q33 0 56.5 23.5T800-400q0 33-23.5 56.5T720-320Zm-240-40q-42 0-71-29t-29-71q0-42 29-71t71-29q42 0 71 29t29 71q0 42-29 71t-71 29Z"/></svg>';

    // Group by position
    const byPosition = {};
    candidates.forEach(candidate => {
        const position = POSITIONS[candidate.position] || `Position ${candidate.position}`;
        if (!byPosition[position]) {
            byPosition[position] = [];
        }
        byPosition[position].push(candidate);
    });

    let html = `
        <div class="party-group">
            <div class="party-header ${isIndependent ? 'independent' : ''}">
                ${iconSvg}
                <h2>${name}</h2>
                <span class="candidate-count">${candidates.length} candidate${candidates.length !== 1 ? 's' : ''}</span>
            </div>
    `;

    // Create sections for each position
    Object.entries(byPosition).forEach(([position, positionCandidates]) => {
        html += `
            <div class="position-section">
                <div class="position-title">${position}</div>
                <div class="candidates-grid">
                    ${positionCandidates.map(candidate => createCandidateCard(candidate)).join('')}
                </div>
            </div>
        `;
    });

    html += '</div>';
    return html;
}

// Create HTML for a candidate card
function createCandidateCard(candidate) {
    const initials = `${candidate.first_name.charAt(0)}${candidate.last_name.charAt(0)}`;
    const photoHtml = candidate.photo 
        ? `<img src="${candidate.photo}" alt="${candidate.first_name} ${candidate.last_name}">`
        : `<div class="candidate-photo no-photo">${initials}</div>`;

    const affiliationBadge = candidate.affiliation_type === 'partylist'
        ? `<span class="affiliation-badge partylist">${partylists[candidate.partylist_id] || 'Partylist'}</span>`
        : `<span class="affiliation-badge independent">Independent</span>`;

    return `
        <div class="candidate-card" data-candidate-id="${candidate.id}">
            <div class="candidate-photo">
                ${photoHtml}
            </div>
            <div class="candidate-info">
                <h3 class="candidate-name">${candidate.first_name} ${candidate.last_name}</h3>
                
                <div class="candidate-details">
                    <div class="detail-row">
                        <svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 -960 960 960" width="18px" fill="currentColor">
                            <path d="M480-120 200-272v-240L40-600l440-240 440 240v320h-80v-276l-80 44v240L480-120Zm0-332 274-148-274-148-274 148 274 148Zm0 241 200-108v-151L480-360 280-470v151l200 108Zm0-241Zm0 90Zm0 0Z"/>
                        </svg>
                        <span><span class="detail-label">College:</span> ${candidate.college}</span>
                    </div>
                    <div class="detail-row">
                        <svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 -960 960 960" width="18px" fill="currentColor">
                            <path d="M200-80q-33 0-56.5-23.5T120-160v-560q0-33 23.5-56.5T200-800h40v-80h80v80h320v-80h80v80h40q33 0 56.5 23.5T840-720v560q0 33-23.5 56.5T760-80H200Zm0-80h560v-400H200v400Z"/>
                        </svg>
                        <span><span class="detail-label">Year:</span> ${candidate.year_level}</span>
                    </div>
                </div>

                ${affiliationBadge}

                <div class="candidate-platform">
                    <div class="platform-label">Platform:</div>
                    <div class="platform-text">${candidate.platform}</div>
                </div>

                <button class="view-details-btn" data-candidate-id="${candidate.id}">
                    View Full Details
                </button>
            </div>
        </div>
    `;
}

// Add event listeners to view details buttons
function addViewDetailsListeners() {
    const buttons = document.querySelectorAll('.view-details-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const candidateId = parseInt(this.getAttribute('data-candidate-id'));
            showCandidateModal(candidateId);
        });
    });

    // Also make cards clickable
    const cards = document.querySelectorAll('.candidate-card');
    cards.forEach(card => {
        card.addEventListener('click', function() {
            const candidateId = parseInt(this.getAttribute('data-candidate-id'));
            showCandidateModal(candidateId);
        });
    });
}

// Show candidate details in modal
function showCandidateModal(candidateId) {
    const candidate = allCandidates.find(c => c.id === candidateId);
    if (!candidate) return;

    const initials = `${candidate.first_name.charAt(0)}${candidate.last_name.charAt(0)}`;
    const photoHtml = candidate.photo 
        ? `<img src="${candidate.photo}" alt="${candidate.first_name} ${candidate.last_name}" class="modal-photo">`
        : `<div class="modal-photo no-photo">${initials}</div>`;

    const partylistName = candidate.affiliation_type === 'partylist' && candidate.partylist_id
        ? partylists[candidate.partylist_id] || 'Unknown Partylist'
        : 'Independent';

    const modalHtml = `
        <div id="candidate-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${candidate.first_name} ${candidate.last_name}</h2>
                    <button class="close-btn" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    ${photoHtml}
                    
                    <div class="modal-details">
                        <div class="modal-detail-item">
                            <span class="modal-detail-label">Student ID</span>
                            <span class="modal-detail-value">${candidate.student_id}</span>
                        </div>
                        <div class="modal-detail-item">
                            <span class="modal-detail-label">Email</span>
                            <span class="modal-detail-value">${candidate.email}</span>
                        </div>
                        <div class="modal-detail-item">
                            <span class="modal-detail-label">College</span>
                            <span class="modal-detail-value">${candidate.college}</span>
                        </div>
                        <div class="modal-detail-item">
                            <span class="modal-detail-label">Year Level</span>
                            <span class="modal-detail-value">${candidate.year_level}</span>
                        </div>
                        <div class="modal-detail-item">
                            <span class="modal-detail-label">Position</span>
                            <span class="modal-detail-value">${POSITIONS[candidate.position]}</span>
                        </div>
                        <div class="modal-detail-item">
                            <span class="modal-detail-label">Affiliation</span>
                            <span class="modal-detail-value">${partylistName}</span>
                        </div>
                    </div>

                    <div class="modal-platform">
                        <h3>Platform & Advocacy</h3>
                        <p>${candidate.platform}</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    const existingModal = document.getElementById('candidate-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = document.getElementById('candidate-modal');
    modal.style.display = 'block';

    // Close on outside click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

// Close modal
function closeModal() {
    const modal = document.getElementById('candidate-modal');
    if (modal) {
        modal.style.display = 'none';
        setTimeout(() => modal.remove(), 300);
    }
}

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});