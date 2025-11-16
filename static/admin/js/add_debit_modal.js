function openDebitModal(userId, username) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.id = 'debit-modal-overlay';
    overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;';
    
    // Create modal content
    const modal = document.createElement('div');
    modal.id = 'debit-modal';
    modal.style.cssText = 'background: white; padding: 30px; border-radius: 8px; max-width: 600px; width: 90%; max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); position: relative;';
    
    const formUrl = `/admin/referral_system/customuser/${userId}/add-debit/`;
    
    modal.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #8B0000; padding-bottom: 10px;">
            <h2 style="margin: 0; color: #8B0000;">Add Debit/Credit Transaction</h2>
            <button onclick="closeDebitModal()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #666;">&times;</button>
        </div>
        
        <form id="debit-form" method="post" action="${formUrl}">
            <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                    Member Account <span style="color: red;">*</span>
                </label>
                <input type="text" value="${username} (ID: ${userId})" readonly 
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background-color: #f5f5f5;">
            </div>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                    Type <span style="color: red;">*</span>
                </label>
                <select name="type" required 
                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <option value="">-- Select Type --</option>
                    <option value="credit">Credit (+)</option>
                    <option value="debit">Debit (-)</option>
                </select>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                    Amount <span style="color: red;">*</span>
                </label>
                <input type="number" name="amount" step="0.01" min="0.01" required placeholder="0.00"
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 10px; font-weight: 600;">Select Remark Type:</label>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <label style="display: flex; align-items: center; cursor: pointer;">
                        <input type="radio" name="remark_type" value="Deposit" style="margin-right: 8px;" onchange="updateRemarkField('Deposit')">
                        <span>Deposit</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer;">
                        <input type="radio" name="remark_type" value="Rewards" style="margin-right: 8px;" onchange="updateRemarkField('Rewards')">
                        <span>Rewards</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer;">
                        <input type="radio" name="remark_type" value="Rebate" style="margin-right: 8px;" onchange="updateRemarkField('Rebate')">
                        <span>Rebate</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer;">
                        <input type="radio" name="remark_type" value="Activation Fees" style="margin-right: 8px;" onchange="updateRemarkField('Activation Fees')">
                        <span>Activation Fees</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer;">
                        <input type="radio" name="remark_type" value="Basic Salary" style="margin-right: 8px;" onchange="updateRemarkField('Basic Salary')">
                        <span>Basic Salary</span>
                    </label>
                </div>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Remark</label>
                <textarea id="remark-field" name="remark" rows="3" placeholder="Enter remark or select a remark type above..."
                          style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;"></textarea>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 25px; padding-top: 20px; border-top: 1px solid #ddd;">
                <button type="submit" 
                        style="background-color: #8B0000; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; flex: 1;">
                    Submit Transaction
                </button>
                <button type="button" onclick="closeDebitModal()" 
                        style="background-color: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; flex: 1;">
                    Cancel
                </button>
            </div>
        </form>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Close on overlay click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            closeDebitModal();
        }
    });
    
    // Wait for modal to be fully added to DOM before attaching event listeners
    setTimeout(function() {
        // Handle form submission
        const form = document.getElementById('debit-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                
                // Ensure remark_type is included if a radio button is selected
                const selectedRemarkType = form.querySelector('input[name="remark_type"]:checked');
                if (selectedRemarkType) {
                    formData.append('remark_type', selectedRemarkType.value);
                }
                
                fetch(formUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => {
                    if (response.redirected || response.ok) {
                        closeDebitModal();
                        window.location.reload();
                    } else {
                        return response.text();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                });
            });
        }
    }, 100);
}

function closeDebitModal() {
    const overlay = document.getElementById('debit-modal-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Make function globally accessible
window.updateRemarkField = function(remarkType) {
    const remarkField = document.getElementById('remark-field');
    if (remarkField) {
        // Set the remark field value to the selected type
        remarkField.value = remarkType;
        // Store the original remark type for form submission
        remarkField.setAttribute('data-remark-type', remarkType);
    }
};

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

