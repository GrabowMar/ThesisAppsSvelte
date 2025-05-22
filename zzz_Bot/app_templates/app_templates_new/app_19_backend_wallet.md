# Backend Generation Prompt - Flask Crypto Wallet Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/wallet`, `/api/transactions`, `/api/addresses`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Crypto Wallet System Backend**  
A comprehensive Flask backend for cryptocurrency wallet application, featuring secure wallet management, transaction processing, address generation, balance tracking, and security features with encryption and validation.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Secure wallet creation and management
- Real-time balance checking and tracking
- Send and receive transaction functionality
- Comprehensive transaction history and logging
- Address generation and management system
- Security features with encryption and authentication
- Multi-currency support with exchange rates
- Transaction validation and confirmation
- Backup and recovery capabilities
- User authentication with enhanced security
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import uuid
import hashlib
import secrets
from cryptography.fernet import Fernet
import json
import requests
from decimal import Decimal

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Cryptographic Functions
# 5. Transaction Processing
# 6. Address Management
# 7. API Routes:
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - POST /api/wallet/create (create wallet)
#    - GET /api/wallet/balance (get balance)
#    - GET /api/wallet/addresses (get addresses)
#    - POST /api/wallet/addresses (generate new address)
#    - POST /api/transactions/send (send transaction)
#    - POST /api/transactions/receive (process received transaction)
#    - GET /api/transactions/history (get transaction history)
#    - GET /api/transactions/<id> (get transaction details)
#    - POST /api/transactions/<id>/confirm (confirm transaction)
#    - GET /api/currencies (get supported currencies)
#    - GET /api/exchange-rates (get current exchange rates)
#    - POST /api/wallet/backup (create wallet backup)
#    - POST /api/wallet/restore (restore wallet from backup)
#    - GET /api/security/settings (get security settings)
#    - PUT /api/security/settings (update security settings)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, security_pin
   - Validate input and create secure user account
   - Generate wallet encryption keys
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password, security_pin
   - Validate credentials with enhanced security
   - Create secure user session
   - Return user info and wallet status

3. **POST /api/auth/logout**
   - Clear user session securely
   - Invalidate active tokens
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include security settings and preferences

### Wallet Management Routes

5. **POST /api/wallet/create**
   - Create new cryptocurrency wallet
   - Generate secure private/public key pairs
   - Initialize wallet with default settings
   - Return wallet information and addresses

6. **GET /api/wallet/balance**
   - Return current wallet balances
   - Include balances for all supported currencies
   - Show pending and confirmed amounts
   - Calculate total value in user's preferred currency

7. **GET /api/wallet/addresses**
   - Return list of wallet addresses
   - Include address types and purposes
   - Show usage history and balance for each
   - Support address labeling and organization

8. **POST /api/wallet/addresses**
   - Generate new wallet address
   - Accept: currency_type, label, purpose
   - Create secure address with proper validation
   - Return new address details

### Transaction Routes

9. **POST /api/transactions/send**
   - Process outgoing transaction
   - Accept: recipient_address, amount, currency, fee_level
   - Validate transaction details and sufficient balance
   - Create and broadcast transaction
   - Return transaction ID and status

10. **POST /api/transactions/receive**
    - Process incoming transaction notification
    - Accept: transaction_hash, amount, sender_address
    - Validate and confirm incoming transaction
    - Update wallet balance and history

11. **GET /api/transactions/history**
    - Return transaction history
    - Support filtering by date, amount, currency, type
    - Include transaction status and confirmations
    - Support pagination for large histories

12. **GET /api/transactions/<id>**
    - Return specific transaction details
    - Include full transaction data and status
    - Show confirmations and network fees
    - Display related addresses and amounts

13. **POST /api/transactions/<id>/confirm**
    - Confirm pending transaction
    - Accept: confirmation_code, security_pin
    - Validate user authorization
    - Broadcast confirmed transaction

### Currency and Exchange Routes

14. **GET /api/currencies**
    - Return list of supported cryptocurrencies
    - Include currency details and network info
    - Show current market prices and trends
    - Display wallet support status for each

15. **GET /api/exchange-rates**
    - Return current exchange rates
    - Include rates for all supported currencies
    - Show historical rate data
    - Calculate conversion rates

### Security and Backup Routes

16. **POST /api/wallet/backup**
    - Create encrypted wallet backup
    - Accept: backup_password, backup_type
    - Generate secure backup file
    - Return backup confirmation and recovery info

