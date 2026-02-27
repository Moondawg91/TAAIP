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
  // document helpers used by DocumentUploadPanel
  listDocuments: jest.fn().mockResolvedValue([]),
  uploadDocumentForm: jest.fn(),
  documentDownloadUrl: jest.fn(),
  default: {}
}))

import ImportCenterPage from '../pages/ImportCenterPage'
import { uploadImport, parseImport, getImport, mapImport, validateImport, commitImport } from '../api/client'

test('ImportCenterPage links to Data Hub imports', async () => {
  render(<ImportCenterPage />)
  const btn = await screen.findByRole('button', { name: /Open Data Hub Imports/i })
  expect(btn).toBeInTheDocument()
})
