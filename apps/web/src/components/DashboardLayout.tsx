import React, {useState, ReactNode} from 'react'

type Props = {
  filters?: ReactNode
  kpis?: ReactNode
  children?: ReactNode
}

export default function DashboardLayout({filters, kpis, children}: Props){
  const [collapsed, setCollapsed] = useState(false)

  const sidebarStyle: React.CSSProperties = {
    width: collapsed ? 56 : 280,
    transition: 'width 200ms ease',
    padding: collapsed ? 8 : 12,
    borderRight: '1px solid #e6e9ef',
    background: '#fafbfd',
    minHeight: '100vh',
  }

  const mainStyle: React.CSSProperties = { padding: 16, background: '#f7fafc', minHeight: '100vh' }

  const contentGridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(12, 1fr)',
    gap: 12,
  }

  const cardStyle: React.CSSProperties = {
    background: '#fff', border: '1px solid #e6e9ef', borderRadius: 8, padding: 12, boxShadow: '0 0 0 rgba(0,0,0,0)'
  }

  return (
    <div style={{display:'flex'}}>
      <aside style={sidebarStyle}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
          {!collapsed && <strong style={{fontSize:14}}>Filters</strong>}
          <button onClick={()=>setCollapsed(!collapsed)} style={{background:'transparent',border:0,cursor:'pointer'}}> {collapsed ? '▶' : '◀'} </button>
        </div>
        <div>
          {filters}
        </div>
      </aside>

      <main style={mainStyle} className="main-pane">
        <div style={contentGridStyle}>
          <div style={{gridColumn:'1 / -1'}}>
            <div style={cardStyle}>{children}</div>
          </div>
        </div>
      </main>
    </div>
  )
}
