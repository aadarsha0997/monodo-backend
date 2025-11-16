(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Function to update available_daily_order based on selected level
        function updateAvailableDailyOrder() {
            var levelField = $('#id_level');
            var availableOrderField = $('#id_available_daily_order');
            
            if (levelField.length && availableOrderField.length) {
                var selectedLevelId = levelField.val();
                
                if (selectedLevelId) {
                    // Fetch level data via AJAX
                    $.ajax({
                        url: '/admin/referral_system/customuser/level/' + selectedLevelId + '/get-orders-count/',
                        method: 'GET',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        success: function(data) {
                            if (data.orders_received_count !== undefined) {
                                var currentValue = availableOrderField.val();
                                availableOrderField.val(data.orders_received_count);
                                
                                // Show a brief visual feedback if value changed
                                if (currentValue != data.orders_received_count) {
                                    availableOrderField.css('background-color', '#d4edda');
                                    setTimeout(function() {
                                        availableOrderField.css('background-color', '');
                                    }, 1000);
                                }
                            }
                        },
                        error: function() {
                            // Silently fail - the backend will handle it via save_model
                        }
                    });
                }
            }
        }
        
        // Trigger on level field change
        $(document).on('change', '#id_level', function() {
            updateAvailableDailyOrder();
        });
        
        // Also trigger on page load if level is already selected (for edit page)
        if ($('#id_level').length && $('#id_level').val()) {
            // Small delay to ensure select2 is initialized if using select2
            setTimeout(function() {
                updateAvailableDailyOrder();
            }, 500);
        }
        
        // Handle select2 fields (used by some admin themes like Jazzmin)
        if (typeof django !== 'undefined' && django.jQuery) {
            django.jQuery(document).on('select2:select', '#id_level', function() {
                updateAvailableDailyOrder();
            });
        }
        
        // Also listen for select2 change events using jQuery
        $(document).on('select2:select', '#id_level', function() {
            updateAvailableDailyOrder();
        });
    });
})(django.jQuery || jQuery);
