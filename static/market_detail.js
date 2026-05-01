document.addEventListener('DOMContentLoaded', () => {
    initCalendar();
    initDarkMode();
    initFavorites();
    initShoppingList();
    initProductModal();
    applyFavorites();
    applyShoppingListIcons();
});

// kalendar
function initCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    const marketId = window.location.pathname.split('/')[2];

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',

        events: `/market/${marketId}/events/`,

        eventContent: () => ({ html: '' }),

        eventDidMount: function(info) {
            info.el.title = info.event.title;
        },

        dateClick: function(info) {
            window.location.href = `?date=${info.dateStr}`;
        },

        eventClick: function(info) {
            window.location.href = `?start=${info.event.startStr}&end=${info.event.endStr}`;
        }
    });

    calendar.render();
}

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