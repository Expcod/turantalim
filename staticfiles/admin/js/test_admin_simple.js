// Oddiy JavaScript for Test Admin Panel
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
        console.log('Simple test admin JavaScript yuklandi');
        
        // Elementlarni topish
        var examSelect = document.getElementById('id_exam');
        var sectionSelect = document.getElementById('id_section');
        
        if (!examSelect || !sectionSelect) {
            console.log('Kerakli elementlar topilmadi');
            return;
        }
        
        console.log('Elementlar topildi');
        
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
            sectionSelect.disabled = true;
            sectionSelect.innerHTML = '<option value="">Yuklanmoqda...</option>';
            
            console.log('AJAX so\'rov yuborilmoqda...');
            
            // AJAX orqali sectionlarni olish
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/multilevel/admin/sections/get-sections-by-exam/?exam_id=' + examId, true);
            
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    console.log('Response status:', xhr.status);
                    console.log('Response text:', xhr.responseText);
                    
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
                            } else {
                                sectionSelect.innerHTML = '<option value="">Bo\'limlar topilmadi</option>';
                            }
                            
                            sectionSelect.disabled = false;
                            
                        } catch (e) {
                            console.error('JSON parse xatolik:', e);
                            sectionSelect.innerHTML = '<option value="">Xatolik yuz berdi</option>';
                            sectionSelect.disabled = false;
                        }
                    } else {
                        console.error('AJAX xatolik:', xhr.status, xhr.responseText);
                        sectionSelect.innerHTML = '<option value="">Server xatolik</option>';
                        sectionSelect.disabled = false;
                    }
                }
            };
            
            xhr.onerror = function() {
                console.error('Network xatolik');
                sectionSelect.innerHTML = '<option value="">Tarmoq xatolik</option>';
                sectionSelect.disabled = false;
            };
            
            xhr.send();
        }
        
        // Event listener qo'shish
        examSelect.addEventListener('change', function() {
            console.log('Exam o\'zgartirildi!');
            updateSections();
        });
        
        // Sahifa yuklanganda ham sectionlarni yangilash
        if (examSelect.value) {
            updateSections();
        } else {
            // Agar exam tanlanmagan bo'lsa, section ni o'chirish
            sectionSelect.disabled = true;
        }
    });
    
})(); 