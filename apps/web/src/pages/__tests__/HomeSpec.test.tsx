import React from 'react'
import { render, screen } from '@testing-library/react'
import HomePage from '../HomePage'

test('HomeSpec: key headings present', ()=>{
  render(<HomePage />)
  // match the heading specifically to avoid matching body text
  expect(screen.getByRole('heading', { name: /Flash Bureau/i })).toBeInTheDocument()
  // target the heading specifically to avoid matching descriptive paragraph text
  expect(screen.getByRole('heading', { name: /Reference Rails/i })).toBeInTheDocument()
})
