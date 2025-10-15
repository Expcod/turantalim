// Turantalim Admin Dashboard JavaScript

// Global variables
let currentSubmissionId = null;
let currentPage = 1;
let totalPages = 1;
let totalCount = 0;
let pageSize = 10;

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    console.log('API Client authenticated:', apiClient.isAuthenticated());
    console.log('Token:', apiClient.token);
    console.log('Is login page:', isLoginPage());
    
    if (!apiClient.isAuthenticated() && !isLoginPage()) {
        console.log('Not authenticated, redirecting to login');
        // Temporarily disable redirect for testing
        // window.location.href = 'login.html';
        // return;
        console.warn('Authentication disabled for testing - redirecting would happen here');
    }
    
    // Setup form handling
    setupFormHandling();
    
    // Setup tab change handlers
    setupTabHandlers();
    
    // Setup audio players
    setupAudioPlayers();
    
    // Setup score calculation
    setupScoreCalculation();
    
    // If URL has status param, preselect filter
    const urlParams = new URLSearchParams(window.location.search);
    const presetStatus = urlParams.get('status');

    // Load submissions on index page
    if (document.getElementById('submissionsTable')) {
        if (presetStatus && document.getElementById('status')) {
            document.getElementById('status').value = presetStatus;
        }
        loadSubmissions();
        
        // Setup filter form submit
        const filterForm = document.getElementById('filterForm');
        if (filterForm) {
            filterForm.addEventListener('submit', function(e) {
                e.preventDefault();
                currentPage = 1; // Reset to first page when filtering
                loadSubmissions();
            });
        }
        
        // Setup pagination event listeners
        setupPaginationHandlers();
    }
    
    // Load submission details on submission page
    const pageParams = new URLSearchParams(window.location.search);
    const submissionId = pageParams.get('id');
    if (submissionId && (document.getElementById('sectionHeader') || document.querySelector('.user-info'))) {
        console.log('Found submission page elements, loading submission ID:', submissionId);
        currentSubmissionId = submissionId;
        loadSubmissionDetails(submissionId);
    } else if (submissionId) {
        console.log('Submission ID found but page elements not found:', submissionId);
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

// Uzbekistan timezone formatter helpers
function formatTashkentDateTime(dateInput) {
    const dt = typeof dateInput === 'string' || typeof dateInput === 'number' ? new Date(dateInput) : dateInput;
    const formatter = new Intl.DateTimeFormat('uz-UZ', {
        timeZone: 'Asia/Tashkent',
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
    // Intl with uz-UZ returns like "14/10/2025, 07:12:05"; normalize space/comma
    return formatter.format(dt).replace(',', '');
}

function formatTashkentDate(dateInput) {
    const dt = typeof dateInput === 'string' || typeof dateInput === 'number' ? new Date(dateInput) : dateInput;
    return new Intl.DateTimeFormat('uz-UZ', { timeZone: 'Asia/Tashkent' }).format(dt);
}

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
    
    // Call API with pagination
    apiClient.getSubmissions(filters, currentPage, pageSize)
        .then(data => {
            if (!data) {
                // e.g., redirected to login or empty response
                if (tableBody) {
                    tableBody.innerHTML = `
                        <tr>
                            <td colspan="8" class="text-center text-muted">Ma'lumotlar topilmadi</td>
                        </tr>
                    `;
                }
                return;
            }
            // Handle paginated response
            if (Array.isArray(data)) {
                renderSubmissionsTable(data);
                updatePaginationInfo({ count: data.length || 0, num_pages: 1, current_page: 1 });
            } else if (data.results) {
                renderSubmissionsTable(data.results || []);
                updatePaginationInfo(data);
            } else {
                renderSubmissionsTable([]);
                updatePaginationInfo({ count: 0, num_pages: 1, current_page: 1 });
            }
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

    // Safety timeout: if nothing rendered after 6s, show empty state
    setTimeout(() => {
        if (tableBody && tableBody.textContent.includes('Yuklanmoqda')) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted">Ma'lumotlar topilmadi</td>
                </tr>
            `;
        }
    }, 6000);
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
        
        console.log(`Submission ${submission.id} statuses:`, {
            writing_status: submission.writing_status,
            speaking_status: submission.speaking_status,
            sections: submission.sections
        });
        
        // Determine status badge class based on available sections
        let statusClass = 'bg-warning text-dark'; // default for pending
        let statusText = 'Kutilmoqda';
        
        // Get statuses for available sections only
        const availableStatuses = [];
        if (submission.sections.includes('writing') && submission.writing_status) {
            availableStatuses.push(submission.writing_status);
        }
        if (submission.sections.includes('speaking') && submission.speaking_status) {
            availableStatuses.push(submission.speaking_status);
        }
        
        // Check if any section is being reviewed
        if (availableStatuses.includes('reviewing')) {
            statusClass = 'bg-info';
            statusText = 'Ko\'rilmoqda';
        } 
        // Check if all available sections are checked
        else if (availableStatuses.length > 0 && availableStatuses.every(s => s === 'checked')) {
            statusClass = 'bg-success';
            statusText = 'Tekshirilgan';
        }
        
        console.log(`Submission ${submission.id} final status:`, statusText);
        
        // Format date in Asia/Tashkent timezone
        const formattedDate = formatTashkentDateTime(submission.created_at);
        
        // Translate sections to Uzbek
        const translatedSections = submission.sections.map(section => {
            switch(section) {
                case 'writing': return 'Yozish';
                case 'speaking': return 'Gapirish';
                case 'listening': return 'Tinglash';
                case 'reading': return 'O\'qish';
                default: return section;
            }
        });
        
        // Create row
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input class="form-check-input" type="checkbox" value="${submission.id}"></td>
            <td>${submission.id}</td>
            <td><a href="submission.html?id=${submission.id}">${user.first_name} ${user.last_name}</a></td>
            <td><a href="submission.html?id=${submission.id}">${exam.title}</a></td>
            <td>${exam.level}</td>
            <td>${formattedDate}</td>
            <td>${translatedSections.join(', ')}</td>
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

// Update pagination information
function updatePaginationInfo(data) {
    totalCount = data.count ?? 0;
    totalPages = data.num_pages || Math.max(1, Math.ceil((totalCount || 0) / pageSize));
    // Do NOT blindly trust backend page number; keep the one user selected unless backend provides a valid value
    const serverPage = data.current_page || data.page;
    if (Number.isFinite(serverPage) && serverPage > 0) {
        currentPage = serverPage;
    }
    
    // Update pagination info text
    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, totalCount);
    const paginationInfo = document.getElementById('pagination-info');
    
    if (paginationInfo) {
        paginationInfo.textContent = `${startItem}-${endItem} of ${totalCount}`;
    }
    
    // Update pagination buttons
    updatePaginationButtons();
}

// Setup pagination button handlers
function setupPaginationHandlers() {
    const paginationContainer = document.querySelector('.pagination');
    if (!paginationContainer) return;
    
    // Previous button
    const prevBtn = paginationContainer.querySelector('.page-item:first-child .page-link');
    if (prevBtn) {
        prevBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                loadSubmissions();
            }
        });
    }
    
    // Next button
    const nextBtn = paginationContainer.querySelector('.page-item:last-child .page-link');
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                currentPage++;
                loadSubmissions();
            }
        });
    }
}

// Update pagination buttons state
function updatePaginationButtons() {
    const paginationContainer = document.querySelector('.pagination');
    if (!paginationContainer) return;
    
    // Clear existing page number buttons
    const existingPages = paginationContainer.querySelectorAll('.page-item:not(:first-child):not(:last-child)');
    existingPages.forEach(page => page.remove());
    
    // Update previous button
    const prevBtn = paginationContainer.querySelector('.page-item:first-child');
    if (prevBtn) {
        prevBtn.classList.toggle('disabled', currentPage <= 1);
    }
    
    // Update next button
    const nextBtn = paginationContainer.querySelector('.page-item:last-child');
    if (nextBtn) {
        nextBtn.classList.toggle('disabled', currentPage >= totalPages);
    }
    
    // Add page number buttons
    const prevPage = paginationContainer.querySelector('.page-item:first-child');
    const nextPage = paginationContainer.querySelector('.page-item:last-child');
    
    // Calculate which page numbers to show
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    // Adjust range to always show 5 pages if possible
    if (endPage - startPage < 4) {
        if (startPage === 1) {
            endPage = Math.min(totalPages, startPage + 4);
        } else {
            startPage = Math.max(1, endPage - 4);
        }
    }
    
    // Create page number buttons
    for (let i = startPage; i <= endPage; i++) {
        const pageItem = document.createElement('li');
        pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
        
        const pageLink = document.createElement('a');
        pageLink.className = 'page-link';
        pageLink.href = '#';
        pageLink.textContent = i;
        
        pageLink.addEventListener('click', function(e) {
            e.preventDefault();
            if (i !== currentPage) {
                currentPage = i;
                loadSubmissions();
            }
        });
        
        pageItem.appendChild(pageLink);
        
        // Insert before next button
        paginationContainer.insertBefore(pageItem, nextPage);
    }
}

// Load submission details
function loadSubmissionDetails(submissionId) {
    console.log('Loading submission details for ID:', submissionId);
    
    // Show loading state for user info
    const avatarElement = document.querySelector('.card-body .avatar');
    const userNameElement = document.querySelector('.card-body .user-info h5');
    const userDetailsElement = document.querySelector('.card-body .user-info .text-muted');
    const examInfoElement = document.querySelector('.card-body .alert-light');
    const sectionHeaderElement = document.getElementById('sectionHeader');
    
    console.log('Found elements:', {
        avatar: !!avatarElement,
        userName: !!userNameElement,
        userDetails: !!userDetailsElement,
        examInfo: !!examInfoElement,
        sectionHeader: !!sectionHeaderElement
    });
    
    if (avatarElement) avatarElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    if (userNameElement) userNameElement.textContent = 'Yuklanmoqda...';
    if (userDetailsElement) userDetailsElement.textContent = 'Yuklanmoqda...';
    if (examInfoElement) {
        examInfoElement.innerHTML = `
            <span class="fw-bold">Imtihon:</span> Yuklanmoqda... | 
            <span class="fw-bold">Level:</span> Yuklanmoqda... | 
            <span class="fw-bold">Sana:</span> Yuklanmoqda...
        `;
    }
    if (sectionHeaderElement) {
        sectionHeaderElement.innerHTML = `
            <i class="fas fa-spinner fa-spin me-2"></i> Yuklanmoqda...
        `;
    }
    
    // Call API to get submission details
    apiClient.getSubmission(submissionId)
        .then(data => {
            console.log('Successfully loaded submission data:', data);
            renderSubmissionDetails(data);
            
            // Also load media files
            return apiClient.getSubmissionMedia(submissionId);
        })
        .then(mediaData => {
            console.log('Successfully loaded media data:', mediaData);
            renderSubmissionMedia(mediaData);
        })
        .catch(error => {
            console.error('Error loading submission details:', error);
            
            // Check if it's a limit_reached error
            if (error.code === 'limit_reached') {
                showNotification(error.message, 'warning');
                
                // Redirect back to dashboard after showing message
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 5000);
                
                return; // Don't show test data
            }
            
            showNotification('Ma\'lumotlarni yuklashda xatolik yuz berdi. Test ma\'lumotlari bilan ishlaydi.', 'warning');
            
            // Use test data for debugging
            const testData = {
                user_test: {
                    user: {
                        first_name: 'Test',
                        last_name: 'User',
                        username: 'testuser',
                        email: 'test@example.com'
                    },
                    exam: {
                        title: 'CEFR 1. Sinav',
                        level: 'A1'
                    },
                    created_at: new Date().toISOString()
                },
                writing_result: {
                    manual_review: {
                        status: 'pending',
                        total_score: null,
                        question_scores: [],
                        logs: []
                    }
                }
            };
            
            console.log('Using test data:', testData);
            renderSubmissionDetails(testData);
            
            // Also render test media data
            const testMediaData = {
                writing: {
                    "1": [
                        {
                            id: 1,
                            file_url: 'https://via.placeholder.com/300x200?text=Test+Image+1',
                            file_type: 'image'
                        }
                    ],
                    "2": [
                        {
                            id: 2,
                            file_url: 'https://via.placeholder.com/300x200?text=Test+Image+2',
                            file_type: 'image'
                        }
                    ]
                }
            };
            
            renderSubmissionMedia(testMediaData);
        });
}

// Global variable to track current section type
let currentSectionType = null;

// Render submission details
function renderSubmissionDetails(data) {
    try {
        console.log('Rendering submission details with data:', data);
        
        // Set user info
        const user = data.user_test.user;
        const userInitials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
        
        // Update avatar
        const avatarElement = document.querySelector('.card-body .avatar') || document.querySelector('.avatar');
        if (avatarElement) {
            avatarElement.textContent = userInitials;
            console.log('Updated avatar with initials:', userInitials);
        } else {
            console.error('Avatar element not found with any selector');
        }
        
        // Update user name
        const userNameElement = document.querySelector('.card-body .user-info h5') || document.querySelector('.user-info h5');
        if (userNameElement) {
            userNameElement.textContent = `${user.first_name} ${user.last_name}`;
            console.log('Updated user name:', `${user.first_name} ${user.last_name}`);
        } else {
            console.error('User name element not found with any selector');
        }
        
        // Update user details
        const userDetailsElement = document.querySelector('.card-body .user-info .text-muted') || document.querySelector('.user-info .text-muted');
        if (userDetailsElement) {
            userDetailsElement.textContent = `${user.username} | ${user.email || 'Email ko\'rsatilmagan'}`;
            console.log('Updated user details');
        } else {
            console.error('User details element not found with any selector');
        }
        
        // Set exam info
        const exam = data.user_test.exam;
        const examInfoElement = document.querySelector('.card-body .alert-light') || document.querySelector('.alert-light');
        if (examInfoElement) {
            examInfoElement.innerHTML = `
                <span class="fw-bold">Imtihon:</span> ${exam.title} | 
                <span class="fw-bold">Level:</span> ${exam.level} | 
                <span class="fw-bold">Sana:</span> ${formatTashkentDate(data.user_test.created_at)}
            `;
            console.log('Updated exam info');
        } else {
            console.error('Exam info element not found with any selector');
        }
        
    // Determine section type from backend
    console.log('Backend section_type:', data.section_type);
    console.log('Available data sections:', {
        section_type: data.section_type,
        writing_result: !!data.writing_result,
        speaking_result: !!data.speaking_result,
        full_data: data
    });
    
    // Use section_type from backend - this is 100% accurate from database
    if (data.section_type === 'writing') {
        currentSectionType = 'writing';
        console.log('Setting currentSectionType to WRITING (from backend)');
        
        // Get writing result data
        const writingData = data.writing_result || {};
        showWritingSection(writingData);
    } else if (data.section_type === 'speaking') {
        currentSectionType = 'speaking';
        console.log('Setting currentSectionType to SPEAKING (from backend)');
        
        // Get speaking result data
        const speakingData = data.speaking_result || {};
        showSpeakingSection(speakingData);
    } else if (data.section_type === 'listening' || data.section_type === 'reading') {
        // These sections don't need manual review
        console.log('Section type is', data.section_type, '- no manual review needed');
        currentSectionType = null;
        
        const sectionHeaderElement = document.getElementById('sectionHeader');
        const sectionTitleElement = document.getElementById('sectionTitle');
        
        if (sectionHeaderElement) {
            sectionHeaderElement.innerHTML = `
                <i class="fas fa-info-circle me-2"></i> Bu bo'lim qo'lda baholanmaydi
            `;
        }
        
        if (sectionTitleElement) {
            sectionTitleElement.textContent = data.section_type;
        }
    } else {
        console.log('No valid section type found');
        currentSectionType = null;
        
        // No section available
        const sectionHeaderElement = document.getElementById('sectionHeader');
        const sectionTitleElement = document.getElementById('sectionTitle');
        
        if (sectionHeaderElement) {
            sectionHeaderElement.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i> Ma'lumot topilmadi
            `;
        }
        
        if (sectionTitleElement) {
            sectionTitleElement.textContent = 'Ma\'lumot yo\'q';
        }
    }
        
} catch (error) {
        console.error('Error rendering submission details:', error);
        showNotification('Ma\'lumotlarni ko\'rsatishda xatolik yuz berdi.', 'danger');
    }
}

// Show writing section
function showWritingSection(writingResult) {
    const statusClass = writingResult.manual_review?.status === 'checked' ? 'success' : 'warning';
    const statusText = writingResult.manual_review?.status === 'checked' ? 'Tekshirilgan' : 'Tekshirish uchun taqdim etilgan';
    
    // Update headers
    document.getElementById('sectionHeader').innerHTML = `
        <i class="fas fa-pencil-alt me-2"></i> Yozish Bo'limi
    `;
    document.getElementById('sectionTitle').textContent = 'Yozish Bo\'limi Baholash';
    
    // Show writing content
    document.getElementById('writing-content').style.display = 'block';
    document.getElementById('speaking-content').style.display = 'none';
    document.getElementById('writing-content').innerHTML = `
        <div class="alert alert-${statusClass} mb-4">
            <i class="fas fa-pencil-alt me-2"></i>
            Yozish bo'limi ${statusText}.
            ${writingResult.manual_review?.status === 'checked' ? `<span class="ms-2 fw-bold">Ball: ${writingResult.manual_review.total_score}/100</span>` : ''}
        </div>
        <div id="writing-questions-container"></div>
    `;
    
    // Show writing grading form and disable speaking form inputs
    const writingGrading = document.getElementById('writingGrading');
    const speakingGrading = document.getElementById('speakingGrading');
    
    writingGrading.style.display = 'block';
    speakingGrading.style.display = 'none';
    
    // Enable writing inputs, disable speaking inputs
    writingGrading.querySelectorAll('input, textarea').forEach(el => {
        if (!el.name.includes('total_score')) {
            el.disabled = false;
        }
    });
    speakingGrading.querySelectorAll('input, textarea').forEach(el => {
        if (!el.name.includes('total_score')) {
            el.disabled = true;
        }
    });
    
    // Setup auto-calculation for writing total score
    const q1Input = document.querySelector('input[name="question1_score"]');
    const q2Input = document.querySelector('input[name="question2_score"]');
    const totalInput = document.getElementById('totalScoreInput');
    
    function calculateWritingTotal() {
        const q1 = parseFloat(q1Input.value) || 0;
        const q2 = parseFloat(q2Input.value) || 0;
        const total = q1 + q2;
        totalInput.value = total.toFixed(2);
    }
    
    if (q1Input && q2Input && totalInput) {
        q1Input.addEventListener('input', calculateWritingTotal);
        q2Input.addEventListener('input', calculateWritingTotal);
    }
    
    // Audit log UI removed
    
    // Pre-fill form if already reviewed
    if (writingResult.manual_review?.status === 'checked') {
        prefillWritingForm(writingResult.manual_review);
    }
}

// Show speaking section
function showSpeakingSection(speakingResult) {
    const statusClass = speakingResult.manual_review?.status === 'checked' ? 'success' : 'warning';
    const statusText = speakingResult.manual_review?.status === 'checked' ? 'Tekshirilgan' : 'Tekshirish uchun taqdim etilgan';
    
    // Update headers
    document.getElementById('sectionHeader').innerHTML = `
        <i class="fas fa-microphone me-2"></i> Gapirish Bo'limi
    `;
    document.getElementById('sectionTitle').textContent = 'Gapirish Bo\'limi Baholash';
    
    // Show speaking content
    document.getElementById('writing-content').style.display = 'none';
    document.getElementById('speaking-content').style.display = 'block';
    document.getElementById('speaking-content').innerHTML = `
        <div class="alert alert-${statusClass} mb-4">
            <i class="fas fa-microphone me-2"></i>
            Gapirish bo'limi ${statusText}.
            ${speakingResult.manual_review?.status === 'checked' ? `<span class="ms-2 fw-bold">Ball: ${speakingResult.manual_review.total_score}/100</span>` : ''}
        </div>
        <div id="speaking-questions-container"></div>
    `;
    
    // Show speaking grading form and disable writing form inputs
    const writingGrading = document.getElementById('writingGrading');
    const speakingGrading = document.getElementById('speakingGrading');
    
    writingGrading.style.display = 'none';
    speakingGrading.style.display = 'block';
    
    // Disable writing inputs, enable speaking inputs
    writingGrading.querySelectorAll('input, textarea').forEach(el => {
        if (!el.name.includes('total_score')) {
            el.disabled = true;
        }
    });
    speakingGrading.querySelectorAll('input, textarea').forEach(el => {
        if (!el.name.includes('total_score')) {
            el.disabled = false;
        }
    });
    
    // Setup auto-update for speaking total score (speaking has only 1 score)
    const speakingInput = document.querySelector('input[name="speaking_question1_score"]');
    const totalInput = document.getElementById('totalScoreInput');
    
    function updateSpeakingTotal() {
        const speakingScore = parseFloat(speakingInput.value) || 0;
        totalInput.value = speakingScore.toFixed(2);
    }
    
    if (speakingInput && totalInput) {
        speakingInput.addEventListener('input', updateSpeakingTotal);
    }
    
    // Audit log UI removed
    
    // Pre-fill form if already reviewed
    if (speakingResult.manual_review?.status === 'checked') {
        prefillSpeakingForm(speakingResult.manual_review);
    }
}

// Setup audit log
// Audit log UI removed

// Pre-fill writing form
function prefillWritingForm(manualReview) {
    if (manualReview.question_scores) {
        manualReview.question_scores.forEach(score => {
            const scoreInput = document.querySelector(`input[name="question${score.question_number}_score"]`);
            const commentInput = document.querySelector(`textarea[name="question${score.question_number}_comment"]`);
            
            if (scoreInput) scoreInput.value = score.score;
            if (commentInput) commentInput.value = score.comment || '';
        });
    }
    
    const totalScoreInput = document.querySelector('input[name="total_score"]');
    if (totalScoreInput) totalScoreInput.value = manualReview.total_score;
}

// Pre-fill speaking form
function prefillSpeakingForm(manualReview) {
    if (manualReview.question_scores) {
        manualReview.question_scores.forEach(score => {
            const scoreInput = document.querySelector(`input[name="speaking_question${score.question_number}_score"]`);
            const commentInput = document.querySelector(`textarea[name="speaking_question${score.question_number}_comment"]`);
            
            if (scoreInput) scoreInput.value = score.score;
            if (commentInput) commentInput.value = score.comment || '';
        });
    }
    
    const totalScoreInput = document.querySelector('input[name="total_score"]');
    if (totalScoreInput) totalScoreInput.value = manualReview.total_score;
}

// Render media files
function renderSubmissionMedia(media) {
    // Render writing media
    if (media.writing && currentSectionType === 'writing') {
        const writingContainer = document.getElementById('writing-questions-container');
        if (writingContainer) {
            let writingHtml = '';
            
            Object.keys(media.writing).forEach((questionNumber, idx) => {
                const questionMedia = media.writing[questionNumber];
                const displayNumber = idx + 1; // Always show sequential numbers
                
                writingHtml += `
                    <div class="mb-4">
                        <h5 class="mb-3">Savol ${displayNumber}</h5>
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
                            <a href="${item.file_url}" data-lightbox="question${displayNumber}" data-title="Yozish namunasi ${displayNumber}">
                                <img src="${item.file_url}" class="img-fluid rounded" alt="Yozish namunasi" style="cursor: pointer; border: 2px solid #dee2e6;">
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
    if (media.speaking && currentSectionType === 'speaking') {
        const speakingContainer = document.getElementById('speaking-questions-container');
        if (speakingContainer) {
            let speakingHtml = '';
            
            Object.keys(media.speaking).forEach((questionNumber, idx) => {
                const questionMedia = media.speaking[questionNumber];
                const displayNumber = idx + 1; // Always show sequential numbers
                
                speakingHtml += `
                    <div class="mb-4">
                        <h5 class="mb-3">Savol ${displayNumber}</h5>
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
    const saveDraftBtn = null; // removed
    
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
    
    // Draft feature removed
}

// Validate form inputs
function validateForm() {
    let isValid = true;
    let inputs = [];
    
    if (currentSectionType === 'writing') {
        inputs = [
            document.querySelector('input[name="question1_score"]'),
            document.querySelector('input[name="question2_score"]'),
            document.querySelector('input[name="total_score"]')
        ];
    } else if (currentSectionType === 'speaking') {
        // Speaking has only 1 question
        inputs = [
            document.querySelector('input[name="speaking_question1_score"]'),
            document.querySelector('input[name="total_score"]')
        ];
    }
    
    inputs.forEach(input => {
        if (!input || !input.value) {
            if (input) input.classList.add('is-invalid');
            isValid = false;
        } else {
            const score = parseFloat(input.value);
            if (isNaN(score) || score < 0 || score > 75) {
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
    const isFinal = type === 'final';
    
    console.log('submitScores called with:', {
        type: type,
        isFinal: isFinal,
        currentSectionType: currentSectionType,
        currentSubmissionId: currentSubmissionId
    });
    
    if (!currentSubmissionId) {
        showNotification('Error: No submission ID found.', 'danger');
        return;
    }
    
    // Build data object based on current section type
    let apiMethod;
    let formData = {};
    
    if (currentSectionType === 'writing') {
        apiMethod = 'updateWritingScores';
        
        console.log('Looking for WRITING form elements...');
        const q1ScoreEl = document.querySelector('input[name="question1_score"]');
        const q1CommentEl = document.querySelector('textarea[name="question1_comment"]');
        const q2ScoreEl = document.querySelector('input[name="question2_score"]');
        const q2CommentEl = document.querySelector('textarea[name="question2_comment"]');
        const totalScoreEl = document.querySelector('input[name="total_score"]');
            const notifyEl = null; // removed
        
        console.log('Writing form elements found:', {
            q1ScoreEl: !!q1ScoreEl,
            q1CommentEl: !!q1CommentEl,
            q2ScoreEl: !!q2ScoreEl,
            q2CommentEl: !!q2CommentEl,
            totalScoreEl: !!totalScoreEl,
            notifyEl: !!notifyEl
        });
        
        // Validate elements exist
        if (!q1ScoreEl || !q2ScoreEl || !totalScoreEl) {
            console.error('Missing writing form elements:', {
                q1ScoreEl: !!q1ScoreEl,
                q2ScoreEl: !!q2ScoreEl,
                totalScoreEl: !!totalScoreEl
            });
            showNotification('Yozish form elementlari topilmadi. Sahifani yangilang.', 'danger');
            return;
        }
        
        formData = {
            question_scores: {
                "1": {
                    score: q1ScoreEl.value.toString(),
                    comment: q1CommentEl ? q1CommentEl.value.toString() : ''
                },
                "2": {
                    score: q2ScoreEl.value.toString(),
                    comment: q2CommentEl ? q2CommentEl.value.toString() : ''
                }
            },
            total_score: parseFloat(totalScoreEl.value),
            notified: true,
            is_draft: !isFinal  // if not final, it's a draft
        };
    } else if (currentSectionType === 'speaking') {
        apiMethod = 'updateSpeakingScores';
        
        console.log('Looking for SPEAKING form elements...');
        const sq1ScoreEl = document.querySelector('input[name="speaking_question1_score"]');
        const sq1CommentEl = document.querySelector('textarea[name="speaking_question1_comment"]');
        const totalScoreEl = document.querySelector('input[name="total_score"]');
        const notifyEl = null; // removed
        
        console.log('Speaking form elements found:', {
            sq1ScoreEl: !!sq1ScoreEl,
            sq1CommentEl: !!sq1CommentEl,
            totalScoreEl: !!totalScoreEl,
            notifyEl: !!notifyEl
        });
        
        // Validate elements exist (speaking has only 1 question)
        if (!sq1ScoreEl || !totalScoreEl) {
            console.error('Missing speaking form elements:', {
                sq1ScoreEl: !!sq1ScoreEl,
                totalScoreEl: !!totalScoreEl
            });
            showNotification('Gapirish form elementlari topilmadi. Sahifani yangilang.', 'danger');
            return;
        }
        
        // Speaking has only 1 question
        formData = {
            question_scores: {
                "1": {
                    score: sq1ScoreEl.value.toString(),
                    comment: sq1CommentEl ? sq1CommentEl.value.toString() : ''
                }
            },
            total_score: parseFloat(totalScoreEl.value),
            notified: true,
            is_draft: !isFinal  // if not final, it's a draft
        };
    } else {
        showNotification('Error: Section type not detected', 'danger');
        return;
    }
    
    // Show loading state
    const submitBtn = document.querySelector('#submitBtn');
    const saveDraftBtn = null; // removed
    const originalSubmitText = submitBtn.innerHTML;
    
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Yuborilmoqda...';
    submitBtn.disabled = true;
    // draft button removed
    
    console.log('Submitting data:', {
        submissionId: currentSubmissionId,
        formData: formData,
        isFinal: isFinal,
        apiMethod: apiMethod
    });
    
    // Call API
    apiClient[apiMethod](currentSubmissionId, formData)
        .then(data => {
            console.log('API response:', data);
            
            // Show success message
            const message = isFinal ? 
                'Baholash muvaffaqiyatli yakunlandi va foydalanuvchiga xabar yuborildi!' : 
                'Qoralama muvaffaqiyatli saqlandi!';
            
            showNotification(message, 'success');
            
            // Audit log removed
            
            // If final submission, redirect to dashboard after a short delay
            if (isFinal) {
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 2000);
            }
        })
        .catch(error => {
            console.error('API Error:', error);
            
            let errorMessage = 'Saqlashda xatolik yuz berdi.';
            if (error.message) {
                errorMessage += ` Xatolik: ${error.message}`;
            }
            
            showNotification(errorMessage, 'danger');
            
            // Reset button
            submitBtn.innerHTML = originalSubmitText;
            submitBtn.disabled = false;
        });
}

// Setup tab change handlers (not needed for writing-only page)
function setupTabHandlers() {
    // Not needed anymore - page shows only Writing section
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
    // Setup score calculation for both sections
    setTimeout(() => {
        // Writing section score calculation
        const wq1Score = document.querySelector('input[name="question1_score"]');
        const wq2Score = document.querySelector('input[name="question2_score"]');
        
        if (wq1Score && wq2Score) {
            [wq1Score, wq2Score].forEach(input => {
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
    }, 100);
}

// Calculate total score based on individual question scores
function calculateTotalScore() {
    const totalScore = document.querySelector('input[name="total_score"]');
    
    if (!totalScore) return;
    
    let q1, q2;
    
    if (currentSectionType === 'writing') {
        q1 = document.querySelector('input[name="question1_score"]')?.value || 0;
        q2 = document.querySelector('input[name="question2_score"]')?.value || 0;
    } else if (currentSectionType === 'speaking') {
        q1 = document.querySelector('input[name="speaking_question1_score"]')?.value || 0;
        q2 = document.querySelector('input[name="speaking_question2_score"]')?.value || 0;
    }
    
    if (q1 && q2) {
        const average = (parseInt(q1) + parseInt(q2)) / 2;
        totalScore.value = Math.round(average);
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

// Audit log helpers removed