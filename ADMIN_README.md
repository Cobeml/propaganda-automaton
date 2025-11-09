# Radio Sponsor Admin Panel

A FastHTML-based admin interface for managing RadioSponsor contract bids.

## Features

- View all pending sponsorship bids
- Approve or reject bids with server-side transaction signing
- Real-time updates using HTMX
- Retro green-on-black terminal aesthetic
- Automatic transaction confirmation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Make sure your `.env` file contains:

```env
# ARC Network Configuration
RPC_URL=https://rpc.testnet.arc.network
CHAIN_ID=1209

# RadioSponsor Contract
CONTRACT_ADDRESS=0x...  # Your deployed contract address

# Owner Wallet (for signing transactions)
OWNER_PRIVATE_KEY=0x...  # Private key of contract owner

# Token Addresses
USDC_ADDRESS=0x...  # USDC token contract address
```

**⚠️ Security Note:** Keep your `.env` file secure and never commit it to version control.

### 3. Run the Admin Panel

```bash
python admin.py
```

The admin panel will start on `http://localhost:5001` (or the default FastHTML port).

## Usage

### Viewing Bids

The main page displays all pending bids with:
- Bid ID and timestamp
- Bidder address (shortened)
- Bid amount in USDC
- Token address
- Sponsorship message

### Approving a Bid

1. Click the **Approve** button on any bid
2. The server will sign and send the transaction
3. Wait for confirmation (transaction status will be displayed)
4. The bid list will refresh automatically

When approved, the tokens are transferred to the contract owner's address.

### Rejecting a Bid

1. Click the **Reject** button on any bid
2. The server will sign and send the transaction
3. Wait for confirmation
4. The bid list will refresh automatically

When rejected, the tokens are refunded to the original bidder.

### Manual Refresh

Click the **Refresh Bids** button at the top to manually reload the pending bids list.

## Technical Details

### Contract Interaction

- Uses `web3.py` for Ethereum blockchain interaction
- Connects to ARC Testnet via RPC URL
- Server-side transaction signing with owner's private key
- Automatic gas price estimation
- Transaction receipt confirmation (120 second timeout)

### USDC Decimals

The application assumes USDC uses 6 decimals (standard for USDC). Amounts are displayed in human-readable format (e.g., "100.00 USDC" instead of "100000000").

### HTMX Integration

- Dynamic updates without full page reloads
- Approve/Reject actions use HTMX POST requests
- Status messages displayed after each action
- Automatic bid list refresh after transactions

## Troubleshooting

### "Unable to connect to RPC"

Check that:
- `RPC_URL` in `.env` is correct
- You have internet connectivity
- The ARC Testnet is online

### "Owner account not configured"

Ensure `OWNER_PRIVATE_KEY` is set in your `.env` file.

### Transaction Fails

Possible reasons:
- Insufficient gas in owner's wallet
- Bid already processed
- Network congestion
- Invalid bid ID

### No Bids Showing

- Check that the `CONTRACT_ADDRESS` is correct
- Verify the contract has pending bids using a block explorer
- Ensure the RPC connection is working

## Security Considerations

- This admin panel is designed for **local use only**
- No authentication is implemented
- Private key is stored in `.env` (server-side)
- Never expose this admin panel to the public internet
- Always use HTTPS if deploying remotely
- Consider adding authentication for production use

## Architecture

```
admin.py
├── Web3 Setup (connection, contract, account)
├── Helper Functions (formatting, conversions)
├── Contract Functions
│   ├── get_pending_bids() - Query pending bids
│   ├── accept_bid() - Approve and transfer tokens
│   └── reject_bid() - Reject and refund tokens
├── UI Components
│   ├── admin_styles() - CSS styling
│   ├── bid_card() - Individual bid display
│   └── bids_list_component() - Full bids list
└── Routes
    ├── GET / - Main page
    ├── GET /bids - Refresh bids list
    ├── POST /approve/{bid_id} - Approve bid
    └── POST /reject/{bid_id} - Reject bid
```

## Future Enhancements

Potential improvements:
- Add authentication/authorization
- Display transaction history
- Show accepted/rejected bids
- Email/webhook notifications for new bids
- Batch approve/reject functionality
- Export bids to CSV
- Real-time updates via WebSockets

