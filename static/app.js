// API base URL
const API_BASE = '';

// Helper function to get auth headers
async function getAuthHeaders() {
    const token = await window.getAuthToken();
    const headers = {
        'Content-Type': 'application/json'
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

// Update stats on page load
document.addEventListener('DOMContentLoaded', () => {
    updateStats();
});

// Update statistics
async function updateStats() {
    try {
        const response = await fetch(`${API_BASE}/api/data/summary`);
        const data = await response.json();
        
        document.getElementById('faculty-count').textContent = data.faculty_count;
        document.getElementById('subjects-count').textContent = data.subjects_count;
        document.getElementById('classrooms-count').textContent = data.classrooms_count;
        document.getElementById('sections-count').textContent = data.sections_count;
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Upload file
async function uploadFile(type) {
    const fileInput = document.getElementById(`${type}-file`);
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus(`Please select a ${type} file`, 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showStatus(`Uploading ${type}...`, 'info');
        
        const token = await window.getAuthToken();
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE}/api/upload/${type}`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showStatus(`✅ ${result.message}`, 'success');
            updateStats();
            fileInput.value = ''; // Clear file input
        } else {
            showStatus(`❌ Error: ${result.detail}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Error uploading ${type}: ${error.message}`, 'error');
    }
}

// Generate timetable
async function generateTimetable() {
    const academicYear = document.getElementById('academic-year').value;
    const semester = parseInt(document.getElementById('semester').value);
    
    if (!academicYear) {
        showStatus('Please enter academic year', 'error');
        return;
    }
    
    try {
        showStatus('🤖 Generating timetable using AI agents...', 'info');
        
        const headers = await getAuthHeaders();
        const response = await fetch(`${API_BASE}/api/generate-timetable`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                academic_year: academicYear,
                semester: semester
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showStatus(`✅ ${result.message}`, 'success');
            displayTimetable(result);
        } else {
            showStatus(`❌ Error: ${result.detail}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Error generating timetable: ${error.message}`, 'error');
    }
}

// Display timetable
function displayTimetable(result) {
    console.log('Displaying timetable v2.0 - Enhanced validation display');
    const resultsSection = document.getElementById('results-section');
    const resultsContainer = document.getElementById('timetable-results');
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Create validation summary
    let html = '<div class="validation-results">';
    html += '<h3>📊 Constraint Validation Report</h3>';
    
    const validation = result.validation || {};
    const totalEntries = validation.total_entries || result.schedule?.length || 0;
    
    if (result.constraints_satisfied) {
        html += '<div style="background: #d4edda; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; margin-bottom: 15px;">';
        html += '<h4 style="color: #155724; margin: 0 0 10px 0;">✅ All Constraints Successfully Satisfied!</h4>';
        html += '<div style="color: #155724;">';
        html += `<p><strong>✓ Faculty Constraints:</strong> No double-booking detected across ${totalEntries} classes</p>`;
        html += `<p><strong>✓ Classroom Constraints:</strong> All rooms properly allocated with no conflicts</p>`;
        html += `<p><strong>✓ Section Constraints:</strong> No overlapping classes for any section</p>`;
        html += `<p><strong>✓ Capacity Constraints:</strong> All classrooms have sufficient capacity</p>`;
        html += `<p><strong>✓ Faculty-Subject Matching:</strong> All faculty assigned to subjects they can teach</p>`;
        html += '</div>';
        html += '</div>';
    } else {
        html += '<div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 15px;">';
        html += '<h4 style="color: #856404; margin: 0 0 10px 0;">⚠️ Constraint Violations Detected</h4>';
        
        if (validation.violations && validation.violations.length > 0) {
            // Group violations by type
            const facultyViolations = validation.violations.filter(v => v.includes('Faculty conflict'));
            const classroomViolations = validation.violations.filter(v => v.includes('Classroom conflict'));
            const capacityViolations = validation.violations.filter(v => v.includes('Capacity violation'));
            const sectionViolations = validation.violations.filter(v => v.includes('Section conflict'));
            
            if (facultyViolations.length > 0) {
                html += `<p style="color: #856404;"><strong>❌ Faculty Conflicts:</strong> ${facultyViolations.length} instances</p>`;
            }
            if (classroomViolations.length > 0) {
                html += `<p style="color: #856404;"><strong>❌ Classroom Conflicts:</strong> ${classroomViolations.length} instances</p>`;
            }
            if (capacityViolations.length > 0) {
                html += `<p style="color: #856404;"><strong>❌ Capacity Issues:</strong> ${capacityViolations.length} instances</p>`;
            }
            if (sectionViolations.length > 0) {
                html += `<p style="color: #856404;"><strong>❌ Section Conflicts:</strong> ${sectionViolations.length} instances</p>`;
            }
            
            html += '<details style="margin-top: 10px;"><summary style="cursor: pointer; color: #856404;">View detailed violations</summary>';
            html += '<ul style="margin-top: 10px;">';
            validation.violations.forEach(v => {
                html += `<li class="violation">${v}</li>`;
            });
            html += '</ul></details>';
        }
        html += '</div>';
    }
    
    // Show warnings if any
    if (validation.warnings && validation.warnings.length > 0) {
        html += '<div style="background: #d1ecf1; padding: 15px; border-radius: 8px; border-left: 4px solid #17a2b8; margin-bottom: 15px;">';
        html += '<h4 style="color: #0c5460; margin: 0 0 10px 0;">💡 Recommendations</h4>';
        validation.warnings.forEach(w => {
            html += `<p style="color: #0c5460;" class="warning">${w}</p>`;
        });
        html += '</div>';
    }
    
    html += '</div>';
    
    // Create schedule table
    html += '<table class="timetable-table">';
    html += '<thead><tr>';
    html += '<th>Day</th><th>Time</th><th>Subject</th><th>Faculty</th><th>Classroom</th><th>Section</th>';
    html += '</tr></thead><tbody>';
    
    const schedule = result.schedule || [];
    
    // Sort by day and time
    const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    schedule.sort((a, b) => {
        const dayDiff = dayOrder.indexOf(a.day) - dayOrder.indexOf(b.day);
        if (dayDiff !== 0) return dayDiff;
        return a.start_time.localeCompare(b.start_time);
    });
    
    schedule.forEach(entry => {
        html += '<tr>';
        html += `<td>${entry.day}</td>`;
        html += `<td>${entry.start_time} - ${entry.end_time}</td>`;
        html += `<td>${entry.subject?.name || entry.subject_id}</td>`;
        html += `<td>${entry.faculty?.name || entry.faculty_id}</td>`;
        html += `<td>${entry.classroom?.name || entry.classroom_id}</td>`;
        html += `<td>${entry.section?.name || entry.section_id}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    // Add export buttons
    html += '<div style="margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap;">';
    html += '<button onclick="exportTimetableCSV()" style="background: #28a745; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 1em; font-weight: 500;">';
    html += '📥 Export as CSV';
    html += '</button>';
    html += '<button onclick="exportTimetableJSON()" style="background: #17a2b8; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 1em; font-weight: 500;">';
    html += '📥 Export as JSON';
    html += '</button>';
    html += '</div>';
    
    resultsContainer.innerHTML = html;
    
    // Store timetable data for export
    storeCurrentTimetable(result);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Show status message
function showStatus(message, type) {
    const statusDiv = document.getElementById('generation-status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    statusDiv.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

// Store last generated timetable for refinement
let lastGeneratedTimetable = null;

// Chat functionality
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    try {
        const headers = await getAuthHeaders();
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                message: message,
                last_timetable: lastGeneratedTimetable  // Send previous timetable for refinement
            })
        });
        
        const result = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();
        
        // Add bot response to chat (with safety check)
        const botResponse = result.response || result.message || 'Sorry, I could not process your request.';
        addChatMessage(botResponse, 'bot');
        
        // If timetable was generated, display it
        if (result.intent && result.intent.timetable_data) {
            // Store for future refinements
            lastGeneratedTimetable = result.intent.timetable_data;
            
            displayChatTimetable(result.intent.timetable_data);
            // Add a helpful message
            addChatMessage('📅 Timetable displayed below! Scroll down to see the full schedule.', 'bot');
        }
        
    } catch (error) {
        typingIndicator.remove();
        addChatMessage(`Error: ${error.message}`, 'bot');
    }
}

// Add typing indicator
function addTypingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing-indicator';
    typingDiv.innerHTML = '<strong>Assistant:</strong> <span class="typing-dots">Thinking<span>.</span><span>.</span><span>.</span></span>';
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return typingDiv;
}

// Handle Enter key in chat input
function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Add message to chat
function addChatMessage(text, sender) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    // Safety check for undefined text
    if (!text) {
        text = 'No response received.';
    }
    
    const label = sender === 'user' ? 'You' : 'Assistant';
    // Use innerText for user messages, innerHTML for bot (to preserve formatting)
    if (sender === 'bot') {
        // Convert markdown-style formatting to HTML
        const formattedText = String(text)
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        messageDiv.innerHTML = `<strong>${label}:</strong> ${formattedText}`;
    } else {
        messageDiv.innerHTML = `<strong>${label}:</strong> ${text}`;
    }
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Display timetable generated from chat
function displayChatTimetable(timetableData) {
    const resultsSection = document.getElementById('results-section');
    const resultsContainer = document.getElementById('timetable-results');
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Create a nice display with header
    let html = '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">';
    html += `<h3 style="margin: 0 0 10px 0; font-size: 1.5em;">📅 ${timetableData.university || 'University'} - Semester ${timetableData.semester || '3'}</h3>`;
    html += '<p style="margin: 0; opacity: 0.9;">✨ Generated via AI Chat Interface</p>';
    html += '</div>';
    
    const schedule = timetableData.schedule || [];
    
    if (schedule.length === 0) {
        html += '<p>No schedule entries found.</p>';
        resultsContainer.innerHTML = html;
        return;
    }
    
    // Sort by day and time
    const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    schedule.sort((a, b) => {
        const dayDiff = dayOrder.indexOf(a.day) - dayOrder.indexOf(b.day);
        if (dayDiff !== 0) return dayDiff;
        return a.start_time.localeCompare(b.start_time);
    });
    
    // Group by day for better visualization
    const scheduleByDay = {};
    schedule.forEach(entry => {
        if (!scheduleByDay[entry.day]) {
            scheduleByDay[entry.day] = [];
        }
        scheduleByDay[entry.day].push(entry);
    });
    
    // Create a week view grid
    html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 30px;">';
    
    dayOrder.forEach(day => {
        if (scheduleByDay[day]) {
            html += `<div style="background: white; border: 2px solid #667eea; border-radius: 8px; padding: 15px;">`;
            html += `<h4 style="color: #667eea; margin: 0 0 15px 0; padding-bottom: 10px; border-bottom: 2px solid #e0e0e0;">${day}</h4>`;
            
            scheduleByDay[day].forEach(entry => {
                html += `<div style="background: #f8f9ff; padding: 10px; margin-bottom: 10px; border-radius: 5px; border-left: 4px solid #667eea;">`;
                html += `<div style="font-weight: bold; color: #333; margin-bottom: 5px;">${entry.subject}</div>`;
                html += `<div style="font-size: 0.9em; color: #666;">`;
                html += `<span style="display: inline-block; margin-right: 10px;">🕐 ${entry.start_time} - ${entry.end_time}</span>`;
                if (entry.class_type) {
                    html += `<span style="background: #667eea; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em;">${entry.class_type}</span>`;
                }
                html += `</div>`;
                html += `</div>`;
            });
            
            html += `</div>`;
        }
    });
    
    html += '</div>';
    
    // Also create traditional table view
    html += '<details style="margin-top: 20px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0;">';
    html += '<summary style="cursor: pointer; font-weight: bold; color: #667eea; padding: 10px;">📋 View as Table</summary>';
    html += '<table class="timetable-table" style="margin-top: 15px;">';
    html += '<thead><tr>';
    html += '<th>Day</th><th>Time</th><th>Subject</th><th>Type</th>';
    html += '</tr></thead><tbody>';
    
    schedule.forEach(entry => {
        html += '<tr>';
        html += `<td><strong>${entry.day}</strong></td>`;
        html += `<td>${entry.start_time} - ${entry.end_time}</td>`;
        html += `<td>${entry.subject}</td>`;
        html += `<td>${entry.class_type || 'Lecture'}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    html += '</details>';
    
    // Add summary stats
    const totalClasses = schedule.length;
    const uniqueSubjects = [...new Set(schedule.map(s => s.subject))].length;
    html += `<div style="margin-top: 20px; padding: 15px; background: #f0f7ff; border-radius: 8px; border-left: 4px solid #667eea;">`;
    html += `<strong>📊 Summary:</strong> ${totalClasses} classes scheduled across ${uniqueSubjects} subjects`;
    html += `</div>`;
    
    // Add export buttons
    html += '<div style="margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap;">';
    html += '<button onclick="exportTimetableCSV()" style="background: #28a745; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 1em; font-weight: 500;">';
    html += '📥 Export as CSV';
    html += '</button>';
    html += '<button onclick="exportTimetableJSON()" style="background: #17a2b8; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 1em; font-weight: 500;">';
    html += '📥 Export as JSON';
    html += '</button>';
    html += '</div>';
    
    resultsContainer.innerHTML = html;
    
    // Store timetable data for export
    storeCurrentTimetable(timetableData);
    
    // Show a floating notification
    showFloatingNotification('✅ Timetable generated! Scroll down to view.');
    
    // Smooth scroll to results with a slight delay for effect
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

// Show floating notification
function showFloatingNotification(message) {
    // Remove existing notification if any
    const existing = document.querySelector('.floating-notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = 'floating-notification';
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: white; font-size: 1.2em; cursor: pointer; margin-left: 10px;">×</button>
    `;
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Make it globally available
window.showFloatingNotification = showFloatingNotification;

// Scroll to top function
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Store the current timetable data globally for export
let currentTimetableData = null;

// Store timetable data
function storeCurrentTimetable(result) {
    currentTimetableData = result;
}

// Export timetable as CSV
function exportTimetableCSV() {
    if (!currentTimetableData || !currentTimetableData.schedule) {
        alert('No timetable data available to export');
        return;
    }
    
    const schedule = currentTimetableData.schedule;
    
    // Create CSV header
    let csv = 'Day,Start Time,End Time,Subject,Subject Code,Faculty,Classroom,Section,Room Type\n';
    
    // Add data rows
    schedule.forEach(entry => {
        const day = entry.day || '';
        const startTime = entry.start_time || '';
        const endTime = entry.end_time || '';
        const subject = entry.subject?.name || entry.subject || '';
        const subjectCode = entry.subject?.code || entry.subject_id || '';
        const faculty = entry.faculty?.name || entry.faculty_id || '';
        const classroom = entry.classroom?.name || entry.classroom_id || '';
        const section = entry.section?.name || entry.section_id || '';
        const roomType = entry.classroom?.room_type || '';
        
        csv += `"${day}","${startTime}","${endTime}","${subject}","${subjectCode}","${faculty}","${classroom}","${section}","${roomType}"\n`;
    });
    
    // Download CSV
    downloadFile(csv, 'timetable.csv', 'text/csv');
    showFloatingNotification('✅ Timetable exported as CSV');
}

// Export timetable as JSON
function exportTimetableJSON() {
    if (!currentTimetableData) {
        alert('No timetable data available to export');
        return;
    }
    
    const json = JSON.stringify(currentTimetableData, null, 2);
    downloadFile(json, 'timetable.json', 'application/json');
    showFloatingNotification('✅ Timetable exported as JSON');
}

// Helper function to download file
function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
