# Documentation Server Lifecycle Management

Shared instructions for starting, verifying, and stopping the Mintlify documentation preview server during agentic workflow runs.

## Starting the Documentation Preview Server

To preview documentation changes locally, start the Mintlify development server:

```bash
cd ${{ github.workspace }}/docs-vnext
npx mintlify dev --port 3333 > /tmp/mintlify-server.log 2>&1 &
echo $! > /tmp/mintlify-server.pid
```

## Waiting for Server Readiness

Wait for the server to be ready before taking screenshots or running tests:

```bash
for i in {1..30}; do
  curl -s http://localhost:3333/ > /dev/null && echo "Mintlify server ready!" && break
  echo "Waiting for server... ($i/30)" && sleep 2
done
```

## Verifying Server Accessibility

Optionally verify the server is serving content:

```bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3333/)
if [ "$STATUS" = "200" ]; then
  echo "✅ Server accessible (HTTP $STATUS)"
else
  echo "❌ Server returned HTTP $STATUS"
fi
```

## Stopping the Documentation Server

Always clean up the server after testing:

```bash
if [ -f /tmp/mintlify-server.pid ]; then
  kill $(cat /tmp/mintlify-server.pid) 2>/dev/null || true
  rm -f /tmp/mintlify-server.pid
fi
rm -f /tmp/mintlify-server.log
```
