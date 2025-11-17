const test = require('node:test');
const assert = require('node:assert/strict');
const request = require('supertest');
const nock = require('nock');

const app = require('./server');

nock.disableNetConnect();
nock.enableNetConnect('127.0.0.1');

test.afterEach(() => {
  nock.cleanAll();
});

test('GET /api/prs validates repository format', async () => {
  const response = await request(app).get('/api/prs').query({ repo: 'invalid' });
  assert.equal(response.status, 400);
  assert.match(response.body.message, /repo/i);
});

test('GET /api/prs proxies pull requests from GitHub', async () => {
  const repo = 'octocat/Hello-World';
  const ghScope = nock('https://api.github.com')
    .get(`/repos/${repo}/pulls`)
    .query(true)
    .reply(200, [
      {
        number: 1,
        title: 'Add feature',
        labels: [{ name: 'bug' }]
      }
    ]);

  const response = await request(app).get('/api/prs').query({ repo });
  assert.equal(response.status, 200);
  assert.equal(response.body.length, 1);
  assert.equal(response.body[0].number, 1);
  ghScope.done();
});

test('GET /api/issues filters pull requests from issue list', async () => {
  const repo = 'octocat/Hello-World';
  const ghScope = nock('https://api.github.com')
    .get(`/repos/${repo}/issues`)
    .query(true)
    .reply(200, [
      { number: 2, title: 'Real issue' },
      { number: 3, title: 'Pull request', pull_request: {} }
    ]);

  const response = await request(app).get('/api/issues').query({ repo });
  assert.equal(response.status, 200);
  assert.equal(response.body.length, 1);
  assert.equal(response.body[0].number, 2);
  ghScope.done();
});

test('GET /api/issues/:number omits pull request results', async () => {
  const repo = 'octocat/Hello-World';
  const issueNumber = 5;
  nock('https://api.github.com')
    .get(`/repos/${repo}/issues/${issueNumber}`)
    .reply(200, { number: issueNumber, pull_request: {} });

  const response = await request(app)
    .get(`/api/issues/${issueNumber}`)
    .query({ repo });
  assert.equal(response.status, 404);
});

test('GET /api/prs/:number handles upstream error', async () => {
  const repo = 'octocat/Hello-World';
  const prNumber = 10;
  nock('https://api.github.com')
    .get(`/repos/${repo}/pulls/${prNumber}`)
    .reply(500, { message: 'Server error' });

  const response = await request(app)
    .get(`/api/prs/${prNumber}`)
    .query({ repo });
  assert.equal(response.status, 500);
  assert.match(response.body.message, /Server error/);
});