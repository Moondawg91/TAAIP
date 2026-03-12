export function pad(n:number){ return n<10 ? `0${n}` : String(n) }

export function getCurrentFY(d?:Date){
  const dt = d || new Date()
  const m = dt.getMonth() + 1
  const y = dt.getFullYear()
  // FY starts Oct 1 => Oct/Nov/Dec belong to next FY
  return (m >= 10) ? (y + 1) : y
}

export function getFYQuarter(d?:Date){
  const dt = d || new Date()
  const m = dt.getMonth() + 1
  const y = dt.getFullYear()
  if (m >= 10 && m <= 12){
    return { fy: y + 1, qtr: 1 as 1|2|3|4 }
  }
  if (m >= 1 && m <= 3){
    return { fy: y, qtr: 2 as 1|2|3|4 }
  }
  if (m >= 4 && m <= 6){
    return { fy: y, qtr: 3 as 1|2|3|4 }
  }
  return { fy: y, qtr: 4 as 1|2|3|4 }
}

export function getCurrentRsmMonth(d?:Date){
  const dt = d || new Date()
  const y = dt.getFullYear()
  const m = pad(dt.getMonth() + 1)
  return `${y}-${m}`
}

export function getQuarterStartMonth(fy:number, qtr:1|2|3|4){
  // Map FY and quarter to calendar month for the quarter start
  // FY Q1 -> Oct of previous calendar year
  if (qtr === 1) return `${fy - 1}-${pad(10)}`
  if (qtr === 2) return `${fy}-${pad(1)}`
  if (qtr === 3) return `${fy}-${pad(4)}`
  return `${fy}-${pad(7)}`
}

export function getQuarterMonths(fy:number, qtr:1|2|3|4){
  const start = getQuarterStartMonth(fy, qtr)
  const [yStr, mStr] = start.split('-')
  const y = Number(yStr)
  const m = Number(mStr)
  const months:string[] = []
  for(let i=0;i<3;i++){
    const mm = m + i
    const yy = y + Math.floor((mm-1)/12)
    const mmAdj = ((mm-1) % 12) + 1
    months.push(`${yy}-${pad(mmAdj)}`)
  }
  return months
}

export default {
  getCurrentFY,
  getFYQuarter,
  getCurrentRsmMonth,
  getQuarterStartMonth,
  getQuarterMonths,
}
