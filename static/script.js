
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
  logoutBtn.addEventListener('click', () => {
    alert('Logged out successfully!');
    window.location.href = 'login.html';
  });
}

// Detect if this page should run in client-only demo mode (no backend)
const expenseForm = document.getElementById('expense-form');
const expenseList = document.getElementById('expense-list');
const totalAmount = document.getElementById('total-amount');
const clearExpensesBtn = document.getElementById('clear-expenses');

// Only use localStorage logic when there is no action attribute (pure client demo)
const usingClientOnlyMode = !!(expenseForm && !expenseForm.getAttribute('action'));

let expenses = [];
if (usingClientOnlyMode) {
  expenses = JSON.parse(localStorage.getItem('expenses')) || [];

  expenseForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('expense-name').value.trim();
    const amount = parseFloat(document.getElementById('expense-amount').value);

    if (name && !isNaN(amount) && amount > 0) {
      expenses.push({ name, amount });
      localStorage.setItem('expenses', JSON.stringify(expenses));
      updateExpenseList();
      updateTotalAmount();
      expenseForm.reset();
    }
  });

  if (clearExpensesBtn) {
    clearExpensesBtn.addEventListener('click', () => {
      if (confirm("Are you sure you want to clear all expenses?")) {
        expenses = [];
        localStorage.removeItem('expenses');
        updateExpenseList();
        updateTotalAmount();
      }
    });
  }

  updateExpenseList();
  updateTotalAmount();
}

function updateExpenseList() {
  if (!usingClientOnlyMode || !expenseList) return;
  expenseList.innerHTML = '';
  expenses.forEach((expense, index) => {
    const expenseItem = document.createElement('div');
    expenseItem.className = 'expense-item mb-2';
    expenseItem.innerHTML = `
      ${expense.name} - &#8377; ${expense.amount.toFixed(2)}
      <button class="btn btn-sm btn-primary" id="btn-delete" onclick="deleteExpense(${index})">X</button>
    `;
    expenseList.appendChild(expenseItem);
  });
}

function updateTotalAmount() {
  if (!usingClientOnlyMode || !totalAmount) return;
  const total = expenses.reduce((acc, expense) => acc + expense.amount, 0);
  totalAmount.textContent = total.toFixed(2);
}

function deleteExpense(index) {
  if (!usingClientOnlyMode) return;
  expenses.splice(index, 1);
  localStorage.setItem('expenses', JSON.stringify(expenses));
  updateExpenseList();
  updateTotalAmount();
}

document.addEventListener("DOMContentLoaded", () => {
  const today = new Date();
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  const dateEl = document.getElementById("current-date");
  if (dateEl) {
    dateEl.textContent = today.toLocaleDateString('en-IN', options);
  }
});