17. **POST /api/wallet/restore**
    - Restore wallet from backup
    - Accept: backup_data, backup_password
    - Validate and decrypt backup
    - Restore wallet state and addresses

18. **GET /api/security/settings**
    - Return user security settings
    - Include 2FA status, PIN settings, notifications
    - Show security recommendations

19. **PUT /api/security/settings**
    - Update security settings
    - Accept: 2fa_enabled, notification_preferences, security_level
    - Validate and apply security changes
    - Return updated settings

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- security_pin_hash (TEXT)
- encryption_key (TEXT)
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)
- two_factor_enabled (BOOLEAN DEFAULT FALSE)
- security_level (TEXT DEFAULT 'standard')

Wallets table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- wallet_name (TEXT)
- encrypted_private_key (TEXT)
- public_key (TEXT)
- created_at (TIMESTAMP)
- is_active (BOOLEAN DEFAULT TRUE)
- backup_status (TEXT DEFAULT 'none')

Addresses table:
- id (TEXT PRIMARY KEY)
- wallet_id (TEXT)
- address (TEXT UNIQUE NOT NULL)
- currency_type (TEXT)
- address_type (TEXT) -- 'receiving', 'change'
- label (TEXT)
- created_at (TIMESTAMP)
- last_used (TIMESTAMP)
- transaction_count (INTEGER DEFAULT 0)

Transactions table:
- id (TEXT PRIMARY KEY)
- wallet_id (TEXT)
- transaction_hash (TEXT UNIQUE)
- transaction_type (TEXT) -- 'send', 'receive'
- from_address (TEXT)
- to_address (TEXT)
- amount (DECIMAL)
- currency (TEXT)
- fee_amount (DECIMAL)
- status (TEXT) -- 'pending', 'confirmed', 'failed'
- confirmations (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)
- confirmed_at (TIMESTAMP)
- notes (TEXT)

Balances table:
- wallet_id (TEXT)
- currency (TEXT)
- available_balance (DECIMAL)
- pending_balance (DECIMAL)
- total_balance (DECIMAL)
- last_updated (TIMESTAMP)

Exchange_Rates table:
- currency_pair (TEXT PRIMARY KEY)
- rate (DECIMAL)
- last_updated (TIMESTAMP)
- source (TEXT)

Security_Logs table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- action (TEXT)
- ip_address (TEXT)
- user_agent (TEXT)
- success (BOOLEAN)
- created_at (TIMESTAMP)
- details (TEXT)
```

## Cryptocurrency Features

- **Multi-currency support** with Bitcoin, Ethereum, and major altcoins
- **HD wallet functionality** with hierarchical deterministic address generation
- **Transaction fee estimation** with multiple fee levels (slow, normal, fast)
- **Address validation** and format checking for different currencies
- **Transaction broadcasting** to respective blockchain networks
- **Confirmation tracking** with real-time status updates
- **Exchange rate integration** with multiple price sources
- **Portfolio valuation** with real-time market prices

## Security Features

- **Private key encryption** with user-controlled passwords
- **Two-factor authentication** support with TOTP
- **Transaction signing** with secure key management
- **PIN-based transaction approval** for enhanced security
- **Session management** with automatic timeouts
- **Backup encryption** with recovery phrase generation
- **Audit logging** for all security-related actions
- **Rate limiting** for transaction and authentication attempts

## Transaction Processing Features

- **Transaction validation** before broadcasting
- **Fee calculation** with network congestion consideration
- **Batch transaction** support for efficiency
- **Transaction replacement** (RBF) for stuck transactions
- **Multi-signature support** for enhanced security
- **Transaction labeling** and categorization
- **Export functionality** for tax reporting
- **Transaction monitoring** with real-time updates

## Backup and Recovery Features

- **Encrypted wallet backups** with password protection
- **Recovery phrase generation** following BIP39 standards
- **Partial backup** options for addresses and transactions
- **Cloud backup integration** with encryption
- **Backup verification** and integrity checking
- **Automated backup scheduling** with user preferences
- **Recovery testing** without affecting live wallet
- **Emergency recovery** procedures and documentation

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, cryptography, blockchain libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Cryptographic security implementation
   - Transaction validation and processing
   - Balance calculation accuracy
   - Address generation and management
   - Security logging and monitoring
   - Performance optimization for crypto operations
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all cryptocurrency wallet scenarios including secure key management, transaction processing, balance tracking, and security features with proper encryption and validation measures.