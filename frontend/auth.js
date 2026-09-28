// Auth gate + session helpers (loaded before app.js)
const API_BASE = 'http://localhost:8000';
const AUTH_STORAGE_KEY = 'reviewer_auth';

const Auth = (() => {
    let session = null; // { access_token, refresh_token, user: {id, username, name} }
    let onAuthenticated = null;
    let onSignedOut = null;
    let mode = 'signin'; // 'signin' | 'signup'

    const loginView = () => document.getElementById('loginView');
    const appView = () => document.getElementById('appView');
    const authMessage = () => document.getElementById('authMessage');
    const authUserLabel = () => document.getElementById('authUserLabel');

    function setMessage(text, isError = false) {
        const el = authMessage();
        if (!el) return;
        el.textContent = text || '';
        el.classList.toggle('error', Boolean(isError && text));
    }

    function restoreSession() {
        try {
            const raw = localStorage.getItem(AUTH_STORAGE_KEY);
            session = raw ? JSON.parse(raw) : null;
        } catch (e) {
            session = null;
            localStorage.removeItem(AUTH_STORAGE_KEY);
        }
        return session;
    }

    function persistSession(next) {
        session = next;
        if (session) {
            localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
        } else {
            localStorage.removeItem(AUTH_STORAGE_KEY);
        }
    }

    function getSession() {
        return session;
    }

    function isLoggedIn() {
        return Boolean(session?.access_token && session?.user);
    }

    function authHeaders() {
        if (!session?.access_token) return {};
        return { Authorization: `Bearer ${session.access_token}` };
    }

    async function apiJson(path, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
            ...authHeaders(),
        };
        const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
        let data = null;
        try {
            data = await response.json();
        } catch (e) {
            data = null;
        }
        if (!response.ok) {
            const detail = data?.detail;
            const message = typeof detail === 'string'
                ? detail
                : (Array.isArray(detail) ? detail.map(d => d.msg).join(', ') : `Request failed (${response.status})`);
            throw new Error(message);
        }
        return data;
    }

    function showLogin() {
        loginView()?.classList.remove('hidden');
        appView()?.classList.add('hidden');
    }

    function showApp() {
        loginView()?.classList.add('hidden');
        appView()?.classList.remove('hidden');
        const label = authUserLabel();
        if (label && session?.user) {
            const name = session.user.name || session.user.username || '';
            const username = session.user.username || '';
            label.textContent = username ? `${name} (@${username})` : name;
        }
    }

    async function enterApp() {
        showApp();
        if (typeof onAuthenticated !== 'function') return;
        try {
            await onAuthenticated(session);
        } catch (e) {
            console.error('App failed to start after login:', e);
            setMessage(`Signed in, but the app failed to load: ${e.message}`, true);
        }
    }

    async function refreshMe() {
        if (!session?.access_token) return false;
        try {
            const data = await apiJson('/api/auth/me');
            session.user = data.user;
            persistSession(session);
            return true;
        } catch (e) {
            console.warn('Session expired:', e.message);
            persistSession(null);
            return false;
        }
    }

    function setMode(next) {
        mode = next;
        const signInFields = document.getElementById('signInFields');
        const signUpFields = document.getElementById('signUpFields');
        const tabSignIn = document.getElementById('tabSignIn');
        const tabSignUp = document.getElementById('tabSignUp');
        const isSignIn = mode === 'signin';

        // Use class only — avoid fighting .hidden { display:none !important }
        if (signInFields) {
            signInFields.classList.toggle('hidden', !isSignIn);
            signInFields.style.removeProperty('display');
        }
        if (signUpFields) {
            signUpFields.classList.toggle('hidden', isSignIn);
            signUpFields.style.removeProperty('display');
        }
        tabSignIn?.classList.toggle('active', isSignIn);
        tabSignUp?.classList.toggle('active', !isSignIn);
        setMessage(isSignIn ? '' : 'Fill in name, username (kang123 style), password (6+), then Create Account.');
        if (!isSignIn) {
            document.getElementById('signUpName')?.focus();
        }
    }

    function showSignIn() {
        setMode('signin');
    }

    function showSignUp() {
        setMode('signup');
    }

    function friendlyAuthError(message) {
        const msg = String(message || '');
        const lower = msg.toLowerCase();
        if (lower.includes('email not confirmed') || lower.includes('confirm email')) {
            return msg;
        }
        if (lower.includes('already') || lower.includes('taken')) {
            return 'That username is already taken. Try another ID, or Sign In.';
        }
        if (lower.includes('letters, numbers') || lower.includes('username must')) {
            return 'Username must be 3–30 characters using only letters, numbers, and underscore. Example: kang123 (not an email).';
        }
        if (lower.includes('at least 6') || lower.includes('string_too_short')) {
            return 'Password must be at least 6 characters.';
        }
        if (lower.includes('invalid')) {
            return 'Wrong username or password.';
        }
        return msg || 'Sign up failed.';
    }

    async function signUp() {
        // Ensure signup fields are visible even if user clicked from Sign In screen
        if (mode !== 'signup') {
            setMode('signup');
        }
        const name = document.getElementById('signUpName')?.value.trim() || '';
        const username = document.getElementById('signUpUsername')?.value.trim() || '';
        const password = document.getElementById('signUpPassword')?.value || '';
        if (!name || !username || password.length < 6) {
            const msg = 'Enter name, username (e.g. kang123), and a password of at least 6 characters.';
            setMessage(msg, true);
            alert(msg);
            return;
        }
        if (!/^[a-zA-Z0-9_]{3,30}$/.test(username)) {
            const msg = 'Username must be 3–30 letters/numbers/underscore only (not an email).';
            setMessage(msg, true);
            alert(msg);
            return;
        }
        setMessage('Creating account...');
        try {
            const data = await apiJson('/api/auth/signup', {
                method: 'POST',
                body: JSON.stringify({ name, username, password }),
            });
            if (!data.access_token) {
                const msg = data.message || 'Sign up did not return a session.';
                setMessage(msg, true);
                alert(msg);
                return;
            }
            persistSession({
                access_token: data.access_token,
                refresh_token: data.refresh_token,
                user: data.user,
            });
            document.getElementById('signUpPassword').value = '';
            setMessage('Account created. Loading...');
            await enterApp();
        } catch (e) {
            const msg = friendlyAuthError(e.message);
            setMessage(msg, true);
            alert(msg);
        }
    }

    async function signIn() {
        if (mode !== 'signin') {
            setMode('signin');
        }
        const username = document.getElementById('signInUsername')?.value.trim() || '';
        const password = document.getElementById('signInPassword')?.value || '';
        if (!username || !password) {
            const msg = 'Enter username and password.';
            setMessage(msg, true);
            alert(msg);
            return;
        }
        setMessage('Signing in...');
        try {
            const data = await apiJson('/api/auth/signin', {
                method: 'POST',
                body: JSON.stringify({ username, password }),
            });
            persistSession({
                access_token: data.access_token,
                refresh_token: data.refresh_token,
                user: data.user,
            });
            document.getElementById('signInPassword').value = '';
            setMessage('');
            await enterApp();
        } catch (e) {
            const msg = friendlyAuthError(e.message);
            setMessage(msg, true);
            alert(msg);
        }
    }

    async function signOut() {
        try {
            if (session?.access_token) {
                await apiJson('/api/auth/signout', { method: 'POST' });
            }
        } catch (e) {
            console.warn('Sign out API failed:', e.message);
        }
        persistSession(null);
        setMode('signin');
        setMessage('Signed out. Sign in to continue.');
        showLogin();
        if (typeof onSignedOut === 'function') {
            onSignedOut();
        }
    }

    function bindUi() {
        document.getElementById('tabSignIn')?.addEventListener('click', () => setMode('signin'));
        document.getElementById('tabSignUp')?.addEventListener('click', () => setMode('signup'));
        document.getElementById('signInPassword')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                signIn();
            }
        });
        document.getElementById('signUpPassword')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                signUp();
            }
        });
    }

    async function bootstrap(callbacks = {}) {
        onAuthenticated = callbacks.onAuthenticated || null;
        onSignedOut = callbacks.onSignedOut || null;
        bindUi();
        setMode('signin');
        restoreSession();

        if (isLoggedIn()) {
            const ok = await refreshMe();
            if (ok) {
                await enterApp();
                return;
            }
        }

        showLogin();
        setMessage('');
    }

    return {
        API_BASE,
        apiJson,
        authHeaders,
        getSession,
        isLoggedIn,
        bootstrap,
        signOut,
        showSignIn,
        showSignUp,
        signIn,
        signUp,
    };
})();
