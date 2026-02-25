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

test('renders and uploads a file', async ()=>{
  render(<DocumentUploadPanel />)
  // file input exists
  const input = screen.getByTestId('document-file-input') as HTMLInputElement
  const file = new File(['hello'], 'hello.txt', { type: 'text/plain' })
  // simulate selecting file
  fireEvent.change(input, { target: { files: [file] } })
  // click upload
  const btn = screen.getByText('Upload')
  fireEvent.click(btn)
  const matches = await screen.findAllByText(/uploaded/i)
  expect(matches.length).toBeGreaterThan(0)
})
