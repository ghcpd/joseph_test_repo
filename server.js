const { app } = require('./app');

const DEFAULT_PORT = 4173;

function resolvePort(value) {
  if (!value) {
    return DEFAULT_PORT;
  }
  const parsed = parseInt(value, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : DEFAULT_PORT;
}

const PORT = resolvePort(process.env.PORT);

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
  });
}

module.exports = app;
