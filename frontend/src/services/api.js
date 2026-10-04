/**
 * LOGIX AI - Centralized API Service
 * Connects directly to FastAPI backend running on http://localhost:8000
 */

const getBaseUrl = () => {
  if (typeof window !== 'undefined' && window.localStorage) {
    const saved = localStorage.getItem('logix_api_base');
    if (saved) return saved;
  }
  // Default to empty string for Vite proxy, or direct port 8000
  return 'http://localhost:8000';
};

export const setBaseUrl = (url) => {
  if (typeof window !== 'undefined' && window.localStorage) {
    localStorage.setItem('logix_api_base', url);
  }
};

export const getStoredBaseUrl = () => getBaseUrl();

/**
 * Robust fetch wrapper with error handling and timeouts
 */
async function request(endpoint, options = {}) {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...options.headers,
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout || 30000);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // use default HTTP error
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error('Request timed out. The server took too long to respond.');
    }
    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      throw new Error('Unable to connect to LOGIX AI backend. Please verify FastAPI is running on port 8000.');
    }
    throw err;
  }
}

/**
 * Health Check: GET /health
 */
export async function checkHealth() {
  try {
    const data = await request('/health', { timeout: 5000 });
    return { ok: data?.status === 'ok', data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

/**
 * Delay Prediction: POST /api/delay
 * @param {Object} record - Complete feature dictionary
 */
export async function predictDelay(record) {
  return await request('/api/delay', {
    method: 'POST',
    body: JSON.stringify({ record }),
  });
}

/**
 * Freight Matching: POST /api/match
 * @param {Array} loads - List of Load objects {load_id, route_id, departure_date, load_weight_pounds}
 * @param {Array<number>} availableTruckIds - List of truck IDs
 */
export async function matchFreight(loads, availableTruckIds) {
  return await request('/api/match', {
    method: 'POST',
    body: JSON.stringify({
      loads,
      available_truck_ids: availableTruckIds,
    }),
  });
}

/**
 * Get Logistics Overview Stats: GET /api/stats
 */
export async function getStats() {
  return await request('/api/stats');
}

/**
 * Get Real Sample Loads and Trucks: GET /api/sample-data
 */
export async function getSampleData() {
  return await request('/api/sample-data');
}

/**
 * Get Model Comparison & Metric Artifacts: GET /api/model-info
 */
export async function getModelInfo() {
  return await request('/api/model-info');
}

export default {
  checkHealth,
  predictDelay,
  matchFreight,
  getStats,
  getSampleData,
  getModelInfo,
  getStoredBaseUrl,
  setBaseUrl,
};
