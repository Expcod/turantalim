// Turantalim Admin Dashboard JavaScript

// Global variables
let currentSubmissionId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    if (!apiClient.isAuthenticated() && !isLoginPage()) {
        window.location.href = 'login.html';
        return;
    }
    
    // Setup form handling
    setupFormHandling();
    
    // Setup tab change handlers
    setupTabHandlers();
    
    // Setup audio players
    setupAudioPlayers();
    
    // Setup score calculation
    setupScoreCalculation();
    
    // Load submissions on index page
    if (document.getElementById('submissionsTable')) {
        loadSubmissions();
        
        // Setup filter form submit
        const filterForm = document.getElementById('filterForm');
        if (filterForm) {
            filterForm.addEventListener('submit', function(e) {
                e.preventDefault();
                loadSubmissions();
            });
        }
    }
    
    // Load submission details on submission page
    const urlParams = new URLSearchParams(window.location.search);
    const submissionId = urlParams.get('id');
    if (submissionId && document.getElementById('sectionTabs')) {
        currentSubmissionId = submissionId;
        loadSubmissionDetails(submissionId);
    }
    
    // Setup logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            apiClient.logout();
        });
    }
});

// Check if current page is login page
function isLoginPage() {
    return window.location.pathname.includes('login.html');
}

// Handle login form submission
function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Tekshirilmoqda...';
    submitBtn.disabled = true;
    
    // Call API
    apiClient.login(username, password)
        .then(result => {
            if (result.success) {
                window.location.href = 'index.html';
            } else {
                showNotification('Login xatosi. Iltimos, ma\'lumotlaringizni tekshiring.', 'danger');
                
                // Reset button
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        })
        .catch(error => {
            showNotification('Server xatosi. Iltimos, qayta urinib ko\'ring.', 'danger');
            console.error('Error:', error);
            
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
}

// Load submissions for the dashboard
function loadSubmissions() {
    // Show loading state
    const tableBody = document.querySelector('#submissionsTable tbody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center">
                    <i class="fas fa-spinner fa-spin me-2"></i> Yuklanmoqda...
                </td>
            </tr>
        `;
    }
    
    // Get filter values
    const statusFilter = document.getElementById('status').value;
    const examType = document.getElementById('examType').value;
    const writingSection = document.getElementById('writingSection').checked;
    const speakingSection = document.getElementById('speakingSection').checked;
    const searchQuery = document.getElementById('searchUser').value;
    
    // Build filters object
    const filters = {};
    if (statusFilter) filters.status = statusFilter;
    if (examType) filters.exam_level = examType;
    
    if (writingSection && !speakingSection) {
        filters.section = 'writing';
    } else if (speakingSection && !writingSection) {
        filters.section = 'speaking';
    }
    
    if (searchQuery) filters.search = searchQuery;
    
    // Call API
    apiClient.getSubmissions(filters)
        .then(data => {
            renderSubmissionsTable(data);
        })
        .catch(error => {
            showNotification('Ma\'lumotlarni yuklashda xatolik yuz berdi.', 'danger');
            console.error('Error:', error);
            
            if (tableBody) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center text-danger">
                            Ma\'lumotlarni yuklashda xatolik yuz berdi.
                        </td>
                    </tr>
                `;
            }
        });
}

