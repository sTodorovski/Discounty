document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initSearch();
    initFavorites();
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

// favorites
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

// searching
function initSearch() {
    const input = document.getElementById('searchInput');
    const resultsContainer = document.getElementById('searchResults');
    const sortSelect = document.querySelector("select[name='sort']");
    const marketSelect = document.querySelector("select[name='market']");
    const categorySelect = document.getElementById('categories');

    if (!input || !resultsContainer) return;

    let timeout;
    let page = 1;
    let loading = false;
    let hasNext = true;

    let query = '';
    let sort = sortSelect?.value || '';
    let market = marketSelect?.value || '';
    let discount = '';

    function load(reset = false, updateCategories = false) {
        if (loading || !hasNext) return;
        loading = true;

        fetch(`/ajax/search-products/?search=${encodeURIComponent(query)}&page=${page}&sort=${sort}&market=${market}&discount=${discount}&category=${encodeURIComponent(categorySelect ? categorySelect.value : '')}`)
            .then(r => r.json())
            .then(data => {
                resultsContainer.innerHTML = reset
                    ? data.html
                    : resultsContainer.innerHTML + data.html;

                applyFavorites();
                applyShoppingListIcons();

                if (updateCategories && categorySelect && data.categories) {
                    categorySelect.innerHTML = '<option value="">All categories</option>';

                    data.categories.forEach(description => {
                        const option = document.createElement('option');
                        option.value = description;
                        option.textContent = description;
                        categorySelect.appendChild(option);
                    });
                }

                hasNext = data.has_next;
                loading = false;
            });
    }

    input.addEventListener('input', () => {
        clearTimeout(timeout);

        timeout = setTimeout(() => {
            query = input.value;
            page = 1;
            hasNext = true;
            load(true);
        }, 300);
    });

    sortSelect?.addEventListener('change', () => {
        sort = sortSelect.value;
        page = 1;
        hasNext = true;
        load(true);
    });

    marketSelect?.addEventListener('change', () => {
        market = marketSelect.value;

        if (categorySelect) {
            categorySelect.value = '';
        }

        page = 1;
        hasNext = true;
        load(true, true);
    });

    if (categorySelect) {
        categorySelect.addEventListener('change', () => {
            page = 1;
            hasNext = true;
            load(true);
        });
    }

    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.discountBtn');
        if (!btn) return;

        discount = discount === btn.dataset.discount ? '' : btn.dataset.discount;
        page = 1;
        hasNext = true;

        document.querySelectorAll('.discountBtn').forEach(b => b.classList.remove('active'));
        if (discount) btn.classList.add('active');

        load(true);
    });

    window.addEventListener('scroll', () => {
        if (loading || !hasNext) return;

        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
            page++;
            load(false);
        }
    });

    load(true);
}

// modal
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