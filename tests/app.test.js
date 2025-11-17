const request = require('supertest');

jest.mock('node-fetch', () => jest.fn());

const fetch = require('node-fetch');
const { app, normalizeRepo } = require('../app');

const createMockResponse = (data, status = 200, headerMap = {}) => ({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(typeof data === 'string' ? data : JSON.stringify(data)),
  headers: {
    get: key => {
      const lowerKey = key.toLowerCase();
      const normalized = Object.fromEntries(
        Object.entries(headerMap).map(([k, v]) => [k.toLowerCase(), v])
      );
      return normalized[lowerKey] ?? null;
    }
  }
});

describe('normalizeRepo', () => {
  it('parses full GitHub URLs', () => {
    expect(normalizeRepo('https://github.com/octocat/hello-world')).toBe('octocat/hello-world');
    expect(normalizeRepo('http://github.com/octo/test/')).toBe('octo/test');
  });

  it('returns null for invalid values', () => {
    expect(normalizeRepo('foo')).toBeNull();
    expect(normalizeRepo('https://example.com/octo/test')).toBeNull();
    expect(normalizeRepo('')).toBeNull();
  });
});

describe('GitHub proxy routes', () => {
  beforeEach(() => {
    fetch.mockReset();
  });

  it('returns 400 when repository is invalid', async () => {
    const response = await request(app).get('/api/prs?repo=invalid');
    expect(response.status).toBe(400);
    expect(response.body.error).toMatch(/Invalid repository format/i);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('proxies pull request list results', async () => {
    const mockedData = [
      { number: 1, title: 'Test PR', user: { login: 'user1' }, state: 'open', merged_at: null }
    ];
    fetch.mockResolvedValue(createMockResponse(mockedData));

    const response = await request(app).get('/api/prs?repo=octocat/hello-world');
    expect(response.status).toBe(200);
    expect(response.body).toEqual(mockedData);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('https://api.github.com/repos/octocat/hello-world/pulls'),
      expect.objectContaining({ headers: expect.any(Object) })
    );
  });

  it('translates GitHub rate limit errors', async () => {
    fetch.mockResolvedValue(
      createMockResponse('Forbidden', 403, {
        'x-ratelimit-remaining': '0',
        'x-ratelimit-reset': `${Math.floor(Date.now() / 1000) + 60}`
      })
    );

    const response = await request(app).get('/api/issues?repo=octocat/hello-world');
    expect(response.status).toBe(429);
    expect(response.body.error).toMatch(/rate limit/i);
  });

  it('fetches pull request details', async () => {
    const mockedDetail = { number: 2, title: 'Detail', user: { login: 'octo' }, state: 'closed', merged_at: '2023-01-01' };
    fetch.mockResolvedValue(createMockResponse(mockedDetail));

    const response = await request(app).get('/api/prs/2?repo=octocat/hello-world');
    expect(response.status).toBe(200);
    expect(response.body).toEqual(mockedDetail);
  });
});