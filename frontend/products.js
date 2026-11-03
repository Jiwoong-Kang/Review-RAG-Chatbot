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
    let addReviewProductId = null;

    function highlight(productId) {
        document.querySelectorAll('.product-item').forEach(item => {
            item.classList.toggle('active', item.dataset.productId === productId);
        });
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

                item.innerHTML = `
                    ${imageHtml}
                    <h3>${product.name}</h3>
                    <p>${product.reviews_count} reviews</p>
                    <div class="product-item-menu">
                        <button type="button" class="product-menu-btn" aria-label="Product options">...</button>
                        <div class="product-menu-dropdown">
                            <button type="button" class="save-product-btn">Save to My List</button>
                            <button type="button" class="add-review-btn">Add review</button>
                            <button type="button" class="clear-chat-btn">Clear chat for this product</button>
                        </div>
                    </div>
                `;

                const menuBtn = item.querySelector('.product-menu-btn');
                const dropdown = item.querySelector('.product-menu-dropdown');
                const saveBtn = item.querySelector('.save-product-btn');
                const addReviewBtn = item.querySelector('.add-review-btn');
                const clearBtn = item.querySelector('.clear-chat-btn');

                menuBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const wasOpen = dropdown.classList.contains('open');
                    closeAllProductMenus();
                    if (!wasOpen) dropdown.classList.add('open');
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

                item.addEventListener('click', () => select(product.product_id));
                productList.appendChild(item);
            });
        } catch (error) {
            console.error('Failed to load products:', error);
            Chat.showError('Unable to load product list.');
        }
    }

    function closeAllProductMenus() {
        document.querySelectorAll('.product-menu-dropdown.open').forEach((el) => {
            el.classList.remove('open');
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
        const productId = document.getElementById('productId').value.trim();
        const name = document.getElementById('productNameInput').value.trim();
        const image = document.getElementById('productImage').value.trim();
        const description = document.getElementById('productDesc').value.trim();
        const reviewsText = document.getElementById('reviewsInput').value.trim();

        if (!productId || !name || !description) {
            alert('Please fill in all required fields.');
            return;
        }

        let reviews = [];
        if (reviewsText) {
            try {
                reviews = JSON.parse(reviewsText);
            } catch (error) {
                alert('Invalid JSON format for reviews.');
                return;
            }
        }

        try {
            const response = await fetch(`${Auth.API_BASE}/api/products/upload`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: productId,
                    name: name,
                    image: image || null,
                    description: description,
                    reviews: reviews,
                }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                alert('Product uploaded successfully!');
                uploadModal.style.display = 'none';
                document.getElementById('productId').value = '';
                document.getElementById('productNameInput').value = '';
                document.getElementById('productImage').value = '';
                document.getElementById('productDesc').value = '';
                document.getElementById('reviewsInput').value = '';
                await load();
            } else {
                alert('Upload failed: ' + (data.detail || 'Unknown error'));
            }
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
        submitAddReview.addEventListener('click', submitReview);
        window.addEventListener('click', (e) => {
            if (e.target === uploadModal) {
                uploadModal.style.display = 'none';
            }
            if (e.target === addReviewModal) {
                closeAddReview();
            }
            if (!e.target.closest('.product-item-menu')) {
                closeAllProductMenus();
            }
        });
        submitUpload.addEventListener('click', upload);
    }

    return { load, select, bind, resetList };
})();
