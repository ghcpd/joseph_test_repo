import assert from 'node:assert/strict';
import { parseRepositoryUrl, createSummary, normaliseItem } from '../src/github.js';

function testParseRepositoryUrl() {
  const result = parseRepositoryUrl('https://github.com/octocat/Hello-World');
  assert.equal(result.owner, 'octocat');
  assert.equal(result.repo, 'Hello-World');

  const withTrailingSlash = parseRepositoryUrl('https://github.com/foo/bar/');
  assert.equal(withTrailingSlash.owner, 'foo');
  assert.equal(withTrailingSlash.repo, 'bar');

  const withGitSuffix = parseRepositoryUrl('https://github.com/foo/my-repo.git');
  assert.equal(withGitSuffix.owner, 'foo');
  assert.equal(withGitSuffix.repo, 'my-repo');

  let threw = false;
  try {
    parseRepositoryUrl('invalid-url');
  } catch (error) {
    threw = true;
    assert.ok(/valid GitHub repository URL/.test(error.message));
  }
  assert.ok(threw, 'parseRepositoryUrl should throw for invalid URLs');
}

function testCreateSummary() {
  const items = [
    normaliseItem(
      {
        id: 1,
        number: 1,
        title: 'Fix bug',
        user: { login: 'alice' },
        state: 'open',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        body: 'Some description',
        html_url: 'https://github.com/test/1',
        labels: [{ name: 'bug' }]
      },
      'issues'
    ),
    normaliseItem(
      {
        id: 2,
        number: 2,
        title: 'Improve docs',
        user: { login: 'bob' },
        state: 'closed',
        created_at: '2024-01-03T00:00:00Z',
        updated_at: '2024-01-04T00:00:00Z',
        body: 'Another description',
        html_url: 'https://github.com/test/2',
        labels: []
      },
      'issues'
    )
  ];

  const summary = createSummary(items);
  assert.equal(summary.count, 2);
  assert.equal(summary.bugCount, 1);
  assert.deepEqual(new Set(summary.authors), new Set(['alice', 'bob']));
  assert.equal(summary.states.open, 1);
  assert.equal(summary.states.closed, 1);
}

function run() {
  testParseRepositoryUrl();
  testCreateSummary();
  console.log('All tests passed.');
}

run();