// Render submissions table
function renderSubmissionsTable(submissions) {
    const tableBody = document.querySelector('#submissionsTable tbody');
    if (!tableBody) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (!submissions || submissions.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center">
                    Ma\'lumotlar topilmadi
                </td>
            </tr>
        `;
        return;
    }
    
    // Add rows for each submission
    submissions.forEach(submission => {
        const user = submission.user;
        const exam = submission.exam;
        
        // Determine status badge class
        let statusClass = 'bg-warning text-dark'; // default for pending
        let statusText = 'Pending';
        
        if (submission.writing_status === 'reviewing' || submission.speaking_status === 'reviewing') {
            statusClass = 'bg-info';
            statusText = 'Reviewing';
        } else if (submission.writing_status === 'checked' && submission.speaking_status === 'checked') {
            statusClass = 'bg-success';
            statusText = 'Checked';
        }
        
        // Create row
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input class="form-check-input" type="checkbox" value="${submission.id}"></td>
            <td><a href="submission.html?id=${submission.id}">${user.first_name} ${user.last_name}</a></td>
            <td><a href="submission.html?id=${submission.id}">${exam.title}</a></td>
            <td>${exam.level}</td>
            <td>${new Date(submission.created_at).toLocaleDateString()}</td>
            <td>${submission.sections.join(', ')}</td>
            <td><span class="badge ${statusClass}">${statusText}</span></td>
            <td>
                <a href="submission.html?id=${submission.id}" class="btn btn-sm btn-primary">
                    <i class="fas fa-external-link-alt"></i> Ochish
                </a>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Load submission details
function loadSubmissionDetails(submissionId) {
    // Show loading state
    document.querySelector('.card-body').innerHTML = `
        <div class="text-center py-5">
            <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
            <p>Ma\'lumotlar yuklanmoqda...</p>
        </div>
    `;
    
    // Call API to get submission details
    apiClient.getSubmission(submissionId)
        .then(data => {
            renderSubmissionDetails(data);
            
            // Also load media files
            return apiClient.getSubmissionMedia(submissionId);
        })
        .then(mediaData => {
            renderSubmissionMedia(mediaData);
        })
        .catch(error => {
            showNotification('Ma\'lumotlarni yuklashda xatolik yuz berdi.', 'danger');
            console.error('Error:', error);
        });
}

// Render submission details
function renderSubmissionDetails(data) {
    // Set user info
    const user = data.user_test.user;
    const userInitials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
    document.querySelector('.avatar').textContent = userInitials;
    document.querySelector('.user-info h5').textContent = `${user.first_name} ${user.last_name}`;
    document.querySelector('.user-info .text-muted').textContent = `${user.username} | ${user.email || 'No email'}`;
    
    // Set exam info
    const exam = data.user_test.exam;
    document.querySelector('.alert-light').innerHTML = `
        <span class="fw-bold">Imtihon:</span> ${exam.title} | 
        <span class="fw-bold">Level:</span> ${exam.level} | 
        <span class="fw-bold">Sana:</span> ${new Date(data.user_test.created_at).toLocaleDateString()}
    `;
    
    // Set listening section data
    if (data.listening_result) {
        const listening = data.listening_result;
        document.getElementById('listening-content').innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Listening bo'limi dastur tomonidan avtomatik tekshirilgan.
            </div>
            <h5>Natija: <span class="badge bg-success">${listening.score} / 100</span></h5>
        `;
    } else {
        document.getElementById('listening-content').innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Listening bo'limi hali topshirilmagan.
            </div>
        `;
    }
    
    // Set reading section data
    if (data.reading_result) {
        const reading = data.reading_result;
        document.getElementById('reading-content').innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Reading bo'limi dastur tomonidan avtomatik tekshirilgan.
            </div>
            <h5>Natija: <span class="badge bg-success">${reading.score} / 100</span></h5>
        `;
    } else {
        document.getElementById('reading-content').innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Reading bo'limi hali topshirilmagan.
            </div>
        `;
    }
    
    // Set writing section data (content will be filled when media loads)
    if (data.writing_result) {
        const writing = data.writing_result;
        let statusClass = writing.manual_review?.status === 'checked' ? 'success' : 'warning';
        let statusText = writing.manual_review?.status === 'checked' ? 'Tekshirilgan' : 'Tekshirish uchun taqdim etilgan';
        
        document.getElementById('writing-content').innerHTML = `
            <div class="alert alert-${statusClass}">
                <i class="fas fa-pencil-alt me-2"></i>
                Writing bo'limi ${statusText}.
                ${writing.manual_review?.status === 'checked' ? `<span class="ms-2 fw-bold">Ball: ${writing.manual_review.total_score}/100</span>` : ''}
            </div>
            <div id="writing-questions-container"></div>
        `;
        
        // If already reviewed, pre-fill the form
        if (writing.manual_review?.status === 'checked') {
            const scores = writing.manual_review.question_scores;
            scores.forEach(score => {
                if (document.querySelector(`input[name="question${score.question_number}_score"]`)) {
                    document.querySelector(`input[name="question${score.question_number}_score"]`).value = score.score;
                    document.querySelector(`textarea[name="question${score.question_number}_comment"]`).value = score.comment || '';
                }
            });
            document.querySelector('input[name="total_score"]').value = writing.manual_review.total_score;
            
            // Add review info to audit log
            if (writing.manual_review.logs && writing.manual_review.logs.length > 0) {
                const auditLog = document.querySelector('.audit-log .list-group-flush');
                if (auditLog) {
                    writing.manual_review.logs.forEach(log => {
                        addAuditLogEntryFromData(auditLog, log);
                    });
                }
            }
        }
    } else {
        document.getElementById('writing-content').innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Writing bo'limi hali topshirilmagan.
            </div>
        `;
    }
    
    // Set speaking section data (content will be filled when media loads)
    if (data.speaking_result) {
        const speaking = data.speaking_result;
        let statusClass = speaking.manual_review?.status === 'checked' ? 'success' : 'warning';
        let statusText = speaking.manual_review?.status === 'checked' ? 'Tekshirilgan' : 'Tekshirish uchun taqdim etilgan';
        
        document.getElementById('speaking-content').innerHTML = `
            <div class="alert alert-${statusClass}">
                <i class="fas fa-microphone me-2"></i>
                Speaking bo'limi ${statusText}.
                ${speaking.manual_review?.status === 'checked' ? `<span class="ms-2 fw-bold">Ball: ${speaking.manual_review.total_score}/100</span>` : ''}
            </div>
            <div id="speaking-questions-container"></div>
        `;
        
        // If already reviewed, pre-fill the form
        if (speaking.manual_review?.status === 'checked') {
            const scores = speaking.manual_review.question_scores;
            scores.forEach(score => {
                if (document.querySelector(`input[name="speaking_question${score.question_number}_score"]`)) {
                    document.querySelector(`input[name="speaking_question${score.question_number}_score"]`).value = score.score;
                    document.querySelector(`textarea[name="speaking_question${score.question_number}_comment"]`).value = score.comment || '';
                }
            });
            document.querySelector('input[name="total_score"]').value = speaking.manual_review.total_score;
            
            // Add review info to audit log
            if (speaking.manual_review.logs && speaking.manual_review.logs.length > 0) {
                const auditLog = document.querySelector('.audit-log .list-group-flush');
                if (auditLog) {
                    speaking.manual_review.logs.forEach(log => {
                        addAuditLogEntryFromData(auditLog, log);
                    });
                }
            }
        }
    } else {
        document.getElementById('speaking-content').innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Speaking bo'limi hali topshirilmagan.
            </div>
        `;
    }
}

// Render media files
function renderSubmissionMedia(media) {
    // Render writing media
    if (media.writing) {
        const writingContainer = document.getElementById('writing-questions-container');
        if (writingContainer) {
            let writingHtml = '';
            
            Object.keys(media.writing).forEach(questionNumber => {
                const questionMedia = media.writing[questionNumber];
                
                writingHtml += `
                    <div class="mb-4">
                        <h5 class="mb-3">Savol ${questionNumber}</h5>
                        <div class="card">
                            <div class="card-header bg-light">
                                <strong>Javoblar:</strong>
                            </div>
                            <div class="card-body">
                                <div class="image-gallery mb-3">
                                    <div class="row">
                `;
                
                // Add images
                questionMedia.forEach(item => {
                    writingHtml += `
                        <div class="col-md-4 mb-3">
                            <a href="${item.file_url}" data-lightbox="question${questionNumber}" data-title="Writing Sample ${questionNumber} (image_id: ${item.id})">
                                <img src="${item.file_url}" class="img-fluid rounded" alt="Writing Sample">
                                <div class="image-id">image_id: ${item.id}</div>
                            </a>
                        </div>
                    `;
                });
                
                writingHtml += `
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            writingContainer.innerHTML = writingHtml;
        }
    }
    
    // Render speaking media
    if (media.speaking) {
        const speakingContainer = document.getElementById('speaking-questions-container');
        if (speakingContainer) {
            let speakingHtml = '';
            
            Object.keys(media.speaking).forEach(questionNumber => {
                const questionMedia = media.speaking[questionNumber];
                
                speakingHtml += `
                    <div class="mb-4">
                        <h5 class="mb-3">Savol ${questionNumber}</h5>
                        <div class="card mb-3">
                            <div class="card-header bg-light">
                                <strong>Audio javoblar:</strong>
                            </div>
                            <div class="card-body">
                `;
                
                // Add audio players
                questionMedia.forEach(item => {
                    speakingHtml += `
                        <div class="audio-player mb-3">
                            <audio controls class="w-100">
                                <source src="${item.file_url}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                            <div class="d-flex justify-content-between align-items-center mt-2">
                                <div class="audio-id">audio_id: ${item.id}</div>
                                <a href="${item.file_url}" download class="btn btn-sm btn-outline-primary">
                                    <i class="fas fa-download me-1"></i> Yuklab olish
                                </a>
                            </div>
                        </div>
                    `;
                });
                
                speakingHtml += `
                            </div>
                        </div>
                    </div>
                `;
            });
            
            speakingContainer.innerHTML = speakingHtml;
            
            // Re-initialize audio players
            setupAudioPlayers();
        }
    }
}

