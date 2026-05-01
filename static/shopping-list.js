let productToRemove = null;

document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initShoppingPage();
    initFavorites();
    initProductModal();
});

// dark mode
function initDarkMode() {
    const toggleBtn = document.getElementById('darkModeToggle');
    const savedMode = localStorage.getItem('darkMode');

    if (savedMode === 'enabled') {
        document.body.classList.add('dark-mode');
    }

    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');

        localStorage.setItem(
            'darkMode',
            document.body.classList.contains('dark-mode') ? 'enabled' : 'disabled'
        );
    });
}

function getFavorites() {
    try {
        return JSON.parse(localStorage.getItem('favorites')) || [];
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
        const id = icon.dataset.id;

        if (favorites.includes(id)) {
            icon.classList.add('filled');
        } else {
            icon.classList.remove('filled');
        }
    });
}

function initFavorites() {
    applyFavorites();

    document.addEventListener('click', (e) => {
        const icon = e.target.closest('.favoriteIcon');
        if (!icon) return;

        const id = icon.dataset.id;
        let favorites = getFavorites();

        if (favorites.includes(id)) {
            favorites = favorites.filter(x => x !== id);
        } else {
            favorites.push(id);
        }

        saveFavorites(favorites);
        applyFavorites();
    });
}

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
        container.innerHTML = "<p>Your shopping list is empty.</p>";
        return;
    }

    fetch(`/shopping-list-data/?ids=${ids.join(',')}&quantities=${encodeURIComponent(JSON.stringify(list))}`)
        .then(res => res.json())
        .then(data => {
            container.innerHTML = data.html;
            applyFavorites();
        });
}

function exportList() {
    const list = getShoppingList();
    const ids = Object.keys(list);

    window.location.href =
        `/export-shopping-list/?ids=${ids.join(',')}&quantities=${encodeURIComponent(JSON.stringify(list))}`;
}

function sendEmail() {
    const email = document.getElementById('emailInput').value;

    if (!email) {
        alert("Please enter an email");
        return;
    }

    const list = getShoppingList();
    const ids = Object.keys(list);

    fetch(`/email-shopping-list/?ids=${ids.join(',')}&quantities=${encodeURIComponent(JSON.stringify(list))}&email=${email}`)
        .then(res => res.json())
        .then(data => {
            const toastEl = document.getElementById('emailToast');
            const toastBody = document.getElementById('emailToastBody');

            if (data.success) {
                toastBody.textContent = "Email sent successfully!";
                toastEl.classList.remove('text-bg-danger');
                toastEl.classList.add('text-bg-success');
            } else {
                toastBody.textContent = "Error sending email";
                toastEl.classList.remove('text-bg-success');
                toastEl.classList.add('text-bg-danger');
            }

            new bootstrap.Toast(toastEl).show();
            bootstrap.Modal.getInstance(document.getElementById('emailModal'))?.hide();
            document.getElementById('emailInput').value = '';
        });
}

function handleClicks(e) {

    const fav = e.target.closest('.favoriteIcon');
    if (fav) {
        toggleFavorite(fav);
        return;
    }

    const remove = e.target.closest('.removeIcon');
    if (remove) {
        productToRemove = remove.dataset.id;
        new bootstrap.Modal(document.getElementById('removeModal')).show();
        return;
    }

    if (e.target.id === 'confirmRemoveBtn') {
        removeProduct(productToRemove);
        return;
    }

    const inc = e.target.closest('.incrementIcon');
    if (inc) {
        updateQty(inc.dataset.id, +1);
        return;
    }

    const dec = e.target.closest('.decrementIcon');
    if (dec) {
        updateQty(dec.dataset.id, -1);
        return;
    }

    if (
        e.target.closest('.favoriteIcon') ||
        e.target.closest('.shoppingListIcon') ||
        e.target.closest('.removeIcon') ||
        e.target.closest('.divQuantity') ||
        e.target.closest('.divFavorite') ||
        e.target.closest('.divRemove')
    ) return;

    const product = e.target.closest('.productItem');
    if (product) {
        fetch(`/product/${product.dataset.id}/`)
            .then(res => res.json())
            .then(data => {
                document.getElementById('modalContent').innerHTML = data.html;
                new bootstrap.Modal(document.getElementById('productModal')).show();
            });
    }
}

function getShoppingList() {
    return JSON.parse(localStorage.getItem('shoppingList')) || {};
}

function saveShoppingList(list) {
    localStorage.setItem('shoppingList', JSON.stringify(list));
}

function updateQty(id, change) {
    let list = getShoppingList();

    list[id] = (list[id] || 0) + change;

    if (list[id] <= 0) {
        productToRemove = id;
        new bootstrap.Modal(document.getElementById('removeModal')).show();
        return;
    }

    saveShoppingList(list);
    loadShoppingList();
}

function removeProduct(id) {
    let list = getShoppingList();
    delete list[id];

    saveShoppingList(list);

    bootstrap.Modal.getInstance(document.getElementById('removeModal'))?.hide();
    loadShoppingList();
}

function toggleFavorite(icon) {
    const id = icon.dataset.id;
    let favorites = getFavorites();

    if (favorites.includes(id)) {
        favorites = favorites.filter(x => x !== id);
        icon.classList.remove('filled');
    } else {
        favorites.push(id);
        icon.classList.add('filled');
    }

    saveFavorites(favorites);
}

function initProductModal() {
    document.addEventListener('click', (e) => {
        if (
            e.target.closest('.favoriteIcon') ||
            e.target.closest('.shoppingListIcon') ||
            e.target.closest('.divFavorite') ||
            e.target.closest('.divShoppingList') ||
            e.target.closest('.discountBtn')
        ) {
            return;
        }

        const product = e.target.closest('.productItem');
        if (!product) return;

        const id = product.dataset.id;

        fetch(`/product/${id}/`)
            .then(r => r.json())
            .then(data => {
                document.getElementById('modalContent').innerHTML = data.html;

                new bootstrap.Modal(
                    document.getElementById('productModal')
                ).show();
            });
    });
}