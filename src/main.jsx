import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import FrameTax from './FrameTax.jsx';

// Storage API polyfill (mirrors the Claude artifacts environment API)
window.storage = {
  get: async function(k) {
    var v = localStorage.getItem(k);
    return v ? { key: k, value: v } : null;
  },
  set: async function(k, v) {
    localStorage.setItem(k, String(v));
    return { key: k, value: v };
  },
  delete: async function(k) {
    localStorage.removeItem(k);
    return { key: k, deleted: true };
  },
  list: async function(p) {
    var keys = Object.keys(localStorage).filter(function(k) {
      return !p || k.startsWith(p);
    });
    return { keys: keys };
  }
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <FrameTax />
  </React.StrictMode>
);
