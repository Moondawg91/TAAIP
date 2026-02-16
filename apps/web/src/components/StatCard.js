/* © 2025 Maroon Moon, LLC. All rights reserved. */
import React from 'react';

export default function StatCard({title, children}){
  return (
    <div className="stat-card">
      <div className="stat-card-title">{title}</div>
      <div className="stat-card-body">{children}</div>
    </div>
  );
}