// Setup form validation and submission
function setupFormHandling() {
    const gradingForm = document.getElementById('gradingForm');
    const saveDraftBtn = document.getElementById('saveDraftBtn');
    
    if (gradingForm) {
        gradingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate form
            if (!validateForm()) {
                showNotification('Formani to\'ldiring!', 'danger');
                return;
            }
            
            // Submit data
            submitScores('final');
        });
    }
    
    if (saveDraftBtn) {
        saveDraftBtn.addEventListener('click', function() {
            // Save as draft without full validation
            submitScores('draft');
        });
    }
}

// Validate form inputs
function validateForm() {
    const activeSection = document.querySelector('.tab-pane.active').id;
    let isValid = true;
    let inputs;
    
    if (activeSection === 'writing-content') {
        inputs = [
            document.querySelector('input[name="question1_score"]'),
            document.querySelector('input[name="question2_score"]'),
            document.querySelector('input[name="total_score"]')
        ];
    } else if (activeSection === 'speaking-content') {
        inputs = [
            document.querySelector('input[name="speaking_question1_score"]'),
            document.querySelector('input[name="speaking_question2_score"]'),
            document.querySelector('input[name="total_score"]')
        ];
    }
    
    if (!inputs) return false;
    
    inputs.forEach(input => {
        if (!input || !input.value) {
            if (input) input.classList.add('is-invalid');
            isValid = false;
        } else {
            const score = parseInt(input.value);
            if (isNaN(score) || score < 0 || score > 100) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        }
    });
    
    return isValid;
}

