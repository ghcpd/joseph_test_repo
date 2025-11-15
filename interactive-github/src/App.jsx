import { useMemo, useState } from 'react'
import './App.css'

const DATA_OPTIONS = [
  { label: 'Pull Requests', value: 'pulls' },
  { label: 'Issues', value: 'issues' },
]

const parseRepositoryUrl = (input) => {
  if (!input) {
    return null
  }

  try {
    const trimmed = input.trim()
    const url = new URL(trimmed)

    if (url.protocol !== 'https:' || url.hostname !== 'github.com') {
      return null
    }

    const segments = url.pathname
      .split('/')
      .map((segment) => segment.trim())
      .filter(Boolean)

    if (segments.length < 2) {
      return null
    }

    return {
      owner: segments[0],
      repo: segments[1].replace(/\.git$/, ''),
      formatted: `${segments[0]}/${segments[1].replace(/\.git$/, '')}`,
    }
  } catch (error) {
    return null
  }
}

const formatDate = (value) => {
  if (!value) {
    return 'Unknown'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown'
  }

  return date.toLocaleString()
}

const summarizeOption = (item, type) => {
  const prefix = type === 'pulls' ? 'PR' : 'Issue'
  const title = item?.title || '(untitled)'
  const bugLabel = Array.isArray(item?.labels)
    ? item.labels.some((label) => label?.name?.toLowerCase() === 'bug')
    : false

  return `${bugLabel ? '🐞 ' : ''}${prefix} #${item.number}: ${title}`
}

