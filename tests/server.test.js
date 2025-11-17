const test = require('node:test');
const assert = require('node:assert');

const { validateRepoParam, mapPullRequest, mapIssue } = require('../server');

test('validateRepoParam accepts owner/repo format', () => {
  assert.strictEqual(validateRepoParam('octocat/Hello-World'), true);
  assert.strictEqual(validateRepoParam('user.name/repo_name-123'), true);
});

test('validateRepoParam rejects invalid formats', () => {
  assert.strictEqual(validateRepoParam(''), false);
  assert.strictEqual(validateRepoParam('invalid url'), false);
  assert.strictEqual(validateRepoParam('owner only'), false);
  assert.strictEqual(validateRepoParam('owner/repo/extra'), false);
});

test('mapPullRequest normalizes merged state and labels', () => {
  const pr = {
    id: 1,
    number: 42,
    title: 'Add feature',
    user: { login: 'alice' },
    state: 'closed',
    merged_at: '2020-01-01T00:00:00Z',
    created_at: '2020-01-01T00:00:00Z',
    updated_at: '2020-01-02T00:00:00Z',
    body: 'Details',
    html_url: 'https://github.com/owner/repo/pull/42',
    labels: [{ name: 'enhancement' }, { name: 'bug' }]
  };

  const mapped = mapPullRequest(pr);
  assert.strictEqual(mapped.state, 'merged');
  assert.deepStrictEqual(mapped.labels, ['enhancement', 'bug']);
  assert.strictEqual(mapped.number, 42);
  assert.strictEqual(mapped.author, 'alice');
});

test('mapIssue returns expected properties', () => {
  const issue = {
    id: 2,
    number: 7,
    title: 'Fix bug',
    user: { login: 'bob' },
    state: 'open',
    created_at: '2021-01-01T00:00:00Z',
    updated_at: '2021-01-02T00:00:00Z',
    body: 'Issue details',
    html_url: 'https://github.com/owner/repo/issues/7',
    labels: []
  };

  const mapped = mapIssue(issue);
  assert.strictEqual(mapped.state, 'open');
  assert.deepStrictEqual(mapped.labels, []);
  assert.strictEqual(mapped.author, 'bob');
  assert.strictEqual(mapped.number, 7);
});