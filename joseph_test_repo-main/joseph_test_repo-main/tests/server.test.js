const request = require('supertest');

jest.mock('node-fetch', () => jest.fn());
const fetch = require('node-fetch');

const buildResponse = (data, overrides = {}) => {
  const { headers = {}, ...rest } = overrides;
  const normalizedHeaders = {
    get: (key) => headers[key.toLowerCase()] ?? headers[key] ?? null
  };
  return {
    ok: rest.ok !== undefined ? rest.ok : true,
    status: rest.status || 200,
    json: jest.fn().mockResolvedValue(data),
    text: jest.fn().mockResolvedValue(JSON.stringify(data)),
    headers: normalizedHeaders,
    ...rest
  };
};

describe('GitHub proxy server', () => {
  let app;

  const sampleList = [
    {
      number: 1,
      title: 'Fix bug',
      state: 'open',
      user: { login: 'octocat' },
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-02T00:00:00Z',
      labels: [{ name: 'bug' }]
    },
    {
      number: 2,
      title: 'Documentation',
      state: 'closed',
      user: { login: 'hubot' },
      created_at: '2023-01-03T00:00:00Z',
      updated_at: '2023-01-04T00:00:00Z',
      labels: []
    }
  ];

  const sampleDetail = {
    number: 1,
    title: 'Fix bug',
    state: 'open',
    user: { login: 'octocat' },
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
    body: 'Body text',
    labels: [{ name: 'bug' }],
    additions: 10,
    deletions: 3,
    changed_files: 2,
    merged_at: null
  };

  beforeEach(() => {
    fetch.mockReset();
    delete require.cache[require.resolve('../server')];
    app = require('../server');
  });

  it('returns a list of pull requests', async () => {
    fetch.mockResolvedValue(buildResponse(sampleList));

    const res = await request(app).get('/api/prs?repo=owner/pullsrepo');

    expect(fetch).toHaveBeenCalledWith('https://api.github.com/repos/owner/pullsrepo/pulls?state=all&per_page=50', expect.any(Object));
    expect(res.status).toBe(200);
    expect(res.body).toEqual([
      expect.objectContaining({
        number: 1,
        title: 'Fix bug',
        author: 'octocat',
        type: 'pulls'
      }),
      expect.objectContaining({
        number: 2,
        title: 'Documentation',
        author: 'hubot',
        type: 'pulls'
      })
    ]);
  });

  it('filters out pull requests when retrieving issues', async () => {
    const issuesList = [
      { ...sampleList[0], pull_request: { url: '...' } },
      { ...sampleList[1] }
    ];
    fetch.mockResolvedValue(buildResponse(issuesList));

    const res = await request(app).get('/api/issues?repo=ownerissues/repo');

    expect(fetch).toHaveBeenCalledWith('https://api.github.com/repos/ownerissues/repo/issues?state=all&per_page=50', expect.any(Object));
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);
    expect(res.body[0]).toEqual(expect.objectContaining({ number: 2, title: 'Documentation', isIssue: true }));
  });

  it('returns detail information for a pull request', async () => {
    fetch.mockResolvedValue(buildResponse(sampleDetail));

    const res = await request(app).get('/api/prs/1?repo=another/repo');

    expect(fetch).toHaveBeenCalledWith('https://api.github.com/repos/another/repo/pulls/1', expect.any(Object));
    expect(res.status).toBe(200);
    expect(res.body).toEqual(expect.objectContaining({
      number: 1,
      type: 'pull_request',
      merged: false,
      author: 'octocat'
    }));
  });

  it('validates repository format', async () => {
    const res = await request(app).get('/api/prs?repo=invalid repo');

    expect(res.status).toBe(400);
    expect(res.body).toEqual(expect.objectContaining({ error: expect.any(String) }));
    expect(fetch).not.toHaveBeenCalled();
  });

  it('translates GitHub rate limit errors', async () => {
    const response = buildResponse(
      { message: 'API rate limit exceeded' },
      {
        ok: false,
        status: 403,
        headers: {
          'x-ratelimit-remaining': '0',
          'x-ratelimit-reset': `${Math.floor(Date.now() / 1000) + 60}`
        }
      }
    );
    fetch.mockResolvedValue(response);

    const res = await request(app).get('/api/prs?repo=owner/ratelimit');

    expect(res.status).toBe(429);
    expect(res.body.error).toMatch(/rate limit/i);
  });

  it('caches list responses to reduce API calls', async () => {
    fetch.mockResolvedValue(buildResponse(sampleList));

    await request(app).get('/api/prs?repo=owner/cache');
    await request(app).get('/api/prs?repo=owner/cache');

    expect(fetch).toHaveBeenCalledTimes(1);
  });
});