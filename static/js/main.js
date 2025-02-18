// Theme handling

// Form handling
const taskForm = document.getElementById('task-form');
const processButton = document.getElementById('process-tasks-btn');
const loadingOverlay = document.getElementById('loading-overlay');
const resultsContainer = document.getElementById('results-container');
const queueList = document.getElementById('queue-list');
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const importanceSlider = document.getElementById('importance');
const sliderValue = document.querySelector('.slider-value');

// Initialize slider value display
function updateSliderValue(value) {
    sliderValue.textContent = value;
    const percent = ((value - importanceSlider.min) / (importanceSlider.max - importanceSlider.min)) * 100;
    sliderValue.style.left = `${percent}%`;
    
    // Update track color
    importanceSlider.style.background = `linear-gradient(to right, 
        var(--primary-color) 0%, 
        var(--primary-color) ${percent}%, 
        var(--border-color) ${percent}%, 
        var(--border-color) 100%)`;
}

// Set initial slider value
updateSliderValue(importanceSlider.value);

// Update slider value on change
importanceSlider.addEventListener('input', (e) => {
    updateSliderValue(e.target.value);
});

// Theme handling
let isDarkTheme = localStorage.getItem('darkTheme') === 'true';
if (isDarkTheme) {
    document.body.classList.add('dark-theme');
    themeToggleBtn.textContent = '☀️';
}

themeToggleBtn.addEventListener('click', () => {
    isDarkTheme = !isDarkTheme;
    document.body.classList.toggle('dark-theme');
    localStorage.setItem('darkTheme', isDarkTheme);
    themeToggleBtn.textContent = isDarkTheme ? '☀️' : '🌙';
});

// Form submission
taskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log('Form submitted');  // Debug log
    
    const query = document.getElementById('query').value;
    const category = document.getElementById('category').value;
    const importance = document.getElementById('importance').value;

    if (!query) {
        showNotification('Query cannot be empty', 'error');
        return;
    }

    const formData = {
        query: query,
        category: category || 'general',
        importance: parseInt(importance || '1')
    };

    console.log('Sending task:', formData);  // Debug log
    showNotification('Adding task...', 'info');

    try {
        const response = await fetch('http://localhost:5002/api/add-task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Server response:', data);  // Debug log

        if (data.status === 'success') {
            taskForm.reset();
            await updateQueueStatus();
            showNotification('Task added successfully!', 'success');
            processButton.disabled = false;
        } else {
            showNotification(data.message || 'Error adding task', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification(`Error adding task: ${error.message}`, 'error');
    }
});

