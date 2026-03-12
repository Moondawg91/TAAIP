import React from 'react'
import PageFrame from './PageFrame'

type Props = {
  title?: string
  children?: React.ReactNode
}

export default function DashboardPageLayout({ title, children }: Props){
  return (
    <PageFrame>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {title ? <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}><h2 style={{ margin: 0 }}>{title}</h2></div> : null}
        <div style={{ width: '100%' }}>{children}</div>
      </div>
    </PageFrame>
  )
}
