import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import DualModeTabs from '../components/DualModeTabs'

function Wrapper({roles = []}:{roles?:string[]}){
  return (
    <MemoryRouter initialEntries={["/budget"]}>
      <Routes>
        <Route path="/budget" element={<DualModeTabs roles={roles} />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('DualModeTabs', () => {
  it('renders tabs and allows switching', () => {
    render(<Wrapper roles={[]} />)
    const exec = screen.getByRole('tab', { name: /Executive/i })
    const comp = screen.getByRole('tab', { name: /Comptroller/i })
    expect(exec).toBeInTheDocument()
    expect(comp).toBeInTheDocument()
    // click comptroller
    fireEvent.click(comp)
    // after click, the tab should be selected (aria-selected true)
    expect(comp).toHaveAttribute('aria-selected', 'true')
  })
})
