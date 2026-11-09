// Product list, selection, and upload (Vanilla, no new dependencies)

const AppState = {
    currentProductId: null,
    conversationHistory: [],
};

const Products = (() => {
    const productList = document.getElementById('productList');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadModal = document.getElementById('uploadModal');
    const closeModal = document.querySelector('#uploadModal .close');
    const submitUpload = document.getElementById('submitUpload');
    const productName = document.getElementById('productName');
    const productInfo = document.getElementById('productInfo');
    const addReviewModal = document.getElementById('addReviewModal');
    const closeAddReviewModal = document.getElementById('closeAddReviewModal');
    const submitAddReview = document.getElementById('submitAddReview');
    const addReviewMessage = document.getElementById('addReviewMessage');
    const addReviewModalTitle = document.getElementById('addReviewModalTitle');
    const reviewsModal = document.getElementById('reviewsModal');
    const closeReviewsModal = document.getElementById('closeReviewsModal');
    const reviewsModalTitle = document.getElementById('reviewsModalTitle');
    const reviewsModalMeta = document.getElementById('reviewsModalMeta');
    const reviewsModalList = document.getElementById('reviewsModalList');
    const reviewsModalMessage = document.getElementById('reviewsModalMessage');
    let addReviewProductId = null;
    let reviewsModalProductId = null;
    let reviewsModalProductName = null;

    function highlight(productId) {
        document.querySelectorAll('.product-item').forEach(item => {
            item.classList.toggle('active', item.dataset.productId === productId);
        });
    }

    function canDeleteProduct(product) {
        const user = Auth.getSession()?.user;
        if (!user) return false;
        if ((user.role || '').toLowerCase() === 'admin') return true;
        return Boolean(product.owner_id && product.owner_id === user.id);
    }

    function canDeleteReview(review) {
        const user = Auth.getSession()?.user;
        if (!user) return false;
        if ((user.role || '').toLowerCase() === 'admin') return true;
        return Boolean(review.author_user_id && review.author_user_id === user.id);
    }

    async function deleteProduct(product) {
        const label = product.name || product.product_id;
        if (!confirm(`Delete "${label}"? Reviews, embeddings, and chat for this product will also be removed.`)) {
            return;
        }
        try {
            await Auth.apiJson(`/api/products/${encodeURIComponent(product.product_id)}`, {
                method: 'DELETE',
            });
            if (AppState.currentProductId === product.product_id) {
                AppState.currentProductId = null;
                AppState.conversationHistory = [];
                productName.textContent = 'Select a product';
                productInfo.textContent = '';
                Chat.reset();
            }
            await load();
        } catch (error) {
            console.error('Delete failed:', error);
            alert('Delete failed: ' + error.message);
        }
    }

    async function load() {
        try {
            const response = await fetch(`${Auth.API_BASE}/api/products`);
            const data = await response.json();

            if (!data.products || data.products.length === 0) {
                productList.innerHTML = '<p class="empty-message">Upload a product</p>';
                return;
            }

            productList.innerHTML = '';
            data.products.forEach(product => {
                const item = document.createElement('div');
                item.className = 'product-item';
                item.dataset.productId = product.product_id;

                const imageHtml = product.image
                    ? `<img src="${product.image}" alt="${product.name}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px; margin-bottom: 5px;">`
                    : '';

                const deleteBtnHtml = canDeleteProduct(product)
                    ? '<button type="button" class="delete-product-btn danger">Delete product</button>'
                    : '';

                item.innerHTML = `
                    ${imageHtml}
                    <h3>${product.name}</h3>
                    <p>${product.reviews_count} reviews</p>
                    <div class="product-item-menu">
                        <button type="button" class="product-menu-btn" aria-label="Product options">...</button>
                        <div class="product-menu-dropdown">
                            <button type="button" class="view-reviews-btn">View reviews</button>
                            <button type="button" class="save-product-btn">Save to My List</button>
                            <button type="button" class="add-review-btn">Add review</button>
                            <button type="button" class="clear-chat-btn">Clear chat for this product</button>
                            ${deleteBtnHtml}
                        </div>
                    </div>
                `;

                const menuBtn = item.querySelector('.product-menu-btn');
                const dropdown = item.querySelector('.product-menu-dropdown');
                const viewReviewsBtn = item.querySelector('.view-reviews-btn');
                const saveBtn = item.querySelector('.save-product-btn');
                const addReviewBtn = item.querySelector('.add-review-btn');
                const clearBtn = item.querySelector('.clear-chat-btn');
                const deleteBtn = item.querySelector('.delete-product-btn');

                menuBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const wasOpen = dropdown.classList.contains('open');
                    closeAllProductMenus();
                    if (!wasOpen) {
                        dropdown.classList.add('open');
                        positionProductMenu(menuBtn, dropdown);
                    }
                });

                viewReviewsBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    closeAllProductMenus();
                    await openReviews(product.product_id, product.name);
                });

                saveBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    closeAllProductMenus();
                    await Saved.openForProduct(product.product_id);
                });

                addReviewBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    closeAllProductMenus();
                    openAddReview(product.product_id, product.name);
                });

                clearBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    closeAllProductMenus();
                    await Chat.clearHistory(product.product_id, product.name);
                });

                if (deleteBtn) {
                    deleteBtn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        closeAllProductMenus();
                        await deleteProduct(product);
                    });
                }

                item.addEventListener('click', () => select(product.product_id));
                productList.appendChild(item);
            });
        } catch (error) {
            console.error('Failed to load products:', error);
            Chat.showError('Unable to load product list.');
        }
    }

    function clearProductMenuPosition(dropdown) {
        dropdown.style.top = '';
        dropdown.style.left = '';
        dropdown.style.right = '';
    }

    function positionProductMenu(menuBtn, dropdown) {
        const rect = menuBtn.getBoundingClientRect();
        const menuWidth = Math.max(200, dropdown.offsetWidth || 200);
        const menuHeight = dropdown.offsetHeight || 180;
        const gap = 8;

        // Open to the left of "..." so the button stays clear of the menu panel
        let left = rect.left - menuWidth - gap;
        let top = rect.top;

        if (left < 8) {
            // Not enough room on the left — drop below the button instead
            left = Math.max(8, Math.min(rect.right - menuWidth, window.innerWidth - menuWidth - 8));
            top = rect.bottom + gap;
        }
        if (top + menuHeight > window.innerHeight - 8) {
            top = Math.max(8, window.innerHeight - menuHeight - 8);
        }

        dropdown.style.top = `${Math.round(top)}px`;
        dropdown.style.left = `${Math.round(left)}px`;
        dropdown.style.right = 'auto';
    }

    function closeAllProductMenus() {
        document.querySelectorAll('.product-menu-dropdown.open').forEach((el) => {
            el.classList.remove('open');
            clearProductMenuPosition(el);
        });
    }

    async function select(productId) {
        try {
            const response = await fetch(`${Auth.API_BASE}/api/products/${productId}`);
            const product = await response.json();

            AppState.currentProductId = productId;
            AppState.conversationHistory = [];

            productName.textContent = product.name;
            productInfo.textContent = `${product.reviews.length} reviews`;
            highlight(productId);

            await Chat.open(product);
            Saved.showForCurrent();
        } catch (error) {
            console.error('Failed to select product:', error);
            Chat.showError('Unable to load product information.');
        }
    }

    async function upload() {
        const name = document.getElementById('productNameInput').value.trim();
        const image = document.getElementById('productImage').value.trim();
        const description = document.getElementById('productDesc').value.trim();

        if (!name || !description) {
            alert('Please fill in name and description.');
            return;
        }

        try {
            const data = await Auth.apiJson('/api/products/upload', {
                method: 'POST',
                body: JSON.stringify({
                    name: name,
                    image: image || null,
                    description: description,
                }),
            });

            alert(`Product uploaded successfully!${data.product_id ? `\nID: ${data.product_id}` : ''}`);
            uploadModal.style.display = 'none';
            document.getElementById('productNameInput').value = '';
            document.getElementById('productImage').value = '';
            document.getElementById('productDesc').value = '';
            await load();
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Error during upload: ' + error.message);
        }
    }

    function openAddReview(productId, productLabel) {
        addReviewProductId = productId;
        addReviewModalTitle.textContent = `Add Review — ${productLabel || productId}`;
        document.getElementById('addReviewContent').value = '';
        document.getElementById('addReviewRating').value = '';
        document.getElementById('addReviewDate').value = '';
        addReviewMessage.textContent = '';
        addReviewModal.style.display = 'block';
    }

    function closeAddReview() {
        addReviewModal.style.display = 'none';
        addReviewProductId = null;
        addReviewMessage.textContent = '';
    }

    function closeReviews() {
        reviewsModal.style.display = 'none';
        reviewsModalProductId = null;
        reviewsModalProductName = null;
        reviewsModalMessage.textContent = '';
        reviewsModalList.innerHTML = '';
    }

    function renderReviewsList(reviews) {
        reviewsModalList.innerHTML = '';
        if (!reviews.length) {
            reviewsModalList.innerHTML = '<p class="empty-message">No reviews yet.</p>';
            return;
        }

        reviews.forEach((review) => {
            const card = document.createElement('div');
            card.className = 'review-card';

            const author = review.author_username || 'Anonymous';
            const parts = [author];
            if (review.rating !== null && review.rating !== undefined) {
                parts.push(`★ ${review.rating}`);
            }
            if (review.date) parts.push(review.date);

            const meta = document.createElement('div');
            meta.className = 'review-card-meta';
            meta.textContent = parts.join(' · ');

            const body = document.createElement('p');
            body.className = 'review-card-content';
            body.textContent = review.content || '';

            card.append(meta, body);

            if (canDeleteReview(review)) {
                const delBtn = document.createElement('button');
                delBtn.type = 'button';
                delBtn.className = 'review-delete-btn';
                delBtn.textContent = 'Delete';
                delBtn.addEventListener('click', async () => {
                    await deleteReview(review);
                });
                card.appendChild(delBtn);
            }

            reviewsModalList.appendChild(card);
        });
    }

    async function openReviews(productId, productLabel) {
        reviewsModalProductId = productId;
        reviewsModalProductName = productLabel || productId;
        reviewsModalTitle.textContent = `Reviews — ${reviewsModalProductName}`;
        reviewsModalMeta.textContent = 'Loading…';
        reviewsModalMessage.textContent = '';
        reviewsModalList.innerHTML = '';
        reviewsModal.style.display = 'block';

        try {
            const response = await fetch(
                `${Auth.API_BASE}/api/products/${encodeURIComponent(productId)}`
            );
            const product = await response.json();
            if (!response.ok) {
                throw new Error(product.detail || `Request failed (${response.status})`);
            }
            const reviews = product.reviews || [];
            reviewsModalMeta.textContent = `${reviews.length} review${reviews.length === 1 ? '' : 's'}`;
            renderReviewsList(reviews);
        } catch (error) {
            console.error('Failed to load reviews:', error);
            reviewsModalMeta.textContent = '';
            reviewsModalMessage.textContent = 'Error: ' + error.message;
        }
    }

    async function deleteReview(review) {
        if (!reviewsModalProductId || !review?.review_id) return;
        if (!confirm('Delete this review? Its embedding will also be removed.')) return;

        reviewsModalMessage.textContent = 'Deleting…';
        try {
            await Auth.apiJson(
                `/api/products/${encodeURIComponent(reviewsModalProductId)}/reviews/${encodeURIComponent(review.review_id)}`,
                { method: 'DELETE' }
            );
            await openReviews(reviewsModalProductId, reviewsModalProductName);
            await load();
            if (AppState.currentProductId === reviewsModalProductId) {
                await select(reviewsModalProductId);
            }
            reviewsModalMessage.textContent = 'Review deleted.';
        } catch (error) {
            console.error('Delete review failed:', error);
            reviewsModalMessage.textContent = 'Error: ' + error.message;
        }
    }

    async function submitReview() {
        if (!addReviewProductId) return;

        const content = document.getElementById('addReviewContent').value.trim();
        if (!content) {
            addReviewMessage.textContent = 'Review content is required.';
            return;
        }

        const ratingRaw = document.getElementById('addReviewRating').value.trim();
        const dateRaw = document.getElementById('addReviewDate').value.trim();
        const payload = {
            review_id: `r_${Date.now()}`,
            content: content,
            rating: ratingRaw === '' ? null : Number(ratingRaw),
            date: dateRaw || null,
        };

        if (payload.rating !== null && Number.isNaN(payload.rating)) {
            addReviewMessage.textContent = 'Rating must be a number.';
            return;
        }

        submitAddReview.disabled = true;
        addReviewMessage.textContent = 'Adding…';
        try {
            await Auth.apiJson(
                `/api/products/${encodeURIComponent(addReviewProductId)}/reviews`,
                {
                    method: 'POST',
                    body: JSON.stringify(payload),
                }
            );

            const productId = addReviewProductId;
            closeAddReview();
            await load();
            if (AppState.currentProductId === productId) {
                await select(productId);
            }
            alert('Review added.');
        } catch (error) {
            console.error('Add review failed:', error);
            addReviewMessage.textContent = 'Error: ' + error.message;
        } finally {
            submitAddReview.disabled = false;
        }
    }

    function resetList() {
        productList.innerHTML = '<p class="empty-message">Upload a product</p>';
        productName.textContent = 'Select a product';
        productInfo.textContent = '';
        document.querySelectorAll('.product-item').forEach(item => item.classList.remove('active'));
    }

    function bind() {
        uploadBtn.addEventListener('click', () => {
            uploadModal.style.display = 'block';
        });
        closeModal.addEventListener('click', () => {
            uploadModal.style.display = 'none';
        });
        closeAddReviewModal.addEventListener('click', closeAddReview);
        closeReviewsModal.addEventListener('click', closeReviews);
        submitAddReview.addEventListener('click', submitReview);
        productList.addEventListener('scroll', closeAllProductMenus);
        window.addEventListener('resize', closeAllProductMenus);
        window.addEventListener('click', (e) => {
            if (e.target === uploadModal) {
                uploadModal.style.display = 'none';
            }
            if (e.target === addReviewModal) {
                closeAddReview();
            }
            if (e.target === reviewsModal) {
                closeReviews();
            }
            if (!e.target.closest('.product-item-menu') && !e.target.closest('.product-menu-dropdown')) {
                closeAllProductMenus();
            }
        });
        submitUpload.addEventListener('click', upload);
    }

    return { load, select, bind, resetList };
})();
