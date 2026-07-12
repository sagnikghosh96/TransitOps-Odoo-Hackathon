import React from "react";

export default function Modal({ title, children, onClose }) {
  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-card">
        <div className="modal-title">{title}</div>
        {children}
      </div>
    </div>
  );
}