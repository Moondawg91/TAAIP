import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock client functions used by the page via jest.fn exports
jest.mock('../api/client', () => ({
  uploadImport: jest.fn(),
  parseImport: jest.fn(),
  getImport: jest.fn(),
  mapImport: jest.fn(),
  validateImport: jest.fn(),
  commitImport: jest.fn(),
  default: {}
}))

import ImportCenterPage from '../pages/ImportCenterPage'
import { uploadImport, parseImport, getImport, mapImport, validateImport, commitImport } from '../api/client'

test('full import flow UI - upload -> parse -> map -> validate -> commit', async () => {
  // set up mock behavior
  ;(uploadImport as jest.Mock).mockResolvedValue({ import_job_id: 42 })
  ;(parseImport as jest.Mock).mockResolvedValue({ preview_rows: 1, columns: ['name','org_unit_id'] })
  ;(getImport as jest.Mock).mockResolvedValue({ preview: [{ name: 'Smoke Test Event', org_unit_id: '1' }], columns: ['name','org_unit_id'], logs: [] })
  ;(mapImport as jest.Mock).mockResolvedValue({ import_job_id: 42, status: 'validating' })
  ;(validateImport as jest.Mock).mockResolvedValue({ import_job_id: 42, errors: 0, warnings: 0 })
  ;(commitImport as jest.Mock).mockResolvedValue({ import_job_id: 42, imported: 1 })

  // stub alert
  const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {})

  render(<ImportCenterPage />)

  const file = new File(["name,org_unit_id\nSmoke Test Event,1\n"], 'import_smoke.csv', { type: 'text/csv' })
  const input = screen.getByTestId('file-input') as HTMLInputElement

  // upload
  fireEvent.change(input, { target: { files: [file] } })

  // wait for parse button to become enabled
  const parseBtn = await screen.findByRole('button', { name: /Parse & Preview/i })
  await waitFor(() => expect(parseBtn).not.toBeDisabled())

  // parse & preview
  fireEvent.click(parseBtn)
  await waitFor(() => expect(getImport).toHaveBeenCalled())
  // preview should show row
  await waitFor(() => expect(screen.getByText('Smoke Test Event')).toBeInTheDocument())

  // auto-map and save mapping
  const autoBtn = screen.getByRole('button', { name: /Auto-map same-name/i })
  fireEvent.click(autoBtn)
  const saveMap = screen.getByRole('button', { name: /Save Mapping/i })
  fireEvent.click(saveMap)
  await waitFor(() => expect(mapImport).toHaveBeenCalled())

  // validate
  const validateBtn = screen.getByRole('button', { name: /Validate/i })
  fireEvent.click(validateBtn)
  await waitFor(() => expect(validateImport).toHaveBeenCalled())

  // commit
  const commitBtn = screen.getByRole('button', { name: /Commit/i })
  fireEvent.click(commitBtn)
  await waitFor(() => expect(commitImport).toHaveBeenCalled())
  expect(alertSpy).toHaveBeenCalledWith('Imported 1 rows')

  alertSpy.mockRestore()
})