function App() {
  const [repoUrl, setRepoUrl] = useState('')
  const [dataType, setDataType] = useState(DATA_OPTIONS[0].value)
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [detailError, setDetailError] = useState('')
  const [loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [selectedNumber, setSelectedNumber] = useState('')
  const [selectedDetail, setSelectedDetail] = useState(null)
  const [activeRepo, setActiveRepo] = useState(null)
  const [detailsCache, setDetailsCache] = useState({})
  const [statusMessage, setStatusMessage] = useState('')

  const repoHint = useMemo(
    () => parseRepositoryUrl(repoUrl),
    [repoUrl],
  )

  const onFetchList = async () => {
    const parsed = parseRepositoryUrl(repoUrl)

    if (!parsed) {
      setError('Enter a valid GitHub repository URL, e.g. https://github.com/user/repo')
      setActiveRepo(null)
      setItems([])
      setSelectedNumber('')
      setSelectedDetail(null)
      setStatusMessage('')
      return
    }

    setLoading(true)
    setError('')
    setDetailError('')
    setStatusMessage('')
    setSelectedNumber('')
    setSelectedDetail(null)
    setDetailsCache({})

    try {
      const response = await fetch(
        `https://api.github.com/repos/${parsed.owner}/${parsed.repo}/${dataType}?per_page=30`,
      )

      if (!response.ok) {
        const rateLimitHeader = response.headers?.get?.('X-RateLimit-Remaining')
        const reachedRateLimit = rateLimitHeader === '0'
        throw new Error(
          reachedRateLimit
            ? 'GitHub API rate limit reached. Please wait and try again later.'
            : 'Unable to fetch data from GitHub. Confirm the repository exists and try again.',
        )
      }

      const data = await response.json()
      if (Array.isArray(data)) {
        setItems(data)
        setStatusMessage(
          `${data.length} ${dataType === 'pulls' ? 'pull requests' : 'issues'} loaded`,
        )
      } else {
        setItems([])
        setStatusMessage('')
      }
      setActiveRepo(parsed)
    } catch (requestError) {
      setError(requestError.message || 'Something went wrong while fetching data.')
      setItems([])
      setActiveRepo(parsed)
    } finally {
      setLoading(false)
    }
  }

  const fetchDetail = async (number) => {
    if (!activeRepo || !number) {
      return null
    }

    const cacheKey = `${dataType}-${number}`

    if (detailsCache[cacheKey]) {
      return detailsCache[cacheKey]
    }

    const resource = dataType === 'pulls' ? 'pulls' : 'issues'
    const response = await fetch(
      `https://api.github.com/repos/${activeRepo.owner}/${activeRepo.repo}/${resource}/${number}`,
    )

    if (!response.ok) {
      const rateLimitHeader = response.headers?.get?.('X-RateLimit-Remaining')
      const reachedRateLimit = rateLimitHeader === '0'
      throw new Error(
        reachedRateLimit
          ? 'GitHub API rate limit reached while loading item details.'
          : 'Unable to fetch the selected item details.',
      )
    }

    const detail = await response.json()
    setDetailsCache((previous) => ({ ...previous, [cacheKey]: detail }))
    return detail
  }

  const handleSelectionChange = async (event) => {
    const number = event.target.value
    setSelectedNumber(number)
    setSelectedDetail(null)
    setDetailError('')

    if (!number) {
      return
    }

    try {
      setDetailLoading(true)
      const detail = await fetchDetail(number)
      if (detail) {
        setSelectedDetail(detail)
      }
    } catch (detailFetchError) {
      setDetailError(detailFetchError.message || 'Unable to fetch the selected item details.')
    } finally {
      setDetailLoading(false)
    }
  }

  const hasBugLabel = useMemo(() => {
    if (!selectedDetail || !Array.isArray(selectedDetail.labels)) {
      return false
    }

    return selectedDetail.labels.some((label) => label?.name?.toLowerCase() === 'bug')
  }, [selectedDetail])

  const statusText = useMemo(() => {
    if (!selectedDetail) {
      return ''
    }

    if (dataType === 'pulls') {
      if (selectedDetail.merged_at) {
        return 'merged'
      }
    }

    return (selectedDetail.state || 'unknown').toLowerCase()
  }, [dataType, selectedDetail])

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>GitHub Explorer</h1>
        <p>
          Fetch and inspect pull requests or issues from any public GitHub repository. Provide a
          repository URL, choose the data type, and explore individual item details.
        </p>
      </header>

      <section className="controls" aria-label="Repository configuration">
        <div className="field">
          <label htmlFor="repo-url">Repository URL</label>
          <input
            id="repo-url"
            name="repo-url"
            type="url"
            placeholder="https://github.com/owner/repository"
            aria-describedby="repo-hint"
            value={repoUrl}
            onChange={(event) => setRepoUrl(event.target.value)}
            autoComplete="off"
          />
          <small id="repo-hint" className="hint">
            {repoHint ? `Parsed as ${repoHint.formatted}` : 'Enter a full GitHub repository URL'}
          </small>
        </div>

        <div className="field">
          <label htmlFor="data-type">Data type</label>
          <select
            id="data-type"
            value={dataType}
            onChange={(event) => {
              setDataType(event.target.value)
              setSelectedNumber('')
              setSelectedDetail(null)
              setDetailError('')
              setDetailsCache({})
            }}
          >
            {DATA_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <button type="button" className="primary" onClick={onFetchList} disabled={loading}>
          {loading ? 'Fetching…' : 'Fetch'}
        </button>
      </section>

      {error ? (
        <div className="alert warning" role="alert">
          {error}
        </div>
      ) : null}

      {statusMessage && !loading ? (
        <p className="status" aria-live="polite">
          {activeRepo ? `${statusMessage} from ${activeRepo.formatted}` : statusMessage}
        </p>
      ) : null}

      <section className="selection" aria-label="Repository items">
        <div className="field full-width">
          <label htmlFor="item-select">
            {dataType === 'pulls' ? 'Select a pull request' : 'Select an issue'}
          </label>
          <select
            id="item-select"
            value={selectedNumber}
            onChange={handleSelectionChange}
            disabled={!items.length || loading}
          >
            <option value="">{items.length ? 'Choose an item…' : 'No items available'}</option>
            {items.map((item) => (
              <option
                key={item.id || item.number}
                value={item.number}
                data-bug={
                  Array.isArray(item?.labels) &&
                  item.labels.some((label) => label?.name?.toLowerCase() === 'bug')
                    ? 'true'
                    : 'false'
                }
              >
                {summarizeOption(item, dataType)}
              </option>
            ))}
          </select>
        </div>
      </section>

      {detailError ? (
        <div className="alert warning" role="alert">
          {detailError}
        </div>
      ) : null}

      {detailLoading ? (
        <p className="status" aria-live="polite">
          Loading details…
        </p>
      ) : null}

      {selectedDetail ? (
        <article className={`detail-panel ${hasBugLabel ? 'bug-highlight' : ''}`}>
          <header>
            <h2>{selectedDetail.title || 'Untitled'}</h2>
            {activeRepo ? (
              <p className="detail-meta">
                {dataType === 'pulls' ? 'Pull Request' : 'Issue'} #{selectedDetail.number} •{' '}
                {activeRepo.formatted}
              </p>
            ) : null}
          </header>

          <dl className="detail-list">
            <div>
              <dt>Status</dt>
              <dd className={`status-pill status-${statusText?.replace(/\s+/g, '-') || 'unknown'}`}>
                {statusText}
              </dd>
            </div>
            <div>
              <dt>Author</dt>
              <dd>{selectedDetail.user?.login || 'Unknown'}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatDate(selectedDetail.created_at)}</dd>
            </div>
            <div>
              <dt>Updated</dt>
              <dd>{formatDate(selectedDetail.updated_at)}</dd>
            </div>
          </dl>

          {Array.isArray(selectedDetail.labels) && selectedDetail.labels.length ? (
            <div className="labels">
              <h3>Labels</h3>
              <ul>
                {selectedDetail.labels.map((label) => (
                  <li key={label.id || label.name} style={{ '--label-color': label.color }}>
                    <span className="label-color" />
                    {label.name}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="body-content">
            <h3>Description</h3>
            <p>{selectedDetail.body?.trim() || 'No description provided.'}</p>
          </div>
        </article>
      ) : null}
    </div>
  )
}

export default App
