function openResetOrderModal(userId, username) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.id = 'reset-order-modal-overlay';
    overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;';
    
    // Create modal content
    const modal = document.createElement('div');
    modal.id = 'reset-order-modal';
    modal.style.cssText = 'background: white; padding: 0; border-radius: 8px; max-width: 500px; width: 90%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); position: relative;';
    
    const resetUrl = `/admin/referral_system/customuser/${userId}/reset-order-quantity/`;
    
    modal.innerHTML = `
        <div style="padding: 24px 24px 20px 24px; border-bottom: 1px solid #e9ecef;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 24px; color: #ff8c00;"></i>
                <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: #212529;">Reset the number of received orders</h3>
            </div>
        </div>
        
        <div style="padding: 24px;">
            <p style="margin: 0; font-size: 14px; color: #495057; line-height: 1.5;">
                Confirm reset <strong>"${username}"</strong>'s number of received orders?
            </p>
        </div>
        
        <div style="padding: 16px 24px; background-color: #f8f9fa; border-top: 1px solid #e9ecef; border-radius: 0 0 8px 8px; display: flex; justify-content: flex-end; gap: 10px;">
            <button type="button" onclick="closeResetOrderModal()" 
                    style="background-color: #fff; color: #6c757d; padding: 8px 20px; border: 1px solid #dee2e6; border-radius: 4px; cursor: pointer; font-weight: 500; font-size: 14px;">
                Cancel
            </button>
            <button type="button" onclick="confirmResetOrder(${userId}, '${username}')" 
                    style="background-color: #ff8c00; color: white; padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">
                Confirm
            </button>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Close on overlay click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            closeResetOrderModal();
        }
    });
}

function closeResetOrderModal() {
    const overlay = document.getElementById('reset-order-modal-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function confirmResetOrder(userId, username) {
    const resetUrl = `/admin/referral_system/customuser/${userId}/reset-order-quantity/`;
    const csrftoken = getCookie('csrftoken');
    
    // Show loading state
    const confirmBtn = event.target;
    const originalText = confirmBtn.innerHTML;
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
    
    fetch(resetUrl, {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeResetOrderModal();
            
            // Update values on the page without reload
            updateUserValues(data);
            
            // Show success message
            showSuccessMessage(data.message);
        } else {
            throw new Error(data.error || 'Reset failed');
        }
    })
    .catch(error => {
        console.error('Error resetting order quantity:', error);
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = originalText;
        alert('An error occurred while resetting. Please try again.');
    });
}

function updateUserValues(data) {
    // Update balance field if visible
    const balanceField = document.querySelector('input[name="balance"]');
    if (balanceField) {
        balanceField.value = data.new_balance;
    }
    
    // Update orders_received_today field if visible
    const ordersReceivedField = document.querySelector('input[name="orders_received_today"]');
    if (ordersReceivedField) {
        ordersReceivedField.value = data.new_orders_received;
    }
    
    // Update taking_orders_today field if visible
    const takingOrdersField = document.querySelector('input[name="taking_orders_today"]');
    if (takingOrdersField) {
        takingOrdersField.value = data.new_taking_orders;
    }
    
    // Update current_orders_made field if visible
    const currentOrdersField = document.querySelector('input[name="current_orders_made"]');
    if (currentOrdersField) {
        currentOrdersField.value = data.new_current_orders;
    }
    
    // Update list display values if on changelist page
    const balanceDisplay = document.querySelector('.balance_display');
    if (balanceDisplay) {
        balanceDisplay.textContent = '$' + data.new_balance;
    }
    
    // Update any displayed values in the list
    const rows = document.querySelectorAll('tr[data-user-id]');
    rows.forEach(row => {
        // Update balance in list if present
        const balanceCell = row.querySelector('.field-balance');
        if (balanceCell) {
            balanceCell.textContent = '$' + data.new_balance;
        }
    });
}

function showSuccessMessage(message) {
    // Create a temporary success message
    const messageDiv = document.createElement('div');
    messageDiv.className = 'alert alert-success alert-dismissible';
    messageDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; min-width: 300px;';
    messageDiv.innerHTML = `
        <button type="button" class="close" data-dismiss="alert" aria-hidden="true" onclick="this.parentElement.remove()">×</button>
        <strong>Success!</strong> ${message}
    `;
    document.body.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 5000);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

