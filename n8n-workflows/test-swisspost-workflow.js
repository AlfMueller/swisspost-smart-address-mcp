#!/usr/bin/env node
/**
 * Test Script für korrigierte Swisspost n8n Workflows
 * 
 * Voraussetzungen:
 * 1. MCP HTTP Proxy starten: python mcp-http-proxy.py
 * 2. n8n Workflow importieren und aktivieren
 * 3. Dieses Script ausführen
 */

const https = require('https');
const http = require('http');

// Konfiguration
const N8N_BASE_URL = process.env.N8N_BASE_URL || 'http://localhost:5678';
const WEBHOOK_PATH = '/webhook/swisspost-validate';
const MCP_PROXY_URL = 'http://localhost:3000';

// Test-Adressen
const testAddresses = [
  {
    name: "Korrekte Adresse",
    data: {
      firstname: "Max",
      lastname: "Mustermann",
      company: "Test AG",
      street: "Bahnhofstrasse 1",
      city: "Zürich",
      postcode: "8001"
    },
    expected: { isValid: true, quality: "CERTIFIED" }
  },
  {
    name: "PLZ und Ort vertauscht",
    data: {
      firstname: "Anna",
      lastname: "Mustermann",
      street: "Hauptstrasse 15",
      city: "8005",  // PLZ im Stadtfeld
      postcode: "Zürich"  // Stadt im PLZ-Feld
    },
    expected: { isValid: true, hasCorrections: true }
  },
  {
    name: "Hausnummer am Anfang",
    data: {
      firstname: "Peter",
      lastname: "Schmidt",
      street: "94 Pfingstweidstrasse",  // Hausnummer am Anfang
      city: "Zürich",
      postcode: "8005"
    },
    expected: { isValid: true, hasCorrections: true }
  },
  {
    name: "Ungültige PLZ",
    data: {
      firstname: "Lisa",
      lastname: "Weber",
      street: "Teststrasse 123",
      city: "Zürich",
      postcode: "123"  // Ungültige PLZ (nur 3 Ziffern)
    },
    expected: { isValid: false, error: "PLZ muss 4 Ziffern haben" }
  },
  {
    name: "Fehlende Felder",
    data: {
      firstname: "Tom",
      lastname: "Bauer"
      // street, city, postcode fehlen
    },
    expected: { isValid: false, error: "Fehlende Felder" }
  }
];

// Hilfsfunktionen
function makeRequest(url, data) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const client = isHttps ? https : http;
    
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: urlObj.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(JSON.stringify(data))
      }
    };

    const req = client.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(body);
          resolve({ status: res.statusCode, data: response });
        } catch (e) {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });

    req.on('error', reject);
    req.write(JSON.stringify(data));
    req.end();
  });
}

async function testMCPProxy() {
  console.log('🔍 Teste MCP HTTP Proxy...');
  
  try {
    const response = await makeRequest(`${MCP_PROXY_URL}/health`, {});
    
    if (response.status === 200) {
      console.log('✅ MCP HTTP Proxy läuft');
      return true;
    } else {
      console.log('❌ MCP HTTP Proxy nicht erreichbar');
      return false;
    }
  } catch (error) {
    console.log('❌ MCP HTTP Proxy Fehler:', error.message);
    return false;
  }
}

async function testN8nWorkflow() {
  console.log('🔍 Teste n8n Workflow...');
  
  try {
    const testData = {
      firstname: "Test",
      lastname: "User",
      street: "Teststrasse 1",
      city: "Zürich",
      postcode: "8001"
    };
    
    const response = await makeRequest(`${N8N_BASE_URL}${WEBHOOK_PATH}`, testData);
    
    if (response.status === 200) {
      console.log('✅ n8n Workflow erreichbar');
      return true;
    } else {
      console.log('❌ n8n Workflow Fehler:', response.status, response.data);
      return false;
    }
  } catch (error) {
    console.log('❌ n8n Workflow Fehler:', error.message);
    return false;
  }
}

async function runTests() {
  console.log('🚀 Starte Swisspost n8n Workflow Tests\n');
  
  // 1. MCP Proxy testen
  const mcpRunning = await testMCPProxy();
  if (!mcpRunning) {
    console.log('\n❌ MCP HTTP Proxy muss gestartet werden:');
    console.log('   python mcp-http-proxy.py');
    return;
  }
  
  // 2. n8n Workflow testen
  const n8nRunning = await testN8nWorkflow();
  if (!n8nRunning) {
    console.log('\n❌ n8n Workflow muss importiert und aktiviert werden');
    return;
  }
  
  console.log('\n🧪 Führe Test-Adressen durch...\n');
  
  let passed = 0;
  let failed = 0;
  
  for (const test of testAddresses) {
    console.log(`📋 Test: ${test.name}`);
    console.log(`   Input: ${JSON.stringify(test.data)}`);
    
    try {
      const response = await makeRequest(`${N8N_BASE_URL}${WEBHOOK_PATH}`, test.data);
      
      if (response.status === 200) {
        const result = response.data;
        console.log(`   Status: ${result.success ? '✅' : '❌'}`);
        console.log(`   Valid: ${result.isValid ? 'Ja' : 'Nein'}`);
        console.log(`   Quality: ${result.quality?.level || 'N/A'}`);
        console.log(`   Score: ${result.quality?.score || 'N/A'}`);
        
        if (result.corrections && result.corrections.length > 0) {
          console.log(`   Korrekturen: ${result.corrections.length}`);
        }
        
        // Validiere Erwartungen
        let testPassed = true;
        
        if (test.expected.isValid !== undefined && result.isValid !== test.expected.isValid) {
          console.log(`   ❌ Erwartet isValid: ${test.expected.isValid}, erhalten: ${result.isValid}`);
          testPassed = false;
        }
        
        if (test.expected.hasCorrections !== undefined && result.hasCorrections !== test.expected.hasCorrections) {
          console.log(`   ❌ Erwartet hasCorrections: ${test.expected.hasCorrections}, erhalten: ${result.hasCorrections}`);
          testPassed = false;
        }
        
        if (test.expected.error && !result.error?.includes(test.expected.error)) {
          console.log(`   ❌ Erwartet Error: ${test.expected.error}, erhalten: ${result.error}`);
          testPassed = false;
        }
        
        if (testPassed) {
          console.log(`   ✅ Test bestanden`);
          passed++;
        } else {
          console.log(`   ❌ Test fehlgeschlagen`);
          failed++;
        }
        
      } else {
        console.log(`   ❌ HTTP ${response.status}: ${JSON.stringify(response.data)}`);
        failed++;
      }
      
    } catch (error) {
      console.log(`   ❌ Fehler: ${error.message}`);
      failed++;
    }
    
    console.log('');
  }
  
  // Zusammenfassung
  console.log('📊 Test-Zusammenfassung:');
  console.log(`   ✅ Bestanden: ${passed}`);
  console.log(`   ❌ Fehlgeschlagen: ${failed}`);
  console.log(`   📈 Erfolgsrate: ${Math.round((passed / (passed + failed)) * 100)}%`);
  
  if (failed === 0) {
    console.log('\n🎉 Alle Tests bestanden!');
  } else {
    console.log('\n⚠️  Einige Tests fehlgeschlagen. Überprüfen Sie die Konfiguration.');
  }
}

// Script ausführen
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { runTests, testAddresses };
