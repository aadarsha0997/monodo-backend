function openAccountChangeModal(userId, username) {
    const accountChangeUrl = `/admin/referral_system/customuser/${userId}/account-change/`;
    
    // Fetch account change data
    fetch(accountChangeUrl, {
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
        overlay.id = 'account-change-modal-overlay';
        overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        
        // Create modal content
        const modal = document.createElement('div');
        modal.id = 'account-change-modal';
        modal.style.cssText = 'background: white; padding: 0; border-radius: 8px; max-width: 700px; width: 90%; max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); position: relative;';
        
        // Build agent options
        let agentOptions = '<option value="">-- No Agent --</option>';
        if (data.agents && data.agents.length > 0) {
            data.agents.forEach(agent => {
                const selected = agent.id === data.current_agent_id ? 'selected' : '';
                agentOptions += `<option value="${agent.id}" ${selected}>${agent.username} (ID: ${agent.id})</option>`;
            });
        }
        
        // Build level options
        let levelOptions = '<option value="">-- No Level --</option>';
        if (data.levels && data.levels.length > 0) {
            data.levels.forEach(level => {
                const selected = level.id === data.current_level_id ? 'selected' : '';
                levelOptions += `<option value="${level.id}" ${selected}>${level.name}</option>`;
            });
        }
        
        // Build referred by options
        let referredByOptions = '<option value="">-- No Referrer --</option>';
        if (data.users && data.users.length > 0) {
            data.users.forEach(user => {
                if (user.id !== parseInt(userId)) { // Don't allow self-referral
                    const selected = user.id === data.current_referred_by_id ? 'selected' : '';
                    referredByOptions += `<option value="${user.id}" ${selected}>${user.username} (ID: ${user.id})</option>`;
                }
            });
        }
        
        modal.innerHTML = `
            <div style="padding: 20px 24px; border-bottom: 1px solid #e9ecef; background-color: #f8f9fa; border-radius: 8px 8px 0 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 600; color: #212529;">
                        <i class="fas fa-exchange-alt" style="color: #ffc107; margin-right: 10px;"></i>
                        Account Change - ${username}
                    </h3>
                    <button type="button" onclick="closeAccountChangeModal()" 
                            style="background: none; border: none; font-size: 24px; color: #6c757d; cursor: pointer; padding: 0; width: 30px; height: 30px; line-height: 1;"
                            title="Close">&times;</button>
                </div>
            </div>
            
            <form id="account-change-form" style="padding: 24px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">User Type *</label>
                        <select name="user_type" required
                                style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            <option value="USER" ${data.user_type === 'USER' ? 'selected' : ''}>Normal User</option>
                            <option value="AGENT" ${data.user_type === 'AGENT' ? 'selected' : ''}>Agent</option>
                            <option value="SUPERADMIN" ${data.user_type === 'SUPERADMIN' ? 'selected' : ''}>Super Admin</option>
                        </select>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Level</label>
                        <select name="level" style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            ${levelOptions}
                        </select>
                        <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Changing level will update available daily orders</small>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Agent / Superior User</label>
                        <select name="agent" style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            ${agentOptions}
                        </select>
                        <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Select an agent as superior user</small>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Referred By</label>
                        <select name="referred_by" style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            ${referredByOptions}
                        </select>
                        <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">User who referred this account</small>
                    </div>
                </div>
                
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529;">
                        <i class="fas fa-shield-alt" style="color: #28a745; margin-right: 8px;"></i>
                        Permissions & Status
                    </h4>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #495057; font-size: 14px; cursor: pointer; margin-bottom: 15px;">
                                <input type="checkbox" name="is_active" ${data.is_active ? 'checked' : ''}
                                       style="width: 18px; height: 18px; cursor: pointer;">
                                Active Account
                            </label>
                            
                            <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #495057; font-size: 14px; cursor: pointer; margin-bottom: 15px;">
                                <input type="checkbox" name="allow_withdrawal" ${data.allow_withdrawal ? 'checked' : ''}
                                       style="width: 18px; height: 18px; cursor: pointer;">
                                Allow Withdrawal
                            </label>
                            
                            <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #495057; font-size: 14px; cursor: pointer;">
                                <input type="checkbox" name="rob_single" ${data.rob_single ? 'checked' : ''}
                                       style="width: 18px; height: 18px; cursor: pointer;">
                                Rob Single
                            </label>
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Credibility Score (0-100)</label>
                            <input type="number" name="credibility" value="${data.credibility || 100}" min="0" max="100"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            
                            <label style="display: block; margin-bottom: 8px; margin-top: 15px; font-weight: 600; color: #495057; font-size: 14px;">Frozen Amount</label>
                            <input type="number" name="frozen_amount" value="${data.frozen_amount || '0.00'}" step="0.01" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e9ecef;">
                    <button type="button" onclick="closeAccountChangeModal()" 
                            style="background-color: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">
                        Cancel
                    </button>
                    <button type="submit" 
                            style="background-color: #ffc107; color: #212529; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">
                        <i class="fas fa-save"></i> Save Changes
                    </button>
                </div>
            </form>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Handle form submission
        const form = modal.querySelector('#account-change-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitAccountChange(userId);
        });
        
        // Close on overlay click
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeAccountChangeModal();
            }
        });
    })
    .catch(error => {
        console.error('Error fetching account change data:', error);
        alert('Error loading account change data. Please try again.');
    });
}

function closeAccountChangeModal() {
    const overlay = document.getElementById('account-change-modal-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function submitAccountChange(userId) {
    const form = document.getElementById('account-change-form');
    const formData = new FormData(form);
    const csrftoken = getCookie('csrftoken');
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    const accountChangeUrl = `/admin/referral_system/customuser/${userId}/account-change/`;
    
    fetch(accountChangeUrl, {
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
            closeAccountChangeModal();
            // Show success message
            showSuccessMessage(data.message || 'Account changes saved successfully!');
            // Reload page to show updated values
            setTimeout(() => window.location.reload(), 1000);
        } else {
            throw new Error(data.error || 'Failed to update account changes');
        }
    })
    .catch(error => {
        console.error('Error updating account changes:', error);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        alert('An error occurred while updating account changes. Please try again.');
    });
}

// Helper functions (shared with account_details_modal.js)
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

