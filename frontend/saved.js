// Saved products list and "Save to My List" modal

const Saved = (() => {
    const saveModal = document.getElementById('saveModal');
    const closeSaveModal = document.getElementById('closeSaveModal');
    const saveModalTitle = document.getElementById('saveModalTitle');
    const interestLevel = document.getElementById('interestLevel');
    const personalNote = document.getElementById('personalNote');
    const saveProductBtn = document.getElementById('saveProductBtn');
    const removeSavedBtn = document.getElementById('removeSavedBtn');
    const saveMessage = document.getElementById('saveMessage');
    const savedList = document.getElementById('savedList');
    const savedSection = document.getElementById('savedSection');
    const savedToggle = document.getElementById('savedToggle');
    const savedToggleLabel = document.getElementById('savedToggleLabel');

    let currentIsSaved = false;
    let modalProductId = null;
    let savedCount = 0;

    function setSaveMessage(text, isError = false) {
        saveMessage.textContent = text || '';
        saveMessage.classList.toggle('error', Boolean(isError && text));
    }

    function formatInterest(level) {
        if (level === 'interested') return 'Interested';
        if (level === 'maybe') return 'Maybe';
        if (level === 'not_for_me') return 'Not for me';
        return level || '';
    }

    function updateToggleLabel(count = savedCount) {
        savedCount = count;
        savedToggleLabel.textContent = `My Saved Products (${savedCount})`;
    }

    function setPanelOpen(open) {
        savedSection.classList.toggle('open', open);
        savedToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    function togglePanel() {
        setPanelOpen(!savedSection.classList.contains('open'));
    }

    function applySavedState(item) {
        if (item) {
            currentIsSaved = true;
            interestLevel.value = item.interest_level || 'interested';
            personalNote.value = item.personal_note || '';
            removeSavedBtn.classList.remove('hidden');
            saveProductBtn.textContent = 'Update Saved';
            saveModalTitle.textContent = 'Edit Saved Product';
        } else {
            currentIsSaved = false;
            interestLevel.value = 'interested';
            personalNote.value = '';
            removeSavedBtn.classList.add('hidden');
            saveProductBtn.textContent = 'Save to My List';
            saveModalTitle.textContent = 'Save to My List';
        }
    }

    function closeModal() {
        saveModal.style.display = 'none';
        setSaveMessage('');
        modalProductId = null;
    }

    async function openForProduct(productId) {
        if (!Auth.isLoggedIn()) {
            alert('Sign in to save products.');
            return;
        }
        if (!productId) return;

        modalProductId = productId;
        setSaveMessage('');
        try {
            const data = await Auth.apiJson(
                `/api/saved-products/${encodeURIComponent(productId)}`
            );
            applySavedState(data.item || null);
            setSaveMessage(
                currentIsSaved ? 'Already in your list — edit and save to update.' : ''
            );
            saveModal.style.display = 'block';
        } catch (e) {
            applySavedState(null);
            setSaveMessage(e.message, true);
            saveModal.style.display = 'block';
        }
    }

    async function loadList() {
        if (!Auth.isLoggedIn()) return;
        try {
            const data = await Auth.apiJson('/api/saved-products');
            const items = data.items || [];
            updateToggleLabel(items.length);
            savedList.innerHTML = '';
            if (items.length === 0) {
                const p = document.createElement('p');
                p.className = 'empty-message';
                p.textContent = 'No saved products yet';
                savedList.appendChild(p);
                return;
            }
            items.forEach(item => {
                const el = document.createElement('div');
                el.className = 'saved-item';
                el.dataset.productId = item.product_id;

                const title = document.createElement('h4');
                title.textContent = item.product_name || item.product_id;

                const meta = document.createElement('p');
                meta.textContent = formatInterest(item.interest_level);

                el.append(title, meta);
                if (item.personal_note) {
                    const note = document.createElement('p');
                    note.className = 'saved-note';
                    note.textContent = item.personal_note;
                    el.appendChild(note);
                }
                el.addEventListener('click', () => {
                    setPanelOpen(false);
                    Products.select(item.product_id);
                });
                savedList.appendChild(el);
            });
        } catch (e) {
            updateToggleLabel(0);
            savedList.innerHTML = '';
            const p = document.createElement('p');
            p.className = 'empty-message';
            p.textContent = `Unable to load saved list: ${e.message}`;
            savedList.appendChild(p);
        }
    }

    async function showForCurrent() {
        if (!Auth.isLoggedIn() || !AppState.currentProductId) {
            currentIsSaved = false;
            return;
        }
        try {
            const data = await Auth.apiJson(
                `/api/saved-products/${encodeURIComponent(AppState.currentProductId)}`
            );
            currentIsSaved = Boolean(data.item);
        } catch (e) {
            currentIsSaved = false;
        }
    }

    async function save() {
        if (!Auth.isLoggedIn() || !modalProductId) return;
        setSaveMessage('Saving...');
        try {
            await Auth.apiJson('/api/saved-products', {
                method: 'POST',
                body: JSON.stringify({
                    product_id: modalProductId,
                    interest_level: interestLevel.value,
                    personal_note: personalNote.value.trim(),
                }),
            });
            applySavedState({
                interest_level: interestLevel.value,
                personal_note: personalNote.value.trim(),
            });
            setSaveMessage('Saved to your list.');
            await loadList();
            closeModal();
        } catch (e) {
            setSaveMessage(e.message, true);
        }
    }

    async function remove() {
        if (!Auth.isLoggedIn() || !modalProductId) return;
        setSaveMessage('Removing...');
        try {
            await Auth.apiJson(
                `/api/saved-products/${encodeURIComponent(modalProductId)}`,
                { method: 'DELETE' }
            );
            applySavedState(null);
            await loadList();
            closeModal();
        } catch (e) {
            setSaveMessage(e.message, true);
        }
    }

    function reset() {
        currentIsSaved = false;
        modalProductId = null;
        closeModal();
        setPanelOpen(false);
        updateToggleLabel(0);
        interestLevel.value = 'interested';
        personalNote.value = '';
        removeSavedBtn.classList.add('hidden');
        saveProductBtn.textContent = 'Save to My List';
        saveModalTitle.textContent = 'Save to My List';
        setSaveMessage('');
        savedList.innerHTML = '<p class="empty-message">No saved products yet</p>';
    }

    function bind() {
        savedToggle.addEventListener('click', togglePanel);
        closeSaveModal.addEventListener('click', closeModal);
        saveProductBtn.addEventListener('click', save);
        removeSavedBtn.addEventListener('click', remove);
        saveModal.addEventListener('click', (e) => {
            if (e.target === saveModal) closeModal();
        });
    }

    return { loadList, showForCurrent, openForProduct, bind, reset };
})();
