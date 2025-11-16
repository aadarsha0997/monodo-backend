function openWalletInformationModal(userId, username) {
    const walletInfoUrl = `/admin/referral_system/customuser/${userId}/wallet-information/`;
    
    // Fetch wallet information
    fetch(walletInfoUrl, {
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
        
        // Calculate available balance (balance - frozen_amount)
        const availableBalance = parseFloat(data.balance || 0) - parseFloat(data.frozen_amount || 0);
        
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.id = 'wallet-information-modal-overlay';
        overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        
        // Create modal content
        const modal = document.createElement('div');
        modal.id = 'wallet-information-modal';
        modal.style.cssText = 'background: white; padding: 0; border-radius: 8px; max-width: 700px; width: 90%; max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); position: relative;';
        
        // Determine balance color (red if negative)
        const balanceColor = parseFloat(data.balance || 0) < 0 ? '#dc3545' : '#28a745';
        
        modal.innerHTML = `
            <div style="padding: 20px 24px; border-bottom: 1px solid #e9ecef; background-color: #f8f9fa; border-radius: 8px 8px 0 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 600; color: #212529;">
                        <i class="fas fa-wallet" style="color: #28a745; margin-right: 10px;"></i>
                        Wallet Information - ${username}
                    </h3>
                    <button type="button" onclick="closeWalletInformationModal()" 
                            style="background: none; border: none; font-size: 24px; color: #6c757d; cursor: pointer; padding: 0; width: 30px; height: 30px; line-height: 1;"
                            title="Close">&times;</button>
                </div>
            </div>
            
            <form id="wallet-information-form" style="padding: 24px;">
                <div style="margin-bottom: 24px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 8px; color: white; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <div>
                                <p style="margin: 0; font-size: 14px; opacity: 0.9;">Total Balance</p>
                                <h2 style="margin: 8px 0 0 0; font-size: 32px; font-weight: 700; color: ${balanceColor};">
                                    $${parseFloat(data.balance || 0).toFixed(2)}
                                </h2>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 16px; border-radius: 8px;">
                                <i class="fas fa-dollar-sign" style="font-size: 32px;"></i>
                            </div>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                            <div>
                                <p style="margin: 0; font-size: 12px; opacity: 0.8;">Available Balance</p>
                                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: 600;">$${availableBalance.toFixed(2)}</p>
                            </div>
                            <div>
                                <p style="margin: 0; font-size: 12px; opacity: 0.8;">Frozen Amount</p>
                                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: 600;">$${parseFloat(data.frozen_amount || 0).toFixed(2)}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529;">
                        <i class="fas fa-coins" style="color: #ffc107; margin-right: 8px;"></i>
                        Balance & Commission
                    </h4>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Balance *</label>
                            <input type="number" name="balance" value="${data.balance || '0.00'}" step="0.01" required
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Current wallet balance</small>
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Frozen Amount</label>
                            <input type="number" name="frozen_amount" value="${data.frozen_amount || '0.00'}" step="0.01" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Amount frozen/held</small>
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Today's Commission</label>
                            <input type="number" name="todays_commission" value="${data.todays_commission || '0.00'}" step="0.01" min="0" readonly
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: #e9ecef;">
                            <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Commission earned today (read-only)</small>
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Credibility Score</label>
                            <input type="number" name="credibility" value="${data.credibility || 100}" min="0" max="100"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Score from 0 to 100</small>
                        </div>
                    </div>
                </div>
                
                <div style="border-top: 2px solid #e9ecef; margin: 20px 0; padding-top: 20px;">
                    <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #212529;">
                        <i class="fas fa-tasks" style="color: #17a2b8; margin-right: 8px;"></i>
                        Order Settings
                    </h4>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #495057; font-size: 14px;">Available Daily Orders</label>
                            <input type="number" name="available_daily_order" value="${data.available_daily_order || 0}" min="0"
                                   style="width: 100%; padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                            <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Orders available for today</small>
                        </div>
                        
                        <div>
                            <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #495057; font-size: 14px; cursor: pointer; margin-top: 28px;">
                                <input type="checkbox" name="allow_withdrawal" ${data.allow_withdrawal ? 'checked' : ''}
                                       style="width: 18px; height: 18px; cursor: pointer;">
                                Allow Withdrawal
                            </label>
                            <small style="display: block; margin-top: 4px; color: #6c757d; font-size: 12px;">Enable withdrawal requests</small>
                        </div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e9ecef;">
                    <button type="button" onclick="closeWalletInformationModal()" 
                            style="background-color: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">
                        Cancel
                    </button>
                    <button type="submit" 
                            style="background-color: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">
                        <i class="fas fa-save"></i> Save Changes
                    </button>
                </div>
            </form>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Handle form submission
        const form = modal.querySelector('#wallet-information-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitWalletInformation(userId);
        });
        
        // Close on overlay click
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeWalletInformationModal();
            }
        });
    })
    .catch(error => {
        console.error('Error fetching wallet information:', error);
        alert('Error loading wallet information. Please try again.');
    });
}

function closeWalletInformationModal() {
    const overlay = document.getElementById('wallet-information-modal-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function submitWalletInformation(userId) {
    const form = document.getElementById('wallet-information-form');
    const formData = new FormData(form);
    const csrftoken = getCookie('csrftoken');
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    const walletInfoUrl = `/admin/referral_system/customuser/${userId}/wallet-information/`;
    
    fetch(walletInfoUrl, {
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
            closeWalletInformationModal();
            // Show success message
            showSuccessMessage(data.message || 'Wallet information updated successfully!');
            // Reload page to show updated values
            setTimeout(() => window.location.reload(), 1000);
        } else {
            throw new Error(data.error || 'Failed to update wallet information');
        }
    })
    .catch(error => {
        console.error('Error updating wallet information:', error);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        alert('An error occurred while updating wallet information. Please try again.');
    });
}

