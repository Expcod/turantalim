(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Savol admin paneli uchun JavaScript
        var sectionSelect = $('#id_section');
        var testSelect = $('#id_test');
        var hasOptionsCheckbox = $('#id_has_options');
        var answerField = $('#id_answer');
        var optionsContainer = $('.inline-group');
        
        // Section o'zgartirilganda testlarni yangilash
        function updateTests() {
            var sectionId = sectionSelect.val();
            
            if (!sectionId) {
                testSelect.html('<option value="">---------</option>');
                return;
            }
            
            // Loading ko'rsatish
            testSelect.addClass('loading');
            
            // AJAX orqali testlarni olish
            $.ajax({
                url: '/admin/multilevel/test/get_tests_by_section/',
                data: {
                    'section_id': sectionId
                },
                dataType: 'json',
                success: function(data) {
                    testSelect.html('<option value="">---------</option>');
                    $.each(data.tests, function(index, test) {
                        testSelect.append(
                            $('<option></option>').val(test.id).text(test.title)
                        );
                    });
                    testSelect.removeClass('loading');
                },
                error: function() {
                    console.error('Testlarni olishda xatolik yuz berdi');
                    testSelect.removeClass('loading');
                }
            });
        }
        
        // Event listener qo'shish
        if (sectionSelect.length) {
            sectionSelect.on('change', updateTests);
            
            // Sahifa yuklanganda ham testlarni yangilash
            if (sectionSelect.val()) {
                updateTests();
            }
        }
        
        // Variantlar checkbox o'zgartirilganda
        function toggleAnswerField() {
            var hasOptions = hasOptionsCheckbox.is(':checked');
            
            if (hasOptions) {
                answerField.closest('.form-row').hide();
                optionsContainer.show();
            } else {
                answerField.closest('.form-row').show();
                optionsContainer.hide();
            }
        }
        
        if (hasOptionsCheckbox.length) {
            hasOptionsCheckbox.on('change', toggleAnswerField);
            
            // Sahifa yuklanganda ham holatni ko'rsatish
            toggleAnswerField();
        }
        
        // Test tanlanganda ma'lumot ko'rsatish
        function showTestInfo() {
            var testId = testSelect.val();
            var testInfo = $('.test-info');
            
            if (testInfo.length) {
                testInfo.remove();
            }
            
            if (!testId) {
                return;
            }
            
            $.ajax({
                url: '/admin/multilevel/test/get_test_info/',
                data: {
                    'test_id': testId
                },
                dataType: 'json',
                success: function(data) {
                    var infoHtml = `
                        <div class="test-info">
                            <strong>Test ma'lumotlari:</strong><br>
                            Bo'lim: ${data.section_title}<br>
                            Turi: ${data.section_type}<br>
                            ${data.description ? 'Tavsif: ' + data.description : ''}
                        </div>
                    `;
                    testSelect.after(infoHtml);
                }
            });
        }
        
        if (testSelect.length) {
            testSelect.on('change', showTestInfo);
            
            // Sahifa yuklanganda ham ma'lumot ko'rsatish
            if (testSelect.val()) {
                showTestInfo();
            }
        }
        
        // Variantlarni dinamik qo'shish/o'chirish
        function setupOptionControls() {
            var addButton = $('<button type="button" class="add-option-btn">+ Variant qo\'shish</button>');
            var removeButton = $('<button type="button" class="remove-option-btn">- Variant o\'chirish</button>');
            
            addButton.on('click', function() {
                var totalForms = parseInt($('#id_option_set-TOTAL_FORMS').val());
                var formNum = totalForms;
                
                // Yangi form yaratish
                var newForm = $('.option-formset').first().clone();
                newForm.find('input, textarea').each(function() {
                    var name = $(this).attr('name');
                    if (name) {
                        $(this).attr('name', name.replace(/\d+/, formNum));
                        $(this).attr('id', $(this).attr('id').replace(/\d+/, formNum));
                    }
                });
                
                // Qiymatlarni tozalash
                newForm.find('input[type="text"], textarea').val('');
                newForm.find('input[type="checkbox"]').prop('checked', false);
                
                $('.option-formset').last().after(newForm);
                $('#id_option_set-TOTAL_FORMS').val(totalForms + 1);
            });
            
            removeButton.on('click', function() {
                var totalForms = parseInt($('#id_option_set-TOTAL_FORMS').val());
                if (totalForms > 2) {
                    $('.option-formset').last().remove();
                    $('#id_option_set-TOTAL_FORMS').val(totalForms - 1);
                }
            });
            
            if (optionsContainer.length) {
                optionsContainer.before(addButton).after(removeButton);
            }
        }
        
        setupOptionControls();
        
        // Jazzmin admin uchun qo'shimcha stillar
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .form-row .field-section select,
                .form-row .field-test select {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #fff;
                }
                
                .form-row .field-section select:focus,
                .form-row .field-test select:focus {
                    border-color: #007bff;
                    outline: none;
                    box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
                }
                
                .form-row .field-section label,
                .form-row .field-test label {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 5px;
                    display: block;
                }
                
                .loading {
                    opacity: 0.6;
                    pointer-events: none;
                }
                
                .test-info {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 10px;
                    margin-top: 10px;
                    font-size: 14px;
                    color: #6c757d;
                }
                
                .add-option-btn,
                .remove-option-btn {
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin: 5px;
                    font-size: 14px;
                }
                
                .remove-option-btn {
                    background: #dc3545;
                }
                
                .add-option-btn:hover {
                    background: #0056b3;
                }
                
                .remove-option-btn:hover {
                    background: #c82333;
                }
                
                .option-formset {
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 10px 0;
                    background: #f8f9fa;
                }
                
                .option-formset input[type="text"] {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }
                
                .option-formset input[type="checkbox"] {
                    margin-right: 8px;
                }
                
                .option-formset label {
                    font-weight: 500;
                    color: #495057;
                }
            `)
            .appendTo('head');
        
        // Form validatsiyasi
        $('form').on('submit', function(e) {
            var hasOptions = hasOptionsCheckbox.is(':checked');
            
            if (hasOptions) {
                var totalForms = parseInt($('#id_option_set-TOTAL_FORMS').val());
                var validOptions = 0;
                var correctOptions = 0;
                
                for (var i = 0; i < totalForms; i++) {
                    var textField = $(`#id_option_set-${i}-text`);
                    var isCorrectField = $(`#id_option_set-${i}-is_correct`);
                    var deleteField = $(`#id_option_set-${i}-DELETE`);
                    
                    if (!deleteField.is(':checked') && textField.val().trim()) {
                        validOptions++;
                        if (isCorrectField.is(':checked')) {
                            correctOptions++;
                        }
                    }
                }
                
                if (validOptions < 2) {
                    alert('Variantli savolda kamida 2 ta variant bo\'lishi kerak!');
                    e.preventDefault();
                    return false;
                }
                
                if (correctOptions === 0) {
                    alert('Hech bo\'lmaganda bitta variant to\'g\'ri bo\'lishi kerak!');
                    e.preventDefault();
                    return false;
                }
                
                if (correctOptions > 1) {
                    alert('Faqat bitta variant to\'g\'ri bo\'lishi mumkin!');
                    e.preventDefault();
                    return false;
                }
            } else {
                if (!answerField.val().trim()) {
                    alert('Variantlarsiz savolda javob majburiy!');
                    e.preventDefault();
                    return false;
                }
            }
        });
    });
    
})(django.jQuery); 