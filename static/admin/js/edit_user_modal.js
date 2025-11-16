function openEditUserModal(userId, username) {
    const editUserUrl = `/admin/referral_system/customuser/${userId}/edit-user/`;
    
    // Fetch user data
    fetch(editUserUrl, {
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
        overlay.id = 'edit-user-modal-overlay';
        overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        
        // Create modal content
        const modal = document.createElement('div');
        modal.id = 'edit-user-modal';
        modal.style.cssText = 'background: white; padding: 0; border-radius: 8px; max-width: 900px; width: 95%; max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); position: relative;';
        
        // Build dropdown options
        let levelOptions = '<option value="">-- No Level --</option>';
        if (data.levels && data.levels.length > 0) {
            data.levels.forEach(level => {
                const selected = level.id === data.level_id ? 'selected' : '';
                levelOptions += `<option value="${level.id}" ${selected}>${level.name}</option>`;
            });
        }
        
        let agentOptions = '<option value="">-- No Agent --</option>';
        if (data.agents && data.agents.length > 0) {
            data.agents.forEach(agent => {
                const selected = agent.id === data.agent_id ? 'selected' : '';
                agentOptions += `<option value="${agent.id}" ${selected}>${agent.username} (ID: ${agent.id})</option>`;
            });
        }
        
        let referredByOptions = '<option value="">-- No Referrer --</option>';
        if (data.users && data.users.length > 0) {
            data.users.forEach(user => {
                if (user.id !== parseInt(userId)) {
                    const selected = user.id === data.referred_by_id ? 'selected' : '';
                    referredByOptions += `<option value="${user.id}" ${selected}>${user.username} (ID: ${user.id})</option>`;
                }
            });
        }
        
        modal.innerHTML = `
            <div style="padding: 20px 24px; border-bottom: 1px solid #e9ecef; background-color: #f8f9fa; border-radius: 8px 8px 0 0; position: sticky; top: 0; z-index: 10;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 600; color: #212529;">
                        <i class="fas fa-edit" style="color: #007bff; margin-right: 10px;"></i>
                        Edit User - ${username}
                    </h3>
                    <button type="button" onclick="closeEditUserModal()" 
                            style="background: none; border: none; font-size: 24px; color: #6c757d; cursor: pointer; padding: 0; width: 30px; height: 30px; line-height: 1;"
                            title="Close">&times;</button>
                </div>
            </div>
            
            <form id="edit-user-form" style="padding: 24px;">
                <!-- Basic Information -->
                <div style="margin-bottom: 24px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529; border-bottom: 2px solid #007bff; padding-bottom: 8px;">
                        <i class="fas fa-user" style="color: #007bff; margin-right: 8px;"></i>
                        Basic Information
                    </h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
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
                        ${data.has_email ? `
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Email</label>
                            <input type="email" name="email" value="${data.email || ''}"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        ` : ''}
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Referral Code</label>
                            <input type="text" name="referral_code" value="${data.referral_code || ''}" maxlength="10"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
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
                    </div>
                </div>
                
                <!-- Account Settings -->
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529; border-bottom: 2px solid #28a745; padding-bottom: 8px;">
                        <i class="fas fa-cog" style="color: #28a745; margin-right: 8px;"></i>
                        Account Settings
                    </h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
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
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Agent / Superior User</label>
                            <select name="agent" style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                                ${agentOptions}
                            </select>
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Referred By</label>
                            <select name="referred_by" style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                                ${referredByOptions}
                            </select>
                        </div>
                    </div>
                </div>
                
                <!-- Balance & Financial -->
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529; border-bottom: 2px solid #ffc107; padding-bottom: 8px;">
                        <i class="fas fa-dollar-sign" style="color: #ffc107; margin-right: 8px;"></i>
                        Balance & Financial
                    </h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Balance *</label>
                            <input type="number" name="balance" value="${data.balance || '0.00'}" step="0.01" required
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Frozen Amount</label>
                            <input type="number" name="frozen_amount" value="${data.frozen_amount || '0.00'}" step="0.01" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Today's Commission</label>
                            <input type="number" name="todays_commission" value="${data.todays_commission || '0.00'}" step="0.01" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Credibility Score (0-100)</label>
                            <input type="number" name="credibility" value="${data.credibility || 100}" min="0" max="100"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-top: 28px;">
                            <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #495057; font-size: 14px; cursor: pointer;">
                                <input type="checkbox" name="allow_withdrawal" ${data.allow_withdrawal ? 'checked' : ''}
                                       style="width: 18px; height: 18px; cursor: pointer;">
                                Allow Withdrawal
                            </label>
                        </div>
                    </div>
                </div>
                
                <!-- Order Tracking -->
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529; border-bottom: 2px solid #17a2b8; padding-bottom: 8px;">
                        <i class="fas fa-tasks" style="color: #17a2b8; margin-right: 8px;"></i>
                        Order Tracking
                    </h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Available Daily Orders</label>
                            <input type="number" name="available_daily_order" value="${data.available_daily_order || 0}" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Taking Orders Today</label>
                            <input type="number" name="taking_orders_today" value="${data.taking_orders_today || 0}" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Orders Received Today</label>
                            <input type="number" name="orders_received_today" value="${data.orders_received_today || 0}" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Current Orders Made</label>
                            <input type="number" name="current_orders_made" value="${data.current_orders_made || 0}" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Start Continuous Orders After</label>
                            <input type="number" name="start_continuous_orders_after" value="${data.start_continuous_orders_after || 0}" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                    </div>
                </div>
                
                <!-- Bank Account Details -->
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529; border-bottom: 2px solid #6f42c1; padding-bottom: 8px;">
                        <i class="fas fa-university" style="color: #6f42c1; margin-right: 8px;"></i>
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
                                <option value="">-- Select --</option>
                                <option value="checking" ${data.bank_account_type === 'checking' ? 'selected' : ''}>Checking</option>
                                <option value="savings" ${data.bank_account_type === 'savings' ? 'selected' : ''}>Savings</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <!-- Permissions & Status -->
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529; border-bottom: 2px solid #dc3545; padding-bottom: 8px;">
                        <i class="fas fa-shield-alt" style="color: #dc3545; margin-right: 8px;"></i>
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
                                <input type="checkbox" name="is_staff" ${data.is_staff ? 'checked' : ''}
                                       style="width: 18px; height: 18px; cursor: pointer;">
                                Staff Status
                            </label>
                            <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #495057; font-size: 14px; cursor: pointer;">
                                <input type="checkbox" name="rob_single" ${data.rob_single ? 'checked' : ''}
                                       style="width: 18px; height: 18px; cursor: pointer;">
                                Rob Single
                            </label>
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Password (leave blank to keep current)</label>
                            <input type="password" name="password" placeholder="Enter new password"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Leave blank to keep current password</small>
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Withdraw Password (leave blank to keep current)</label>
                            <input type="password" name="withdraw_password" placeholder="Enter new withdraw password"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Leave blank to keep current password</small>
                        </div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e9ecef;">
                    <button type="button" onclick="closeEditUserModal()" 
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
        const form = modal.querySelector('#edit-user-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitEditUser(userId);
        });
        
        // Close on overlay click
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeEditUserModal();
            }
        });
    })
    .catch(error => {
        console.error('Error fetching user data:', error);
        alert('Error loading user data. Please try again.');
    });
}

function closeEditUserModal() {
    const overlay = document.getElementById('edit-user-modal-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function submitEditUser(userId) {
    const form = document.getElementById('edit-user-form');
    const formData = new FormData(form);
    const csrftoken = getCookie('csrftoken');
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    const editUserUrl = `/admin/referral_system/customuser/${userId}/edit-user/`;
    
    fetch(editUserUrl, {
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
            closeEditUserModal();
            // Show success message
            showSuccessMessage(data.message || 'User updated successfully!');
            // Reload page to show updated values
            setTimeout(() => window.location.reload(), 1000);
        } else {
            throw new Error(data.error || 'Failed to update user');
        }
    })
    .catch(error => {
        console.error('Error updating user:', error);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        alert('An error occurred while updating user. Please try again.');
    });
}

