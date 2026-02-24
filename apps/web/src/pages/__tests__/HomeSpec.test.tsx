import React from 'react'
import { render, screen } from '@testing-library/react'
import HomePage from '../HomePage'

test('HomeSpec: key headings present', ()=>{
  render(<HomePage />)
  expect(screen.getByText(/Strategic Flash Feed/i)).toBeInTheDocument()
  expect(screen.getByText(/Reference Rails/i)).toBeInTheDocument()
})
