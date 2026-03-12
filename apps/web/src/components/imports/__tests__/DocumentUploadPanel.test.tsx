import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import DocumentUploadPanel from '../DocumentUploadPanel'

jest.mock('../../../api/client', () => {
  const actual = jest.requireActual('../../../api/client')
  return Object.assign({}, actual, {
    uploadDocumentForm: jest.fn().mockResolvedValue({ id: 'abc', filename: 't.txt', uploaded_at: 'now', size: 5, tags: '' }),
    listDocuments: jest.fn().mockResolvedValue([]),
    documentDownloadUrl: jest.fn().mockReturnValue('/api/documents/abc/download')
  })
})

test('renders Data Hub redirect instead of inline upload', async ()=>{
  render(<DocumentUploadPanel />)
  const btn = await screen.findByRole('button', { name: /Open Data Hub Imports/i })
  expect(btn).toBeInTheDocument()
})
