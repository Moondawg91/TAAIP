import React from 'react'
import {Card, CardContent, Typography} from '@mui/material'
import {BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell} from 'recharts'

const COLORS = ['#2b7bff','#7b61ff','#00b07a','#ffb84d','#9aa0a6']

export default function CoverageCharts({counts}){
  // counts: {MK: n, MW: n, MO: n, SU: n, UNK: n}
  const categories = ['MK','MW','MO','SU','UNK']
  const total = categories.reduce((s,c)=> s + (counts && counts[c] ? counts[c] : 0), 0)
  const barData = [{name: 'Coverage', ...counts}]
  const pieData = categories.map((c,i)=> ({name:c, value: counts && counts[c] ? counts[c] : 0, color: COLORS[i]}))

  const hasAny = total > 0

  return (
    <>
      <Card variant="outlined">
        <CardContent>
          <Typography variant="subtitle1">ZIP Coverage by Category</Typography>
          {!hasAny ? <Typography variant="body2" color="text.secondary">No ZIP coverage loaded. Import Zip Codes in USAREC.xlsx.</Typography> : (
            <div style={{height:220}}>
              <ResponsiveContainer>
                <BarChart data={barData} layout="vertical">
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" />
                  <Tooltip />
                  <Legend />
                  {categories.map((c, i)=> (
                    <Bar key={c} dataKey={c} stackId="a" fill={COLORS[i]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card variant="outlined" sx={{mt:2}}>
        <CardContent>
          <Typography variant="subtitle1">Category Distribution</Typography>
          {!hasAny ? <Typography variant="body2" color="text.secondary">No ZIP coverage to display distribution.</Typography> : (
            <div style={{height:200}}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} label>
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </>
  )
}