// Submit scores to backend
function submitScores(type) {
    const activeSection = document.querySelector('.tab-pane.active').id;
    const isFinal = type === 'final';
    
    if (!currentSubmissionId) {
        showNotification('Error: No submission ID found.', 'danger');
        return;
    }
    
    // Build data object based on active section
    let formData = {};
    let apiMethod;
    
    if (activeSection === 'writing-content') {
        apiMethod = 'updateWritingScores';
        formData = {
            question_scores: {
                "1": {
                    score: document.querySelector('input[name="question1_score"]').value,
                    comment: document.querySelector('textarea[name="question1_comment"]').value
                },
                "2": {
                    score: document.querySelector('input[name="question2_score"]').value,
                    comment: document.querySelector('textarea[name="question2_comment"]').value
                }
            },
            total_score: document.querySelector('input[name="total_score"]').value,
            notified: document.querySelector('input[name="notify_student"]').checked
        };
    } else if (activeSection === 'speaking-content') {
        apiMethod = 'updateSpeakingScores';
        formData = {
            question_scores: {
                "1": {
                    score: document.querySelector('input[name="speaking_question1_score"]').value,
                    comment: document.querySelector('textarea[name="speaking_question1_comment"]').value
                },
                "2": {
                    score: document.querySelector('input[name="speaking_question2_score"]').value,
                    comment: document.querySelector('textarea[name="speaking_question2_comment"]').value
                }
            },
            total_score: document.querySelector('input[name="total_score"]').value,
            notified: document.querySelector('input[name="notify_student"]').checked
        };
    } else {
        showNotification('Error: Invalid section', 'danger');
        return;
    }
    
    // Show loading state
    const submitBtn = document.querySelector('#submitBtn');
    const saveDraftBtn = document.querySelector('#saveDraftBtn');
    const originalSubmitText = submitBtn.innerHTML;
    const originalDraftText = saveDraftBtn.innerHTML;
    
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Yuborilmoqda...';
    submitBtn.disabled = true;
    saveDraftBtn.disabled = true;
    
    // Call API
    apiClient[apiMethod](currentSubmissionId, formData)
        .then(data => {
            // Show success message
            const message = isFinal ? 
                'Balllar muvaffaqiyatli saqlandi va foydalanuvchiga yuborildi!' : 
                'Qoralama muvaffaqiyatli saqlandi!';
            
            showNotification(message, 'success');
            
            // Add to audit log
            const action = isFinal ? 'Tekshirildi' : 'Qoralama';
            const section = activeSection === 'writing-content' ? 'Writing' : 'Speaking';
            const description = `${section} bo'limi ${isFinal ? 'tekshirildi' : 'qoralama saqlandi'}. Ball: ${formData.total_score}`;
            
            addAuditLogEntry(action, description);
            
            // If final submission, refresh the page after a short delay
            if (isFinal) {
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                // Reset buttons
                submitBtn.innerHTML = originalSubmitText;
                saveDraftBtn.innerHTML = originalDraftText;
                submitBtn.disabled = false;
                saveDraftBtn.disabled = false;
            }
        })
        .catch(error => {
            showNotification('Saqlashda xatolik yuz berdi. Qayta urinib ko\'ring.', 'danger');
            console.error('Error:', error);
            
            // Reset buttons
            submitBtn.innerHTML = originalSubmitText;
            saveDraftBtn.innerHTML = originalDraftText;
            submitBtn.disabled = false;
            saveDraftBtn.disabled = false;
        });
}

