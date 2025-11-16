function openAccountDetailsModal(userId, username) {
    const accountDetailsUrl = `/admin/referral_system/customuser/${userId}/account-details/`;
    
    // Fetch account details
    fetch(accountDetailsUrl, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.id = 'account-details-modal-overlay';
        overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        
        // Create modal content
        const modal = document.createElement('div');
        modal.id = 'account-details-modal';
        modal.style.cssText = 'background: white; padding: 0; border-radius: 8px; max-width: 700px; width: 90%; max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); position: relative;';
        
        modal.innerHTML = `
            <div style="padding: 20px 24px; border-bottom: 1px solid #e9ecef; background-color: #f8f9fa; border-radius: 8px 8px 0 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 600; color: #212529;">
                        <i class="fas fa-user-circle" style="color: #007bff; margin-right: 10px;"></i>
                        Account Details - ${username}
                    </h3>
                    <button type="button" onclick="closeAccountDetailsModal()" 
                            style="background: none; border: none; font-size: 24px; color: #6c757d; cursor: pointer; padding: 0; width: 30px; height: 30px; line-height: 1;"
                            title="Close">&times;</button>
                </div>
            </div>
            
            <form id="account-details-form" style="padding: 24px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Username *</label>
                        <input type="text" name="username" value="${data.username || ''}" required
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Phone Number *</label>
                        <input type="text" name="phone_number" value="${data.phone_number || ''}" required
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                    </div>
                    
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">User Type</label>
                        <input type="text" value="${data.user_type || ''}" readonly
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: #e9ecef;">
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Level</label>
                        <input type="text" value="${data.level || ''}" readonly
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: #e9ecef;">
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Balance</label>
                        <input type="text" value="$${data.balance || '0.00'}" readonly
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: #e9ecef;">
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Operate</label>
                        <input type="text" name="operate" value="${data.operate || ''}"
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Place</label>
                        <input type="text" name="place" value="${data.place || ''}"
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Date Joined</label>
                        <input type="text" value="${data.date_joined || ''}" readonly
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: #e9ecef;">
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Last Login</label>
                        <input type="text" value="${data.last_login || 'Never'}" readonly
                               style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: #e9ecef;">
                    </div>
                </div>
                
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529;">
                        <i class="fas fa-university" style="color: #28a745; margin-right: 8px;"></i>
                        Bank Account Details
                    </h4>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Account Holder Name</label>
                            <input type="text" name="bank_account_holder_name" value="${data.bank_account_holder_name || ''}"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Account Number</label>
                            <input type="text" name="bank_account_number" value="${data.bank_account_number || ''}"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Bank Name</label>
                            <input type="text" name="bank_name" value="${data.bank_name || ''}"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Routing Number</label>
                            <input type="text" name="bank_routing_number" value="${data.bank_routing_number || ''}"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Account Type</label>
                            <select name="bank_account_type" style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                                <option value="checking" ${data.bank_account_type === 'checking' ? 'selected' : ''}>Checking</option>
                                <option value="savings" ${data.bank_account_type === 'savings' ? 'selected' : ''}>Savings</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e9ecef;">
                    <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #495057; font-size: 14px; cursor: pointer;">
                        <input type="checkbox" name="is_active" ${data.is_active ? 'checked' : ''}
                               style="width: 18px; height: 18px; cursor: pointer;">
                        Active Account
                    </label>
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e9ecef;">
                    <button type="button" onclick="closeAccountDetailsModal()" 
                            style="background-color: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">
                        Cancel
                    </button>
                    <button type="submit" 
                            style="background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">
                        <i class="fas fa-save"></i> Save Changes
                    </button>
                </div>
            </form>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Handle form submission
        const form = modal.querySelector('#account-details-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitAccountDetails(userId);
        });
        
        // Close on overlay click
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeAccountDetailsModal();
            }
        });
    })
    .catch(error => {
        console.error('Error fetching account details:', error);
        alert('Error loading account details. Please try again.');
    });
}

function closeAccountDetailsModal() {
    const overlay = document.getElementById('account-details-modal-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function submitAccountDetails(userId) {
    const form = document.getElementById('account-details-form');
    const formData = new FormData(form);
    const csrftoken = getCookie('csrftoken');
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    const accountDetailsUrl = `/admin/referral_system/customuser/${userId}/account-details/`;
    
    fetch(accountDetailsUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeAccountDetailsModal();
            // Show success message
            showSuccessMessage(data.message || 'Account details updated successfully!');
            // Reload page to show updated values
            setTimeout(() => window.location.reload(), 1000);
        } else {
            throw new Error(data.error || 'Failed to update account details');
        }
    })
    .catch(error => {
        console.error('Error updating account details:', error);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        alert('An error occurred while updating account details. Please try again.');
    });
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

function showSuccessMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'alert alert-success alert-dismissible';
    messageDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10001; min-width: 300px;';
    messageDiv.innerHTML = `
        <button type="button" class="close" data-dismiss="alert" aria-hidden="true" onclick="this.parentElement.remove()">×</button>
        <strong>Success!</strong> ${message}
    `;
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 5000);
}

