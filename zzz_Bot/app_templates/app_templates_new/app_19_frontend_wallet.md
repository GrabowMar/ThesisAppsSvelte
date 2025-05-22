# Frontend Generation Prompt - React Crypto Wallet Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, send, receive, history, settings, security).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Crypto Wallet System Frontend**  
A modern React frontend for cryptocurrency wallet application, featuring intuitive balance management, secure transaction interfaces, comprehensive history tracking, and advanced security controls with clean, financial-grade design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Real-time balance dashboard with portfolio overview
- Secure send and receive transaction interfaces
- Comprehensive transaction history with filtering
- Address management and QR code generation
- Security settings and authentication controls
- Multi-currency support with exchange rate display
- Backup and recovery interface
- Mobile-responsive design for on-the-go access

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (dashboard, send, receive, history, addresses, settings, auth)
  // - wallet data with balances and addresses
  // - transactions array with history
  // - exchangeRates for currency conversion
  // - sendTransaction form data
  // - receiveAddress and QR code data
  // - user authentication state
  // - security settings and preferences
  // - loading states for transactions
  // - error states and notifications

  // 4. Refs
  // - qrCodeRef for generating QR codes
  // - transactionFormRef
  // - cameraRef for QR scanning
  // - pinInputRef for security
  
  // 5. Lifecycle Functions
  // - Load wallet data and balances
  // - Check user authentication
  // - Setup real-time balance updates
  // - Initialize security settings
  
  // 6. Event Handlers
  // - handleSendTransaction
  // - handleReceiveRequest
  // - handleAddressGeneration
  // - handleTransactionHistory
  // - handleSecuritySettings
  // - handleAuth (login/register/logout)
  // - handleQRCodeScan/Generate
  
  // 7. Transaction Functions
  // - sendCrypto
  // - generateReceiveAddress
  // - validateTransaction
  // - calculateFees
  // - confirmTransaction
  
  // 8. API Calls
  // - getWalletBalance
  // - sendTransaction
  // - getTransactionHistory
  // - generateAddress
  // - getExchangeRates
  // - updateSecuritySettings
  // - createBackup
  // - authenticate
  
  // 9. Utility Functions
  // - formatCurrency
  // - validateAddress
  // - generateQRCode
  // - calculatePortfolioValue
  // - formatTransactionHash
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderSendInterface()
  // - renderReceiveInterface()
  // - renderTransactionHistory()
  // - renderAddressManager()
  // - renderSecuritySettings()
  // - renderAuthView()
  
  return (
    <main className="wallet-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Wallet Dashboard**
   - Portfolio overview with total balance in multiple currencies
   - Individual currency balances with price changes
   - Quick action buttons (send, receive, buy, swap)
   - Recent transactions summary
   - Market price charts and trends
   - Portfolio performance metrics
   - News and market updates

2. **Send Transaction Interface**
   - Recipient address input with validation
   - Amount input with currency selection
   - Transaction fee selector (slow, normal, fast)
   - Transaction preview with all details
   - Security confirmation (PIN, biometric, 2FA)
   - QR code scanner for address input
   - Contact list for frequent recipients
   - Transaction templates for recurring payments

3. **Receive Transaction Interface**
   - QR code generation for wallet addresses
   - Address display with copy functionality
   - Custom amount request with QR code
   - Address labeling and organization
   - Share functionality for payment requests
   - Transaction monitoring for incoming payments
   - Address history and usage tracking

4. **Transaction History and Analytics**
   - Comprehensive transaction list with search
   - Transaction details with confirmations
   - Filtering by currency, amount, date, type
   - Export functionality for tax reporting
   - Transaction status tracking
   - Performance analytics and insights
   - Spending categories and analysis

5. **Address Management System**
   - List of all wallet addresses with balances
   - Address generation for different purposes
   - Address labeling and categorization
   - QR code generation for each address
   - Address verification and validation
   - Privacy settings for address reuse
   - Hierarchical deterministic address display

6. **Security and Settings Panel**
   - Two-factor authentication setup
   - PIN and password management
   - Backup and recovery options
   - Security audit and recommendations
   - Transaction limits and controls
   - Privacy settings and preferences
   - Account activity and login history

## Transaction Interface Features

```javascript
// Advanced transaction functionality:
const TransactionFeatures = {
  // - Real-time fee estimation with network congestion
  // - Address validation with format checking
  // - QR code scanning with camera integration
  // - Transaction templates for recurring payments
  // - Batch transactions for multiple recipients
  // - Transaction scheduling for future payments
  // - Multi-signature transaction support
  // - Transaction replacement (RBF) for stuck transactions
};
```

## Security and Authentication Interface

- **Multi-factor authentication** with TOTP support
- **Biometric authentication** for supported devices
- **PIN-based transaction** approval and access
- **Security audit** dashboard with recommendations
- **Session management** with automatic logout
- **Device registration** and trusted device management
- **Security alerts** and unusual activity notifications
- **Emergency recovery** procedures and backup access

## Balance and Portfolio Management

- **Real-time balance updates** with WebSocket connections
- **Multi-currency portfolio** with conversion rates
- **Portfolio performance** tracking and analytics
- **Price alerts** and notification system
- **Market data integration** with charts and trends
- **Profit/loss calculations** with cost basis tracking
- **Asset allocation** visualization and recommendations
- **Historical performance** analysis and reporting

## UI/UX Requirements

- Clean, financial-grade interface design
- Mobile-first responsive layout
- Touch-friendly controls for mobile transactions
- High contrast mode for accessibility
- Quick access buttons for common actions
- Visual feedback for transaction status
- Loading states for blockchain operations
- Error handling with helpful security guidance
- Accessibility compliance for financial apps
- Dark/Light theme for different environments

## QR Code and Camera Features

```javascript
// QR code and camera functionality:
const QRFeatures = {
  // - QR code generation for addresses and payment requests
  // - Camera integration for QR code scanning
  // - Address validation from scanned QR codes
  // - Payment URI support (BIP21, EIP681)
  // - Custom QR code styling and branding
  // - Batch QR code generation for multiple addresses
  // - QR code sharing and export functionality
  // - Error correction and validation for scanned codes
};
```

## Backup and Recovery Interface

- **Wallet backup creation** with encryption options
- **Recovery phrase display** with security warnings
- **Backup verification** and integrity checking
- **Cloud backup integration** with major providers
- **Partial recovery** for specific addresses or keys
- **Emergency recovery** procedures and documentation
- **Backup scheduling** and automated reminders
- **Recovery testing** without affecting live wallet

## Real-time Features and Notifications

- **Live balance updates** without page refresh
- **Transaction status notifications** with push support
- **Price alerts** for significant market movements
- **Security alerts** for unusual account activity
- **Network status** indicators and congestion warnings
- **Real-time exchange rates** with automatic updates
- **Transaction confirmations** with progress tracking
- **Market news** and updates relevant to holdings

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials, securityPin)
// - register(userData, securitySettings)
// - logout()
// - getCurrentUser()

