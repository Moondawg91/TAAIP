import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ExportMenu from '../components/ExportMenu'

describe('ExportMenu', () => {
  beforeEach(() => {
    // mock URL.createObjectURL and revokeObjectURL
    ;(global as any).URL.createObjectURL = jest.fn(() => 'blob:fake')
    ;(global as any).URL.revokeObjectURL = jest.fn()
    // spy on anchor click
    jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function() {})
  })
  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders and exports CSV/JSON without throwing', async () => {
    const data = [{ a: 1, b: 'x' }, { a: 2, b: 'y' }]
    render(<ExportMenu data={data} filename="testfile" />)

    const btn = screen.getByTitle('Export')
    fireEvent.click(btn)

    // menu items are rendered; click CSV then JSON
    const csvItem = await screen.findByText('Export CSV')
    fireEvent.click(csvItem)
    await waitFor(() => expect((global as any).URL.createObjectURL).toHaveBeenCalled())

    // open again and export JSON
    fireEvent.click(btn)
    const jsonItem = await screen.findByText('Export JSON')
    fireEvent.click(jsonItem)
    await waitFor(() => expect((global as any).URL.createObjectURL).toHaveBeenCalledTimes(2))
  })
})
