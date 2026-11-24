const fs = require('fs');
const https = require('https');
const path = require('path');

const envPath = path.join(__dirname, '.env.local');
let apiKey = null;

if (fs.existsSync(envPath)) {
  const content = fs.readFileSync(envPath, 'utf8');
  const match = content.match(/BREVO_API_KEY=(.*)/);
  if (match) {
    apiKey = match[1].replace(/["']/g, '').trim();
  }
}

if (!apiKey) {
  console.error("No BREVO_API_KEY found in .env.local");
  process.exit(1);
}

const options = {
  hostname: 'api.brevo.com',
  port: 443,
  path: '/v3/smtp/statistics/events?limit=10&sort=desc',
  method: 'GET',
  headers: {
    'accept': 'application/json',
    'api-key': apiKey
  }
};

const req = https.request(options, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    try {
      const parsed = JSON.parse(data);
      if (parsed.events) {
        parsed.events.forEach(event => {
          console.log(`Message ID: ${event.messageId}`);
          console.log(`Event Status: ${event.event}`);
          console.log(`Email: ${event.email}`);
          if (event.reason) console.log(`Reason: ${event.reason}`);
          if (event.reasonCode) console.log(`Reason Code: ${event.reasonCode}`);
          console.log('-'.repeat(40));
        });
      } else {
        console.log("Response:", data);
      }
    } catch (e) {
      console.error("Parse Error:", e);
      console.log("Raw Response:", data);
    }
  });
});

req.on('error', (e) => {
  console.error(`Request Error: ${e.message}`);
});

req.end();
