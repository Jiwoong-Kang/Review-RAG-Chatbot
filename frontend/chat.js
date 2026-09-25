// Chat, history restore, and citation rendering

const Chat = (() => {
    const chatContainer = document.getElementById('chatContainer');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');

    function setInputEnabled(enabled) {
        messageInput.disabled = !enabled;
        sendBtn.disabled = !enabled;
        sendBtn.textContent = enabled ? 'Send' : 'Sending...';
        if (enabled) messageInput.focus();
    }

    function renderAnswerText(content) {
        const wrapper = document.createElement('div');
        wrapper.className = 'answer-text';

        String(content).split(/(\[\d+\])/).forEach(part => {
            const match = part.match(/^\[(\d+)\]$/);
            if (match) {
                const marker = document.createElement('sup');
                marker.className = 'citation-marker';
                marker.dataset.marker = match[1];
                marker.textContent = part;
                marker.title = `Show review ${match[1]}`;
                wrapper.appendChild(marker);
            } else if (part) {
                wrapper.appendChild(document.createTextNode(part));
            }
        });

        return wrapper;
    }

    function renderSources(sources) {
        const details = document.createElement('details');
        details.className = 'sources';

        const summary = document.createElement('summary');
        summary.textContent = `Sources (${sources.length} review${sources.length === 1 ? '' : 's'})`;
        details.appendChild(summary);

        sources.forEach(source => {
            const card = document.createElement('div');
            card.className = 'source-card';
            card.dataset.marker = source.marker;

            const parts = [`[${source.marker}]`, source.review_id];
            if (source.rating !== null && source.rating !== undefined) parts.push(`★ ${source.rating}`);
            if (source.date) parts.push(source.date);

            const meta = document.createElement('div');
            meta.className = 'source-meta';
            meta.textContent = parts.join(' · ');

            const quote = document.createElement('p');
            quote.className = 'source-content';
            quote.textContent = source.content;

            card.append(meta, quote);
            details.appendChild(card);
        });

        return details;
    }

    function linkCitations(contentDiv) {
        const details = contentDiv.querySelector('.sources');

        contentDiv.querySelectorAll('.citation-marker').forEach(marker => {
            marker.addEventListener('click', () => {
                const card = details.querySelector(`.source-card[data-marker="${marker.dataset.marker}"]`);
                if (!card) return;

                details.open = true;
                details.querySelectorAll('.source-card').forEach(c => c.classList.remove('highlighted'));
                card.classList.add('highlighted');
                card.scrollIntoView({ block: 'nearest' });
            });
        });
    }

    function addMessage(content, role, options = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        if (options.isError) contentDiv.classList.add('error');

        if (options.insufficientEvidence) {
            const notice = document.createElement('div');
            notice.className = 'evidence-notice';
            notice.textContent = '⚠️ Not enough evidence in the reviews';
            contentDiv.appendChild(notice);
        }

        contentDiv.appendChild(renderAnswerText(content));

        const sources = options.sources || [];
        if (sources.length > 0) {
            contentDiv.appendChild(renderSources(sources));
            linkCitations(contentDiv);
        }

        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function showError(message) {
        addMessage(message, 'assistant', { isError: true });
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.id = id;
        typingDiv.className = 'message assistant';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        chatContainer.appendChild(typingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const element = document.getElementById(id);
        if (element) element.remove();
    }

    function reset() {
        AppState.currentProductId = null;
        AppState.conversationHistory = [];
        setInputEnabled(false);
        sendBtn.disabled = true;
        messageInput.disabled = true;
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>👋 Welcome!</h2>
                <p>Select a product and ask any questions.</p>
                <p>We'll answer based on actual user reviews.</p>
            </div>
        `;
    }

    async function restoreHistory(productId) {
        if (!Auth.isLoggedIn()) return;
        try {
            const data = await Auth.apiJson(`/api/chat/history/${encodeURIComponent(productId)}`);
            const messages = data.messages || [];
            if (messages.length === 0) return;

            AppState.conversationHistory = [];
            messages.forEach(msg => {
                addMessage(msg.content, msg.role, {
                    sources: msg.sources || [],
                    insufficientEvidence: Boolean(msg.insufficient_evidence),
                });
                AppState.conversationHistory.push({
                    role: msg.role,
                    content: msg.role === 'assistant'
                        ? String(msg.content || '').replace(/\[\d+\]/g, '')
                        : msg.content,
                });
            });
        } catch (e) {
            console.warn('Could not load chat history:', e.message);
        }
    }

    async function open(product) {
        chatContainer.innerHTML = '';
        const welcome = document.createElement('div');
        welcome.className = 'message assistant';
        welcome.innerHTML = `
            <div class="message-content">
                Hello! Ask me anything about ${product.name}. 
                I'll answer based on ${product.reviews.length} actual user reviews. 😊
            </div>
        `;
        chatContainer.appendChild(welcome);

        await restoreHistory(product.id || AppState.currentProductId);
        setInputEnabled(true);
    }

    async function send() {
        const message = messageInput.value.trim();
        if (!message || !AppState.currentProductId) return;

        addMessage(message, 'user');
        messageInput.value = '';

        AppState.conversationHistory.push({
            role: 'user',
            content: message,
        });

        const typingId = showTypingIndicator();
        setInputEnabled(false);

        try {
            const data = await Auth.apiJson('/api/chat', {
                method: 'POST',
                body: JSON.stringify({
                    product_id: AppState.currentProductId,
                    message: message,
                    conversation_history: AppState.conversationHistory,
                }),
            });

            removeTypingIndicator(typingId);

            addMessage(data.response, 'assistant', {
                sources: data.sources,
                insufficientEvidence: data.insufficient_evidence,
            });

            AppState.conversationHistory.push({
                role: 'assistant',
                content: data.response.replace(/\[\d+\]/g, ''),
            });
        } catch (error) {
            removeTypingIndicator(typingId);
            console.error('Failed to send message:', error);
            addMessage(`Sorry, unable to generate a response. ${error.message}`, 'assistant', { isError: true });
        } finally {
            setInputEnabled(true);
        }
    }

    async function clearHistory(productId, productName) {
        if (!Auth.isLoggedIn()) {
            alert('Sign in to manage chat history.');
            return;
        }
        const label = productName || 'this product';
        const ok = window.confirm(
            `Clear all chat history for "${label}"?\nThis cannot be undone.`
        );
        if (!ok) return;

        try {
            await Auth.apiJson(`/api/chat/history/${encodeURIComponent(productId)}`, {
                method: 'DELETE',
            });

            if (AppState.currentProductId === productId) {
                AppState.conversationHistory = [];
                chatContainer.innerHTML = '';
                const welcome = document.createElement('div');
                welcome.className = 'message assistant';
                welcome.innerHTML = `
                    <div class="message-content">
                        Chat history cleared. Ask me anything about ${label}.
                    </div>
                `;
                chatContainer.appendChild(welcome);
                setInputEnabled(true);
            }
        } catch (error) {
            console.error('Failed to clear chat history:', error);
            alert('Unable to clear chat history: ' + error.message);
        }
    }

    function bind() {
        sendBtn.addEventListener('click', send);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
            }
        });
    }

    return { open, send, reset, bind, showError, clearHistory };
})();
