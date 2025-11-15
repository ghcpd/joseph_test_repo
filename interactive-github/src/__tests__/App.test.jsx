import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import App from '../App'

const createResponse = (data, overrides = {}) => ({
  ok: overrides.ok ?? true,
  status: overrides.status ?? 200,
  headers: {
    get: (key) => {
      const normalized = key?.toLowerCase?.()
      const headerMap = Object.entries(overrides.headers || {}).reduce(
        (accumulator, [headerKey, value]) => {
          accumulator[headerKey.toLowerCase()] = value
          return accumulator
        },
        {},
      )
      return headerMap[normalized] ?? null
    },
  },
  json: async () => data,
})

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('validates repository URL before fetching', async () => {
    render(<App />)

    const repoInput = screen.getByLabelText(/repository url/i)
    await userEvent.type(repoInput, 'https://example.com/owner/repo')

    const fetchButton = screen.getByRole('button', { name: /fetch/i })
    await userEvent.click(fetchButton)

    expect(
      screen.getByText(/enter a valid github repository url/i),
    ).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalled()
  })

  test('fetches repository issues and displays details', async () => {
    const listResponse = [
      {
        id: 101,
        number: 17,
        title: 'Triage bugfix',
        labels: [
          { id: 1, name: 'bug', color: 'd73a4a' },
          { id: 2, name: 'needs-triage', color: '0075ca' },
        ],
        user: { login: 'octocat' },
        state: 'open',
        created_at: '2023-10-01T12:00:00Z',
        updated_at: '2023-10-02T12:00:00Z',
      },
    ]

    const detailResponse = {
      ...listResponse[0],
      body: 'This issue tracks the bugfix work.',
    }

    fetch.mockResolvedValueOnce(createResponse(listResponse))
    fetch.mockResolvedValueOnce(createResponse(detailResponse))

    render(<App />)

    const repoInput = screen.getByLabelText(/repository url/i)
    await userEvent.type(repoInput, 'https://github.com/test-org/example')

    const dataTypeSelect = screen.getByLabelText(/data type/i)
    await userEvent.selectOptions(dataTypeSelect, 'issues')

    const fetchButton = screen.getByRole('button', { name: /fetch/i })
    await userEvent.click(fetchButton)

    const itemSelect = await screen.findByLabelText(/select an issue/i)
    const option = await within(itemSelect).findByRole('option', {
      name: /issue #17: triage bugfix/i,
    })
    expect(option).toBeInTheDocument()

    await userEvent.selectOptions(itemSelect, option)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /triage bugfix/i })).toBeInTheDocument()
    })

    expect(screen.getByText(/octocat/)).toBeInTheDocument()
    expect(screen.getByText(/bugfix work/i)).toBeInTheDocument()

    expect(fetch).toHaveBeenNthCalledWith(
      1,
      'https://api.github.com/repos/test-org/example/issues?per_page=30',
    )
    expect(fetch).toHaveBeenNthCalledWith(
      2,
      'https://api.github.com/repos/test-org/example/issues/17',
    )
  })
})
