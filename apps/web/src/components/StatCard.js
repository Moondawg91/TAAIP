/* © 2026 TAAIP. Copyright pending. */
import React from 'react';

export default function StatCard({title, children}){
  return (
    <div className="stat-card">
      <div className="stat-card-title">{title}</div>
      <div className="stat-card-body">{children}</div>
    </div>
  );
}
