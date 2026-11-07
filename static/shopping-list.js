
let productToRemove = null;

document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initShoppingPage();
    initFavorites();
    initProductModal();
});

// Dark mode
function initDarkMode() {
    const toggleBtn = document.getElementById('darkModeToggle');
    const savedMode = localStorage.getItem('darkMode');

    if (savedMode === 'enabled') {
        document.body.classList.add('dark-mode');
    }

    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', document.body.classList.contains('dark-mode') ? 'enabled' : 'disabled');
    });
}

// Favorites
function getFavorites() {
    try {
        return (JSON.parse(localStorage.getItem('favorites')) || []).map(id => String(id));
    } catch {
        return [];
    }
}

function saveFavorites(favorites) {
    localStorage.setItem('favorites', JSON.stringify(favorites));
}

function applyFavorites() {
    const favorites = getFavorites();

    document.querySelectorAll('.favoriteIcon').forEach(icon => {
        const productId = String(icon.dataset.id);
        const isFavorite = favorites.includes(productId);

        icon.classList.toggle('filled', isFavorite);
        icon.title = isFavorite ? 'Remove from favorites!' : 'Add to favorites!';
    });
}

function initFavorites() {
    applyFavorites();
}

// Shopping page
function initShoppingPage() {
    loadShoppingList();

    document.getElementById('exportBtn')?.addEventListener('click', exportList);
    document.getElementById('sendEmailBtn')?.addEventListener('click', sendEmail);

    document.addEventListener('click', handleClicks);
}

function loadShoppingList() {
    const container = document.getElementById('shoppingListContainer');
    if (!container) return;

    const list = getShoppingList();
    const ids = Object.keys(list);

    if (ids.length === 0) {
        container.innerHTML = '<p>Your shopping list is empty.</p>';
        return;
    }

    fetch(`/shopping-list-data/?ids=${ids.join(',')}&quantities=${encodeURIComponent(JSON.stringify(list))}`)
        .then(res => {
            if (!res.ok) throw new Error('Failed to load shopping list.');
            return res.json();
        })
        .then(data => {
            container.innerHTML = data.html;
            applyFavorites();
        })
        .catch(error => console.error('Error loading shopping list:', error));
}

function exportList() {
    const list = getShoppingList();
    const ids = Object.keys(list);

    if (ids.length === 0) {
        alert('Your shopping list is empty.');
        return;
    }

    window.location.href = `/export-shopping-list/?ids=${ids.join(',')}&quantities=${encodeURIComponent(JSON.stringify(list))}`;
}

function sendEmail() {
    const emailInput = document.getElementById('emailInput');
    const email = emailInput?.value.trim();

    if (!email) {
        alert('Please enter an email.');
        return;
    }

    const list = getShoppingList();
    const ids = Object.keys(list);

    fetch(`/email-shopping-list/?ids=${ids.join(',')}&quantities=${encodeURIComponent(JSON.stringify(list))}&email=${encodeURIComponent(email)}`)
        .then(res => {
            if (!res.ok) throw new Error('Failed to send shopping list.');
            return res.json();
        })
        .then(data => {
            const toastEl = document.getElementById('emailToast');
            const toastBody = document.getElementById('emailToastBody');

            if (!toastEl || !toastBody) return;

            if (data.success) {
                toastBody.textContent = 'Email sent successfully!';
                toastEl.classList.remove('text-bg-danger');
                toastEl.classList.add('text-bg-success');
            } else {
                toastBody.textContent = 'Error sending email.';
                toastEl.classList.remove('text-bg-success');
                toastEl.classList.add('text-bg-danger');
            }

            bootstrap.Toast.getOrCreateInstance(toastEl).show();
            bootstrap.Modal.getInstance(document.getElementById('emailModal'))?.hide();

            if (emailInput) emailInput.value = '';
        })
        .catch(error => console.error('Error sending shopping list:', error));
}

function handleClicks(e) {
    console.log('shopping-list.js handleClicks fired');
    const target = e.target instanceof Element ? e.target : e.target.parentElement;
    if (!target) return;

    // Match the behavior in favorites.js: remove the ID, save, and refresh the UI.
    const favIcon = target.closest('.favoriteIcon');

    if (favIcon) {
        console.log('Existing handler found heart:', favIcon.dataset.id);
        e.preventDefault();
        e.stopPropagation();

        const productId = String(favIcon.dataset.id);
        let favorites = getFavorites();

        if (favorites.includes(productId)) {
            favorites = favorites.filter(id => id !== productId);
        } else {
            favorites.push(productId);
        }

        saveFavorites(favorites);
        applyFavorites();
        return;
    }

    const remove = target.closest('.removeIcon');

    if (remove) {
        productToRemove = remove.dataset.id;
        bootstrap.Modal.getOrCreateInstance(document.getElementById('removeModal')).show();
        return;
    }

    if (target.closest('#confirmRemoveBtn')) {
        if (productToRemove !== null) {
            removeProduct(productToRemove);
        }
        return;
    }

    const inc = target.closest('.incrementIcon');

    if (inc) {
        updateQty(inc.dataset.id, 1);
        return;
    }

    const dec = target.closest('.decrementIcon');

    if (dec) {
        updateQty(dec.dataset.id, -1);
        return;
    }

    // Don't open the product modal when interacting with controls.
    if (target.closest('.shoppingListIcon, .divQuantity, .divFavorite, .divRemove')) return;

    const product = target.closest('.productItem');

    if (product) {
        openProductModal(product.dataset.id);
    }
}

// Shopping-list storage
function getShoppingList() {
    try {
        return JSON.parse(localStorage.getItem('shoppingList')) || {};
    } catch {
        return {};
    }
}

function saveShoppingList(list) {
    localStorage.setItem('shoppingList', JSON.stringify(list));
}

function updateQty(id, change) {
    const list = getShoppingList();

    list[id] = (list[id] || 0) + change;

    if (list[id] <= 0) {
        productToRemove = id;
        bootstrap.Modal.getOrCreateInstance(document.getElementById('removeModal')).show();
        return;
    }

    saveShoppingList(list);
    loadShoppingList();
}

function removeProduct(id) {
    const list = getShoppingList();
    delete list[id];

    saveShoppingList(list);

    bootstrap.Modal.getInstance(document.getElementById('removeModal'))?.hide();
    productToRemove = null;

    loadShoppingList();
}

// Product modal
function initProductModal() {
    // Product-card clicks are handled by handleClicks().
}

function openProductModal(id) {
    fetch(`/product/${id}/`)
        .then(res => {
            if (!res.ok) throw new Error('Failed to load product details.');
            return res.json();
        })
        .then(data => {
            const modalContent = document.getElementById('modalContent');
            const modalElement = document.getElementById('productModal');

            if (!modalContent || !modalElement) return;

            modalContent.innerHTML = data.html;
            bootstrap.Modal.getOrCreateInstance(modalElement).show();
        })
        .catch(error => console.error('Error loading product details:', error));
}
