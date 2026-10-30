// Shared project persistence for designs.html + projects.html.
//
// IndexedDB is the source of truth — it has no ~5MB cap, so pasted images
// (stored as data URLs) can't silently push the store over quota and stop
// saves. localStorage is still written as a best-effort mirror; if that write
// fails, its `savedAt` stamp goes stale and init() prefers the IDB copy.
//
// Usage: `await ProjectStore.init()` once at boot, then load()/save() are
// synchronous. save() hands the object to IDB in the same tick (structured
// clone happens at put() time), so a save right before unload still lands.
window.ProjectStore = (() => {
  const KEY = 'opencraw-projects-v1';
  const DB_NAME = 'opencraw';
  const OS = 'kv';
  let cache = null;
  let db = null;
  let pending = null;   // store saved before the DB finished opening

  const empty = () => ({ currentId: null, projects: [] });

  function readLocal() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { console.warn('projects local load failed', e); }
    return null;
  }

  function openDB() {
    return new Promise((resolve, reject) => {
      if (!window.indexedDB) return reject(new Error('no indexedDB'));
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => req.result.createObjectStore(OS);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  function idbGet() {
    return new Promise((resolve, reject) => {
      const req = db.transaction(OS, 'readonly').objectStore(OS).get(KEY);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  }

  function idbPut(store) {
    try {
      const tx = db.transaction(OS, 'readwrite');
      tx.objectStore(OS).put(store, KEY);
      tx.onerror = () => console.warn('projects idb save failed', tx.error);
    } catch (e) { console.warn('projects idb save failed', e); }
  }

  async function init() {
    const local = readLocal();
    let stored = null;
    try {
      db = await openDB();
      stored = await idbGet();
    } catch (e) { console.warn('IndexedDB unavailable — using localStorage only', e); }
    // Newest snapshot wins. Legacy localStorage stores have no savedAt (0).
    const lt = (local && local.savedAt) || 0;
    const it = (stored && stored.savedAt) || 0;
    cache = (stored && it >= lt) ? stored : (local || stored || empty());
    if (pending) { cache = pending; pending = null; }
    // Seed IDB the first time (migrates an existing localStorage store).
    if (db && cache !== stored) idbPut(cache);
    return cache;
  }

  function load() {
    if (!cache) cache = readLocal() || empty();
    return cache;
  }

  function save(store) {
    store.savedAt = Date.now();
    cache = store;
    if (db) idbPut(store); else pending = store;
    try {
      localStorage.setItem(KEY, JSON.stringify(store));
    } catch (e) {
      // Over quota (big images). IDB has the data; the stale mirror loses on
      // the savedAt comparison in init().
    }
  }

  return { init, load, save };
})();
