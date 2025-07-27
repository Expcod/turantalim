// Vanilla JavaScript for Test Admin Panel
(function() {
    'use strict';
    
    // DOM yuklangani ekanligini tekshirish
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }
    
    ready(function() {
        console.log('Test admin JavaScript yuklandi');
        
        // Elementlarni topish
        var examSelect = document.getElementById('id_exam');
        var sectionSelect = document.getElementById('id_section');
        
        if (!examSelect || !sectionSelect) {
            console.log('Kerakli elementlar topilmadi');
            return;
        }
        
        console.log('Elementlar topildi:', examSelect, sectionSelect);
        
        // Exam o'zgartirilganda sectionlarni yangilash
        function updateSections() {
            var examId = examSelect.value;
            console.log('Exam ID:', examId);
            
            if (!examId) {
                sectionSelect.innerHTML = '<option value="">---------</option>';
                sectionSelect.disabled = true;
                return;
            }
            
            // Loading ko'rsatish
            sectionSelect.classList.add('loading');
            sectionSelect.disabled = true;
            
            console.log('AJAX so\'rov yuborilmoqda...');
            
            // CSRF token ni olish
            var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            var csrfValue = csrfToken ? csrfToken.value : '';
            
            // AJAX orqali sectionlarni olish
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/multilevel/admin/sections/get-sections-by-exam/?exam_id=' + examId, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            if (csrfValue) {
                xhr.setRequestHeader('X-CSRFToken', csrfValue);
            }
            
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            console.log('AJAX javob:', data);
                            
                            sectionSelect.innerHTML = '<option value="">---------</option>';
                            
                            if (data.sections && data.sections.length > 0) {
                                data.sections.forEach(function(section) {
                                    var option = document.createElement('option');
                                    option.value = section.id;
                                    option.textContent = section.title;
                                    sectionSelect.appendChild(option);
                                });
                            }
                            
                            sectionSelect.classList.remove('loading');
                            sectionSelect.disabled = false;
                            
                        } catch (e) {
                            console.error('JSON parse xatolik:', e);
                            sectionSelect.classList.remove('loading');
                            sectionSelect.disabled = false;
                        }
                    } else {
                        console.error('AJAX xatolik:', xhr.status, xhr.responseText);
                        sectionSelect.classList.remove('loading');
                        sectionSelect.disabled = false;
                    }
                }
            };
            
            xhr.onerror = function() {
                console.error('Network xatolik');
                sectionSelect.classList.remove('loading');
                sectionSelect.disabled = false;
            };
            
            xhr.send();
        }
        
        // Event listener qo'shish
        examSelect.addEventListener('change', updateSections);
        
        // Sahifa yuklanganda ham sectionlarni yangilash
        if (examSelect.value) {
            updateSections();
        } else {
            // Agar exam tanlanmagan bo'lsa, section ni o'chirish
            sectionSelect.disabled = true;
        }
        
        // Section tanlanganda ma'lumot ko'rsatish
        function showSectionInfo() {
            var sectionId = sectionSelect.value;
            var existingInfo = document.querySelector('.section-info');
            
            if (existingInfo) {
                existingInfo.remove();
            }
            
            if (!sectionId) {
                return;
            }
            
            // CSRF token ni olish
            var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            var csrfValue = csrfToken ? csrfToken.value : '';
            
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/multilevel/admin/sections/get-section-info/?section_id=' + sectionId, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            if (csrfValue) {
                xhr.setRequestHeader('X-CSRFToken', csrfValue);
            }
            
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        var infoHtml = '<div class="section-info">' +
                            '<strong>Bo\'lim ma\'lumotlari:</strong><br>' +
                            'Turi: ' + data.type + '<br>' +
                            'Davomiyligi: ' + data.duration + ' daqiqa<br>' +
                            (data.description ? 'Tavsif: ' + data.description : '') +
                            '</div>';
                        
                        sectionSelect.insertAdjacentHTML('afterend', infoHtml);
                    } catch (e) {
                        console.error('Section info parse xatolik:', e);
                    }
                }
            };
            
            xhr.send();
        }
        
        sectionSelect.addEventListener('change', showSectionInfo);
        
        // Sahifa yuklanganda ham ma'lumot ko'rsatish
        if (sectionSelect.value) {
            showSectionInfo();
        }
    });
    
})(); 