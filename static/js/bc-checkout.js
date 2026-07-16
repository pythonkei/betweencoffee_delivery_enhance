/**
 * bc-checkout.js — Between Coffee 一頁式結帳
 * Sprint 1: 一頁式結帳 + 取餐通知
 * 
 * 依賴: 無 (純 Vanilla JS)
 */

class OnePageCheckout {
  constructor() {
    this.form = document.getElementById('bc-checkout-form');
    this.selectedPayment = null;
    this.selectedTime = null;
    this.csrfToken = this._getCSRF();

    if (!this.form) return;
    this._bindEvents();
  }

  _bindEvents() {
    // 支付方式選擇
    document.querySelectorAll('.bc-payment-option').forEach(el => {
      el.addEventListener('click', () => this._selectPayment(el.dataset.method));
    });

    // 取貨時間選擇
    document.querySelectorAll('.bc-time-chip').forEach(el => {
      el.addEventListener('click', () => this._selectTime(el.dataset.minutes));
    });

    // 表單提交
    this.form.addEventListener('submit', (e) => this._handleSubmit(e));
  }

  _selectPayment(method) {
    this.selectedPayment = method;
    document.querySelectorAll('.bc-payment-option').forEach(el => {
      el.classList.toggle('active', el.dataset.method === method);
    });
  }

  _selectTime(minutes) {
    this.selectedTime = minutes;
    document.querySelectorAll('.bc-time-chip').forEach(el => {
      el.classList.toggle('active', el.dataset.minutes === minutes);
    });
  }

  async _handleSubmit(e) {
    e.preventDefault();

    const submitBtn = this.form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = '處理中...';

    try {
      const formData = new FormData(this.form);
      
      // 加入支付方式和取貨時間
      if (this.selectedPayment) {
        formData.append('payment_method', this.selectedPayment);
      }
      if (this.selectedTime) {
        formData.append('pickup_time', this.selectedTime);
      }

      const response = await fetch(this.form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const data = await response.json();

      if (data.success) {
        // 根據支付方式處理跳轉
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else if (data.order_id) {
          window.location.href = `/order/${data.order_id}/confirmation/`;
        }
      } else {
        alert(data.message || '提交失敗，請重試');
        submitBtn.disabled = false;
        submitBtn.textContent = '確認訂單並支付';
      }
    } catch (err) {
      console.error('提交訂單失敗:', err);
      alert('系統錯誤，請稍後再試');
      submitBtn.disabled = false;
      submitBtn.textContent = '確認訂單並支付';
    }
  }

  _getCSRF() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
      c = c.trim();
      if (c.startsWith(name + '=')) {
        return decodeURIComponent(c.substring(name.length + 1));
      }
    }
    return '';
  }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  new OnePageCheckout();
});
