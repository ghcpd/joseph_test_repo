const request = require('supertest');
const { app, parseRepoInput } = require('../server');

const originalFetch = global.fetch;

describe('GitHub proxy server', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
    global.fetch = originalFetch;
  });

  it('parses repository input correctly', () => {
    expect(parseRepoInput('octocat/Hello-World')).toBe('octocat/Hello-World');
    expect(parseRepoInput(' https://github.com/octocat/Hello-World ')).toBe('octocat/Hello-World');
    expect(parseRepoInput('invalid-url')).toBeNull();
  });

  it('returns formatted pull request items', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            number: 7,
            title: 'Update dependencies',
            state: 'open',
            user: { login: 'alice' },
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-02T00:00:00Z',
            merged_at: null,
            labels: [{ name: 'bug' }],
            body: 'Details',
          },
        ]),
    });

    const response = await request(app).get('/api/prs').query({ repo: 'octocat/Hello-World' });

    expect(response.status).toBe(200);
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.github.com/repos/octocat/Hello-World/pulls?state=all&per_page=20',
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: 'application/vnd.github+json' }),
      }),
    );
    expect(response.body).toEqual({
      items: [
        {
          number: 7,
          title: 'Update dependencies',
          author: 'alice',
          state: 'open',
          merged: false,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
          labels: ['bug'],
          body: 'Details',
        },
      ],
    });
  });

  it('filters out pull requests in the issues API response', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            number: 101,
            title: 'Issue only',
            state: 'open',
            user: { login: 'bob' },
            created_at: '2023-06-01T00:00:00Z',
            updated_at: '2023-06-02T00:00:00Z',
            labels: [],
            body: 'Issue body',
          },
          {
            number: 55,
            title: 'PR disguised as issue',
            pull_request: {},
            state: 'closed',
          },
        ]),
    });

    const response = await request(app).get('/api/issues').query({ repo: 'octocat/Hello-World' });

    expect(response.status).toBe(200);
    expect(response.body.items).toHaveLength(1);
    expect(response.body.items[0]).toMatchObject({ number: 101, title: 'Issue only' });
  });

  it('returns details for a specific pull request', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          number: 9,
          title: 'Add feature',
          state: 'closed',
          merged_at: '2024-05-01T00:00:00Z',
          user: { login: 'charlie' },
          created_at: '2024-04-01T00:00:00Z',
          updated_at: '2024-05-01T00:00:00Z',
          labels: [],
          body: 'Description',
        }),
    });

    const response = await request(app)
      .get('/api/prs')
      .query({ repo: 'octocat/Hello-World', number: '9' });

    expect(response.status).toBe(200);
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.github.com/repos/octocat/Hello-World/pulls/9',
      expect.any(Object),
    );
    expect(response.body.item).toMatchObject({
      number: 9,
      merged: true,
      author: 'charlie',
    });
  });

  it('returns an error when GitHub responds with an error', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ message: 'Not Found' }),
    });

    const response = await request(app).get('/api/prs').query({ repo: 'octocat/Unknown' });

    expect(response.status).toBe(404);
    expect(response.body).toEqual({ error: 'Not Found' });
  });

  it('rejects invalid repository values', async () => {
    const response = await request(app).get('/api/prs').query({ repo: 'not-valid' });
    expect(response.status).toBe(400);
    expect(response.body.error).toMatch(/invalid repository/i);
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