// Setup tab change handlers
function setupTabHandlers() {
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    const sectionTitle = document.getElementById('sectionTitle');
    
    if (tabEls && sectionTitle) {
        tabEls.forEach(tab => {
            tab.addEventListener('shown.bs.tab', function(e) {
                const section = e.target.textContent.trim();
                
                // Update section title in scoring panel
                sectionTitle.textContent = `${section} Bo'limi Baholash`;
                
                // Toggle appropriate grading form
                if (section === 'Writing') {
                    document.getElementById('writingGrading').style.display = 'block';
                    document.getElementById('speakingGrading').style.display = 'none';
                } else if (section === 'Speaking') {
                    document.getElementById('writingGrading').style.display = 'none';
                    document.getElementById('speakingGrading').style.display = 'block';
                } else {
                    // Hide scoring panel for automated sections
                    document.getElementById('writingGrading').style.display = 'none';
                    document.getElementById('speakingGrading').style.display = 'none';
                    
                    // Update section title to show read-only
                    sectionTitle.textContent = `${section} Bo'limi (Avtomatik)`;
                }
            });
        });
    }
}

// Setup audio players to ensure only one plays at a time
function setupAudioPlayers() {
    const audioElements = document.querySelectorAll('audio');
    
    audioElements.forEach(audio => {
        audio.addEventListener('play', function() {
            audioElements.forEach(otherAudio => {
                if (otherAudio !== audio && !otherAudio.paused) {
                    otherAudio.pause();
                }
            });
        });
    });
}

