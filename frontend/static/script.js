const API = '/api';

function getToken() {
    const match = document.cookie.match(/token=([^;]+)/);
    return match ? match[1] : null;
}

async function api(method, path, body = null) {
    const token = getToken();
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (token) opts.headers['Authorization'] = 'Bearer ' + token;
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API + path, opts);
    if (res.status === 401) { window.location.href = '/login'; return; }
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Ошибка запроса');
    }
    return res.status === 204 ? null : res.json();
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const group = tab.closest('.tabs').dataset.group;
            document.querySelectorAll(`.tab[data-group="${group}"]`).forEach(t => t.classList.remove('active'));
            document.querySelectorAll(`.tab-content[data-group="${group}"]`).forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.target).classList.add('active');
        });
    });
}

function statusBadge(status) {
    const map = {
        active: ['badge-active', 'Активен'],
        inactive: ['badge-inactive', 'Неактивен'],
        pending: ['badge-pending', 'Ожидает'],
        confirmed: ['badge-confirmed', 'Подтверждено'],
        cancelled: ['badge-cancelled', 'Отменено'],
        planned: ['badge-planned', 'Запланирована'],
        done: ['badge-done', 'Проведена'],
    };
    const [cls, label] = map[status] || ['badge-inactive', status];
    return `<span class="badge ${cls}">${label}</span>`;
}

function fmtDate(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.href && window.location.pathname.startsWith(new URL(link.href).pathname) && link.href !== '/') {
            link.classList.add('active');
        }
    });
});