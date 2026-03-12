const fs = require('fs')
const path = require('path')

describe('TOR routes exist in App.js', () => {
  const appFile = path.resolve(__dirname, '..', 'App.js')
  const content = fs.readFileSync(appFile, 'utf8')
  const required = [
    '/planning',
    '/planning/calendar',
    '/roi/events',
    '/schools',
    '/data-hub',
    '/help/submit-ticket',
    '/help/system-status',
    '/budget',
    '/command-center'
  ]
  required.forEach(route => {
    test(`route ${route} exists in App.js`, () => {
      expect(content.includes(route)).toBeTruthy()
    })
  })
})