// Process tasks button
processButton.addEventListener('click', async () => {
    console.log('Processing tasks...');  // Debug log
    loadingOverlay.classList.remove('hidden');
    showNotification('Processing tasks...', 'info');
    
    try {
        const response = await fetch('http://localhost:5002/api/process-tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Process tasks response:', data);  // Debug log
        
        if (data.status === 'success' && data.results) {
            displayResults(data.results);
            await updateQueueStatus();
            showNotification('Tasks processed successfully!', 'success');
        } else {
            showNotification(data.message || 'Error processing tasks', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification(`Error processing tasks: ${error.message}`, 'error');
    } finally {
        loadingOverlay.classList.add('hidden');
    }
});

// Display results
function displayResults(results) {
    console.log('Displaying results:', results);  // Debug log
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<p>No results to display.</p>';
        return;
    }

    resultsContainer.innerHTML = results.map(result => {
        const query = result.query;
        const highlightedQuery = highlightKeywords(query);
        
        return `
            <div class="result-card">
                <div class="result-header">
                    <div class="query-section">
                        <div class="query-text">${highlightedQuery}</div>
                        <div class="category-badge">${escapeHtml(result.category)}</div>
                    </div>
                    <div class="status-badge ${result.result.status}">
                        ${formatStatus(result.result.status)}
                    </div>
                </div>
                
                ${result.result.error ? 
                    `<div class="error-message">${escapeHtml(result.result.error)}</div>` :
                    `<div class="result-content">
                        <div class="research-results">
                            <h4>Research Results:</h4>
                            <p>${formatContent(result.result.research_results.answer || 'No answer available')}</p>
                        </div>
                        
                        <div class="reasoning-analysis">
                            <h4>AI Analysis:</h4>
                            <p>${formatContent(result.result.reasoning_analysis || 'No analysis available')}</p>
                        </div>
                        
                        ${result.result.research_results.sources ? `
                            <div class="sources-section">
                                <h4>Sources:</h4>
                                <div class="source-list">
                                    ${result.result.research_results.sources.map(source => `
                                        <a href="${escapeHtml(source.url)}" class="source-item" target="_blank">
                                            ${escapeHtml(source.title || source.url)}
                                        </a>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="follow-up-section">
                            <h4>Suggested Follow-up Questions:</h4>
                            <div class="follow-up-questions">
                                ${generateFollowUpQuestions(query).map(q => `
                                    <button class="follow-up-question" onclick="addFollowUpQuery('${escapeHtml(q)}')">${escapeHtml(q)}</button>
                                `).join('')}
                            </div>
                        </div>
                    </div>`
                }
            </div>
        `;
    }).join('');
}

// Helper function to highlight keywords
function highlightKeywords(text) {
    const keywords = [
        'how', 'what', 'why', 'when', 'where', 'which', 'who',
        'influence', 'affect', 'impact', 'cause', 'effect', 'relationship',
        'function', 'process', 'system', 'mechanism', 'role'
    ];
    
    return text.split(' ').map(word => {
        const lowerWord = word.toLowerCase();
        if (keywords.includes(lowerWord)) {
            return `<span class="highlight">${word}</span>`;
        }
        return word;
    }).join(' ');
}

// Helper function to format content with highlights
function formatContent(text) {
    const keywords = [
        'influence', 'affect', 'impact', 'cause', 'effect', 'relationship',
        'function', 'process', 'system', 'mechanism', 'role', 'significant',
        'important', 'crucial', 'essential', 'key', 'main', 'primary'
    ];
    
    return text.split(' ').map(word => {
        const lowerWord = word.toLowerCase();
        if (keywords.includes(lowerWord)) {
            return `<span class="highlight-word">${word}</span>`;
        }
        return word;
    }).join(' ');
}

// Generate follow-up questions based on the original query
function generateFollowUpQuestions(query) {
    const baseQuestions = [
        'What are the latest developments in this field?',
        'How does this relate to overall health?',
        'What are the practical applications?',
        'What are the main challenges?',
        'How can this knowledge be applied in daily life?'
    ];
    
    return baseQuestions;
}

// Add follow-up query to the input
function addFollowUpQuery(question) {
    const queryInput = document.getElementById('query');
    queryInput.value = question;
    queryInput.focus();
}

// Update queue status
async function updateQueueStatus() {
    try {
        const response = await fetch('http://localhost:5002/api/queue-status', {
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Queue status:', data);  // Debug log
        
        if (data.status === 'success' && data.tasks) {
            if (data.tasks.length === 0) {
                queueList.innerHTML = '<p>No tasks in queue.</p>';
                processButton.disabled = true;
                return;
            }

            queueList.innerHTML = data.tasks.map(task => `
                <div class="queue-item ${task.status}">
                    <div class="task-header">
                        <strong>${escapeHtml(task.query)}</strong>
                        ${task.status ? `<span class="status-badge ${task.status}">${formatStatus(task.status)}</span>` : ''}
                    </div>
                    <div class="task-details">
                        <span>Category: ${escapeHtml(task.category)}</span>
                        <span>Priority: ${task.importance}</span>
                    </div>
                    ${task.error ? `<div class="error-message">${escapeHtml(task.error)}</div>` : ''}
                </div>
            `).join('');
            
            processButton.disabled = false;
        } else {
            queueList.innerHTML = '<p>No tasks in queue.</p>';
            processButton.disabled = true;
        }
    } catch (error) {
        console.error('Error updating queue status:', error);
        showNotification(`Error updating queue status: ${error.message}`, 'error');
        queueList.innerHTML = '<p>Failed to load queue status.</p>';
    }
}

// Helper functions
function formatStatus(status) {
    return {
        'pending': '⏳ Pending',
        'processing': '⚙️ Processing',
        'completed': '✅ Complete',
        'failed': '❌ Failed',
        'success': '✅ Success',
        'error': '❌ Error',
        'partial': '⚠️ Partial'
    }[status] || status;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function escapeHtml(unsafe) {
    return (unsafe || '')
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Initial queue status update
updateQueueStatus();

// Auto-refresh queue status every 5 seconds
setInterval(updateQueueStatus, 5000);

// Add styles for status badges
document.head.insertAdjacentHTML('beforeend', `
    <style>
        .status-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 999px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-badge.success { background-color: #10B981; color: white; }
        .status-badge.partial { background-color: #F59E0B; color: white; }
        .status-badge.error { background-color: #EF4444; color: white; }
        .status-badge.processing { background-color: #3B82F6; color: white; }
        
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .task-details {
            display: flex;
            gap: 1rem;
            font-size: 0.875rem;
            color: var(--text-light);
        }
        
        .error-message {
            background-color: rgba(239, 68, 68, 0.1);
            border-left: 3px solid #EF4444;
            padding: 0.75rem;
            margin: 0.5rem 0;
            color: #EF4444;
        }
    </style>
`);