// Setup automatic score calculation from individual questions
function setupScoreCalculation() {
    // Writing section score calculation
    const q1Score = document.querySelector('input[name="question1_score"]');
    const q2Score = document.querySelector('input[name="question2_score"]');
    const totalScore = document.querySelector('input[name="total_score"]');
    
    if (q1Score && q2Score && totalScore) {
        [q1Score, q2Score].forEach(input => {
            input.addEventListener('input', calculateTotalScore);
        });
    }
    
    // Speaking section score calculation
    const sq1Score = document.querySelector('input[name="speaking_question1_score"]');
    const sq2Score = document.querySelector('input[name="speaking_question2_score"]');
    
    if (sq1Score && sq2Score) {
        [sq1Score, sq2Score].forEach(input => {
            input.addEventListener('input', calculateTotalScore);
        });
    }
}

// Calculate total score based on individual question scores
function calculateTotalScore() {
    const activeSection = document.querySelector('.tab-pane.active').id;
    const totalScore = document.querySelector('input[name="total_score"]');
    
    if (!totalScore) return;
    
    if (activeSection === 'writing-content') {
        const q1 = document.querySelector('input[name="question1_score"]').value || 0;
        const q2 = document.querySelector('input[name="question2_score"]').value || 0;
        
        if (q1 && q2) {
            const average = (parseInt(q1) + parseInt(q2)) / 2;
            totalScore.value = Math.round(average);
        }
    } else if (activeSection === 'speaking-content') {
        const q1 = document.querySelector('input[name="speaking_question1_score"]').value || 0;
        const q2 = document.querySelector('input[name="speaking_question2_score"]').value || 0;
        
        if (q1 && q2) {
            const average = (parseInt(q1) + parseInt(q2)) / 2;
            totalScore.value = Math.round(average);
        }
    }
}

// Show notification message
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Position it
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 150);
    }, 5000);
}

// Add entry to audit log
function addAuditLogEntry(action, description) {
    const auditLog = document.querySelector('.list-group-flush');
    
    if (auditLog) {
        const now = new Date();
        const timeString = now.toLocaleDateString() + ' ' + 
                           now.getHours().toString().padStart(2, '0') + ':' + 
                           now.getMinutes().toString().padStart(2, '0');
        
        const entry = document.createElement('div');
        entry.className = 'list-group-item';
        entry.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">${timeString}</small>
                <span class="badge bg-${action === 'Tekshirildi' ? 'success' : 'info'}">${action}</span>
            </div>
            <div>${description}</div>
        `;
        
        auditLog.prepend(entry);
    }
}

// Add entry to audit log from data
function addAuditLogEntryFromData(auditLog, log) {
    if (auditLog) {
        const timeString = new Date(log.created_at).toLocaleDateString() + ' ' + 
                           new Date(log.created_at).getHours().toString().padStart(2, '0') + ':' + 
                           new Date(log.created_at).getMinutes().toString().padStart(2, '0');
        
        // Map action to badge
        let actionText = 'Info';
        let badgeClass = 'info';
        
        if (log.action === 'update_total_score') {
            actionText = 'Ball O\'zgartirildi';
            badgeClass = 'primary';
        } else if (log.action === 'create_question_score') {
            actionText = 'Ball Qo\'yildi';
            badgeClass = 'success';
        } else if (log.action === 'update_question_score') {
            actionText = 'Ball Yangilandi';
            badgeClass = 'warning';
        } else if (log.action === 'notify_user') {
            actionText = 'Xabar Yuborildi';
            badgeClass = 'info';
        }
        
        const entry = document.createElement('div');
        entry.className = 'list-group-item';
        entry.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">${timeString}</small>
                <span class="badge bg-${badgeClass}">${actionText}</span>
            </div>
            <div>${log.comment}</div>
        `;
        
        auditLog.prepend(entry);
    }
}