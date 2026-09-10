const API_BASE = '';

async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(API_BASE + url, options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API error:', error);
        throw error;
    }
}
