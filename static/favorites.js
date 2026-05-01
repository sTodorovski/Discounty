document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initFavoritesPage();
    initShoppingList();
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

function initFavoritesPage() {
    loadFavorites();

    document.addEventListener('click', (e) => {

        const favIcon = e.target.closest('.favoriteIcon');
        if (favIcon) {
            const productId = favIcon.dataset.id;
            let favorites = getFavorites();

            favorites = favorites.filter(id => id !== productId);
            saveFavorites(favorites);

            loadFavorites();
            return;
        }
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

function loadFavorites() {
    const favorites = getFavorites();
    const container = document.getElementById('favoritesResults');

    if (!container) return;

    if (favorites.length === 0) {
        container.innerHTML = "<p>No favorites yet.</p>";
        return;
    }

    fetch(`/favorites-data/?ids=${favorites.join(",")}`)
        .then(r => r.json())
        .then(data => {
            container.innerHTML = data.html;

            applyFavorites();
            applyShoppingListIcons();
        });
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

// shopping list
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

function applyShoppingListIcons() {
    const list = getShoppingList();

    document.querySelectorAll('.shoppingListIcon').forEach(icon => {
        const id = icon.dataset.id;

        if (list[id] > 0) {
            icon.classList.add('filled');
        } else {
            icon.classList.remove('filled');
        }
    });
}

function initShoppingList() {
    applyShoppingListIcons();

    document.addEventListener('click', (e) => {
        const icon = e.target.closest('.shoppingListIcon');
        if (icon) {
            const productId = icon.dataset.id;

            fetch(`/shopping-list/add/${productId}/`)
                .then(r => r.json())
                .then(data => {
                    document.getElementById('shoppingListContent').innerHTML = data.html;

                    const modal = new bootstrap.Modal(
                        document.getElementById('shoppingListModal')
                    );
                    modal.show();
                });

            return;
        }

        if (e.target.id === 'addToListBtn') {
            const productId = e.target.dataset.id;
            const qty = parseInt(document.getElementById('quantityInput')?.value || 1);

            let list = getShoppingList();
            list[productId] = (list[productId] || 0) + qty;

            saveShoppingList(list);
            applyShoppingListIcons();

            const modalEl = document.getElementById('shoppingListModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
    });
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