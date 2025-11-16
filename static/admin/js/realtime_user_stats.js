(function($) {
    'use strict';
    
    let statsPollInterval;
    let isPolling = false;
    
    function getUserIdFromRow(row) {
        // Try multiple ways to get user ID from row
        // Method 1: Check for checkbox value
        const checkbox = row.querySelector('input[name="_selected_action"]');
        if (checkbox && checkbox.value) {
            return checkbox.value;
        }
        
        // Method 2: Check for data-user-id attribute
        if (row.dataset && row.dataset.userId) {
            return row.dataset.userId;
        }
        
        // Method 3: Check first cell (ID column) text content
        const firstCell = row.querySelector('td:first-child');
        if (firstCell) {
            const text = firstCell.textContent.trim();
            const id = parseInt(text);
            if (!isNaN(id)) {
                return id.toString();
            }
        }
        
        // Method 4: Try to extract from row ID
        if (row.id) {
            const match = row.id.match(/user-(\d+)/);
            if (match) {
                return match[1];
            }
        }
        
        return null;
    }
    
    function getAllUserIds() {
        const userIds = [];
        const rows = document.querySelectorAll('#result_list tbody tr');
        
        rows.forEach(row => {
            const userId = getUserIdFromRow(row);
            if (userId) {
                userIds.push(userId);
            }
        });
        
        return userIds;
    }
    
    function updateUserStats(stats) {
        const rows = document.querySelectorAll('#result_list tbody tr');
        
        rows.forEach(row => {
            const userId = getUserIdFromRow(row);
            if (!userId || !stats[userId]) {
                return;
            }
            
            const userStat = stats[userId];
            const cells = row.querySelectorAll('td');
            
            // Find cells by their position or class and update
            // We need to map list_display order to actual cells
            // available_daily_order, taking_orders_today, current_orders_made, 
            // orders_received_today, todays_commission are in list_display
            cells.forEach((cell, index) => {
                const cellText = cell.textContent.trim();
                
                // Check if this cell contains the field we're looking for
                // We'll update based on cell content patterns
                
                // Check by class name first (more reliable)
                const cellClasses = cell.className || '';
                
                // Update balance_display (column 4: id, username, superior_id, phone_number, balance_display)
                if (cellClasses.includes('field-balance') || cell.querySelector('.balance_display, .negative-balance')) {
                    const newBalance = parseFloat(userStat.balance || 0);
                    const balanceElement = cell.querySelector('.balance_display, .negative-balance') || cell;
                    const currentText = balanceElement.textContent || '';
                    const currentBalance = parseFloat(currentText.replace(/[^0-9.-]/g, '')) || 0;
                    
                    if (Math.abs(currentBalance - newBalance) > 0.01) {
                        if (newBalance < 0) {
                            balanceElement.innerHTML = '<span class="negative-balance" style="color: red; font-weight: bold; padding: 2px 6px; border-radius: 3px; display: inline-block; animation: pulseRed 2s infinite;">$' + newBalance.toFixed(2) + '</span>';
                        } else {
                            balanceElement.textContent = '$' + newBalance.toFixed(2);
                        }
                        cell.classList.add('updated-field');
                        setTimeout(() => cell.classList.remove('updated-field'), 1000);
                    }
                }
                
                // Update available_daily_order (column 5)
                if (cellClasses.includes('field-available_daily_order')) {
                    const newValue = userStat.available_daily_order;
                    const currentValue = parseInt(cell.textContent.trim()) || 0;
                    if (currentValue !== newValue) {
                        cell.textContent = newValue;
                        cell.classList.add('updated-field');
                        setTimeout(() => cell.classList.remove('updated-field'), 1000);
                    }
                }
                
                // Update taking_orders_today (column 6)
                if (cellClasses.includes('field-taking_orders_today')) {
                    const newValue = userStat.taking_orders_today;
                    const currentValue = parseInt(cell.textContent.trim()) || 0;
                    if (currentValue !== newValue) {
                        cell.textContent = newValue;
                        cell.classList.add('updated-field');
                        setTimeout(() => cell.classList.remove('updated-field'), 1000);
                    }
                }
                
                // Update current_orders_made (column 7)
                if (cellClasses.includes('field-current_orders_made')) {
                    const newValue = userStat.current_orders_made;
                    const currentValue = parseInt(cell.textContent.trim()) || 0;
                    if (currentValue !== newValue) {
                        cell.textContent = newValue;
                        cell.classList.add('updated-field');
                        setTimeout(() => cell.classList.remove('updated-field'), 1000);
                    }
                }
                
                // Update orders_received_today (column 8)
                if (cellClasses.includes('field-orders_received_today')) {
                    const newValue = userStat.orders_received_today;
                    const currentValue = parseInt(cell.textContent.trim()) || 0;
                    if (currentValue !== newValue) {
                        cell.textContent = newValue;
                        cell.classList.add('updated-field');
                        setTimeout(() => cell.classList.remove('updated-field'), 1000);
                    }
                }
                
                // Update todays_commission (column 9)
                if (cellClasses.includes('field-todays_commission')) {
                    const newValue = parseFloat(userStat.todays_commission || 0);
                    const currentText = cell.textContent.trim().replace(/[$,\s]/g, '');
                    const currentValue = parseFloat(currentText) || 0;
                    if (Math.abs(currentValue - newValue) > 0.01) {
                        // Format as currency
                        cell.textContent = '$' + newValue.toFixed(2);
                        cell.classList.add('updated-field');
                        setTimeout(() => cell.classList.remove('updated-field'), 1000);
                    }
                }
                
                // Update frozen_amount (if column exists in list_display)
                if (cellClasses.includes('field-frozen_amount')) {
                    const newValue = parseFloat(userStat.frozen_amount || 0);
                    const currentText = cell.textContent.trim().replace(/[$,\s]/g, '');
                    const currentValue = parseFloat(currentText) || 0;
                    if (Math.abs(currentValue - newValue) > 0.01) {
                        // Format as currency
                        cell.textContent = '$' + newValue.toFixed(2);
                        cell.classList.add('updated-field');
                        setTimeout(() => cell.classList.remove('updated-field'), 1000);
                    }
                }
                
            });
        });
    }
    
    function fetchUserStats() {
        if (isPolling) {
            return; // Prevent concurrent requests
        }
        
        const userIds = getAllUserIds();
        if (userIds.length === 0) {
            return;
        }
        
        isPolling = true;
        
        $.ajax({
            url: '/admin/referral_system/customuser/get-user-stats/',
            method: 'GET',
            data: {
                'user_ids[]': userIds
            },
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(data) {
                if (data.stats) {
                    updateUserStats(data.stats);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error fetching user stats:', error);
            },
            complete: function() {
                isPolling = false;
            }
        });
    }
    
    function startRealTimePolling() {
        // Only start if we're on the changelist page
        if (!document.querySelector('#result_list')) {
            return;
        }
        
        // Clear any existing interval
        if (statsPollInterval) {
            clearInterval(statsPollInterval);
        }
        
        // Fetch stats immediately
        fetchUserStats();
        
        // Then poll every 2 seconds
        statsPollInterval = setInterval(fetchUserStats, 2000);
    }
    
    function stopRealTimePolling() {
        if (statsPollInterval) {
            clearInterval(statsPollInterval);
            statsPollInterval = null;
        }
    }
    
    $(document).ready(function() {
        // Start polling when page loads
        startRealTimePolling();
        
        // Also start after AJAX navigation (if using AJAX pagination)
        $(document).on('DOMNodeInserted', '#result_list', function() {
            setTimeout(startRealTimePolling, 500);
        });
    });
    
    // Clean up on page unload
    $(window).on('beforeunload', function() {
        stopRealTimePolling();
    });
    
    // Handle navigation away from changelist
    $(document).on('click', 'a', function() {
        // If clicking a link that navigates away from changelist, stop polling
        const href = $(this).attr('href');
        if (href && !href.includes('/admin/referral_system/customuser/') && 
            !href.includes('#') && 
            !href.includes('javascript:')) {
            stopRealTimePolling();
        }
    });
    
})(django.jQuery || jQuery);