// Wallet API functions:
// - getWalletBalance()
// - getAddresses()
// - generateNewAddress(currency, label)
// - createWallet(walletData)

// Transaction API functions:
// - sendTransaction(transactionData)
// - getTransactionHistory(filters)
// - getTransaction(transactionId)
// - confirmTransaction(transactionId, pin)

// Security API functions:
// - getSecuritySettings()
// - updateSecuritySettings(settings)
// - createBackup(backupOptions)
// - restoreWallet(backupData)

// Market API functions:
// - getExchangeRates()
// - getSupportedCurrencies()
// - getMarketData(currency)
```

## Configuration Files

### vite.config.js
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: XXXX,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:YYYY',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
```

### index.html
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Crypto Wallet</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/App.jsx"></script>
  </body>
</html>
```

## Response Requirements

1. **Port Configuration**
   - Use `XXXX` for frontend port in vite.config.js
   - Proxy API calls to backend on port `YYYY`

2. **Dependencies**
   - Generate complete package.json with all necessary npm dependencies
   - Include React, Vite, QR code libraries, cryptography libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Secure transaction processing with validation
   - Responsive design with mobile optimization
   - Proper state management for financial data
   - Performance optimization (efficient balance updates, caching)
   - Security compliance for financial applications
   - Clean code with comments
   - User experience enhancements (intuitive flows, clear feedback)
   - Progressive Web App features
   - Offline transaction preparation capabilities

**Very important:** Your frontend should be feature rich, production ready, and provide excellent cryptocurrency wallet experience with secure transaction interfaces, comprehensive portfolio management, advanced security controls, and responsive design optimized for financial operations and mobile use.