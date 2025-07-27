(function($) {
    'use strict';
    
    // jQuery yuklangani ekanligini tekshirish
    if (typeof $ === 'undefined') {
        console.error('jQuery yuklanmagan!');
        return;
    }
    
    $(document).ready(function() {
        // Test admin paneli uchun JavaScript
        var examSelect = $('#id_exam');
        var sectionSelect = $('#id_section');
        
        // Exam o'zgartirilganda sectionlarni yangilash
        function updateSections() {
            var examId = examSelect.val();
            console.log('Exam ID:', examId); // Debug
            
            if (!examId) {
                sectionSelect.html('<option value="">---------</option>');
                sectionSelect.prop('disabled', true);
                return;
            }
            
            // Loading ko'rsatish
            sectionSelect.addClass('loading');
            sectionSelect.prop('disabled', true);
            
            console.log('AJAX so\'rov yuborilmoqda...'); // Debug
            
            // AJAX orqali sectionlarni olish
            $.ajax({
                url: '/multilevel/admin/sections/get-sections-by-exam/',
                data: {
                    'exam_id': examId
                },
                dataType: 'json',
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(data) {
                    console.log('AJAX javob:', data); // Debug
                    sectionSelect.html('<option value="">---------</option>');
                    $.each(data.sections, function(index, section) {
                        sectionSelect.append(
                            $('<option></option>').val(section.id).text(section.title)
                        );
                    });
                    sectionSelect.removeClass('loading');
                    sectionSelect.prop('disabled', false);
                },
                error: function(xhr, status, error) {
                    console.error('AJAX xatolik:', xhr.responseText); // Debug
                    console.error('Status:', status);
                    console.error('Error:', error);
                    sectionSelect.removeClass('loading');
                    sectionSelect.prop('disabled', false);
                }
            });
        }
        
        // Event listener qo'shish
        if (examSelect.length) {
            examSelect.on('change', updateSections);
            
            // Sahifa yuklanganda ham sectionlarni yangilash
            if (examSelect.val()) {
                updateSections();
            } else {
                // Agar exam tanlanmagan bo'lsa, section ni o'chirish
                sectionSelect.prop('disabled', true);
            }
        }
        
        // Jazzmin admin uchun qo'shimcha stillar
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .form-row .field-exam select,
                .form-row .field-section select {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #fff;
                }
                
                .form-row .field-exam select:focus,
                .form-row .field-section select:focus {
                    border-color: #007bff;
                    outline: none;
                    box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
                }
                
                .form-row .field-exam label,
                .form-row .field-section label {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 5px;
                    display: block;
                }
                
                .loading {
                    opacity: 0.6;
                    pointer-events: none;
                }
                
                .section-info {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 10px;
                    margin-top: 10px;
                    font-size: 14px;
                    color: #6c757d;
                }
            `)
            .appendTo('head');
        
        // Section tanlanganda ma'lumot ko'rsatish
        function showSectionInfo() {
            var sectionId = sectionSelect.val();
            var sectionInfo = $('.section-info');
            
            if (sectionInfo.length) {
                sectionInfo.remove();
            }
            
            if (!sectionId) {
                return;
            }
            
            $.ajax({
                url: '/admin/multilevel/section/get_section_info/',
                data: {
                    'section_id': sectionId
                },
                dataType: 'json',
                success: function(data) {
                    var infoHtml = `
                        <div class="section-info">
                            <strong>Bo'lim ma'lumotlari:</strong><br>
                            Turi: ${data.type}<br>
                            Davomiyligi: ${data.duration} daqiqa<br>
                            ${data.description ? 'Tavsif: ' + data.description : ''}
                        </div>
                    `;
                    sectionSelect.after(infoHtml);
                }
            });
        }
        
        if (sectionSelect.length) {
            sectionSelect.on('change', showSectionInfo);
            
            // Sahifa yuklanganda ham ma'lumot ko'rsatish
            if (sectionSelect.val()) {
                showSectionInfo();
            }
        }
    });
    
})(django.jQuery);