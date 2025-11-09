from fasthtml.common import *
from web3 import Web3
from dotenv import load_dotenv
import os
from datetime import datetime
from pathlib import Path
import requests
import urllib3
from audio_gen import generate_audio

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Configuration
RPC_URL = os.getenv('RPC_URL')
CHAIN_ID = int(os.getenv('CHAIN_ID', '5042002'))
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
OWNER_PRIVATE_KEY = os.getenv('OWNER_PRIVATE_KEY')
USDC_ADDRESS = os.getenv('USDC_ADDRESS')
RADIO_SERVER_URL = os.getenv('RADIO_SERVER_URL', 'https://localhost:5002')

# Sponsored messages directory
SPONSORED_DIR = Path("voices/sponsored")
SPONSORED_DIR.mkdir(parents=True, exist_ok=True)

# RadioSponsor Contract ABI
RADIO_SPONSOR_ABI = [
    {
        "type": "constructor",
        "inputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "submitBid",
        "inputs": [
            {"name": "_token", "type": "address", "internalType": "address"},
            {"name": "_amount", "type": "uint256", "internalType": "uint256"},
            {"name": "_transcript", "type": "string", "internalType": "string"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "acceptBid",
        "inputs": [
            {"name": "_bidId", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "rejectBid",
        "inputs": [
            {"name": "_bidId", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "getBid",
        "inputs": [
            {"name": "_bidId", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [
            {
                "name": "",
                "type": "tuple",
                "internalType": "struct RadioSponsor.Bid",
                "components": [
                    {"name": "bidder", "type": "address", "internalType": "address"},
                    {"name": "token", "type": "address", "internalType": "address"},
                    {"name": "amount", "type": "uint256", "internalType": "uint256"},
                    {"name": "transcript", "type": "string", "internalType": "string"},
                    {"name": "status", "type": "uint8", "internalType": "enum RadioSponsor.BidStatus"},
                    {"name": "timestamp", "type": "uint256", "internalType": "uint256"}
                ]
            }
        ],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "getPendingBidsCount",
        "inputs": [],
        "outputs": [
            {"name": "count", "type": "uint256", "internalType": "uint256"}
        ],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "nextBidId",
        "inputs": [],
        "outputs": [
            {"name": "", "type": "uint256", "internalType": "uint256"}
        ],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "bids",
        "inputs": [
            {"name": "", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [
            {"name": "bidder", "type": "address", "internalType": "address"},
            {"name": "token", "type": "address", "internalType": "address"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"},
            {"name": "transcript", "type": "string", "internalType": "string"},
            {"name": "status", "type": "uint8", "internalType": "enum RadioSponsor.BidStatus"},
            {"name": "timestamp", "type": "uint256", "internalType": "uint256"}
        ],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "owner",
        "inputs": [],
        "outputs": [
            {"name": "", "type": "address", "internalType": "address"}
        ],
        "stateMutability": "view"
    },
    {
        "type": "event",
        "name": "BidSubmitted",
        "inputs": [
            {"name": "bidId", "type": "uint256", "indexed": True, "internalType": "uint256"},
            {"name": "bidder", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "token", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"},
            {"name": "transcript", "type": "string", "indexed": False, "internalType": "string"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "BidAccepted",
        "inputs": [
            {"name": "bidId", "type": "uint256", "indexed": True, "internalType": "uint256"},
            {"name": "bidder", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "token", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "BidRejected",
        "inputs": [
            {"name": "bidId", "type": "uint256", "indexed": True, "internalType": "uint256"},
            {"name": "bidder", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "token", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    }
]

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Check connection
if not w3.is_connected():
    print(f"Warning: Unable to connect to {RPC_URL}")

# Create contract instance
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=RADIO_SPONSOR_ABI)

# Create account from private key
if OWNER_PRIVATE_KEY:
    account = w3.eth.account.from_key(OWNER_PRIVATE_KEY)
else:
    print("Warning: OWNER_PRIVATE_KEY not set")
    account = None

# Helper functions
def format_address(address):
    """Shorten address to 0x1234...5678 format"""
    return f"{address[:6]}...{address[-4:]}"

def format_amount(amount_wei, decimals=6):
    """Convert Wei to human-readable format (default USDC with 6 decimals)"""
    return float(amount_wei) / (10 ** decimals)

def format_timestamp(timestamp):
    """Convert Unix timestamp to readable format"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Contract interaction functions
def get_pending_bids():
    """Fetch all pending bids from the contract"""
    try:
        next_bid_id = contract.functions.nextBidId().call()
        pending_bids = []
        
        for bid_id in range(1, next_bid_id):
            try:
                bid = contract.functions.getBid(bid_id).call()
                # bid structure: (bidder, token, amount, transcript, status, timestamp)
                # status: 0=Pending, 1=Accepted, 2=Rejected
                if bid[4] == 0:  # Pending status
                    pending_bids.append({
                        'id': bid_id,
                        'bidder': bid[0],
                        'token': bid[1],
                        'amount': bid[2],
                        'transcript': bid[3],
                        'status': bid[4],
                        'timestamp': bid[5]
                    })
            except Exception as e:
                print(f"Error fetching bid {bid_id}: {e}")
                continue
        
        return pending_bids
    except Exception as e:
        print(f"Error in get_pending_bids: {e}")
        return []

def accept_bid(bid_id):
    """Accept a bid by sending a transaction and generate audio for radio"""
    try:
        if not account:
            return {"success": False, "message": "Owner account not configured"}
        
        # First, get the bid details to get the message
        try:
            bid = contract.functions.getBid(bid_id).call()
            bid_message = bid[3]  # transcript is at index 3
        except Exception as e:
            return {"success": False, "message": f"Error fetching bid details: {str(e)}"}
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(account.address)
        
        transaction = contract.functions.acceptBid(bid_id).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Sign transaction
        signed_txn = account.sign_transaction(transaction)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] != 1:
            return {"success": False, "message": "Transaction failed"}
        
        # Transaction successful! Now generate audio
        print(f"✅ Bid {bid_id} accepted on blockchain")
        print(f"📝 Generating audio for message: {bid_message[:50]}...")
        
        try:
            # Generate audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = SPONSORED_DIR / f"sponsored_{bid_id}_{timestamp}.wav"
            
            audio_files = generate_audio(
                text=bid_message,
                output_path=str(output_file),
                voice="bm_lewis",
                lang_code="a",
                speed=1.0
            )
            
            if not audio_files:
                return {"success": True, "message": f"Bid accepted but audio generation failed", "tx_hash": tx_hash.hex()}
            
            generated_file = audio_files[0]
            print(f"🎙️  Audio generated: {generated_file}")
            
            # Add to radio broadcast queue
            try:
                response = requests.get(
                    f"{RADIO_SERVER_URL}/radio/add_sponsored",
                    params={"audio_file": generated_file},
                    verify=False,  # Skip SSL verification for self-signed certs
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        print(f"📻 Added to radio queue successfully")
                        return {
                            "success": True,
                            "message": f"Bid {bid_id} accepted and scheduled to play on radio!",
                            "tx_hash": tx_hash.hex(),
                            "audio_file": generated_file
                        }
                    else:
                        print(f"⚠️  Radio API error: {result.get('error')}")
                        return {
                            "success": True,
                            "message": f"Bid accepted, audio generated, but radio queue failed: {result.get('error')}",
                            "tx_hash": tx_hash.hex(),
                            "audio_file": generated_file
                        }
                else:
                    print(f"⚠️  Radio server returned status {response.status_code}")
                    return {
                        "success": True,
                        "message": f"Bid accepted and audio generated, but radio server unreachable",
                        "tx_hash": tx_hash.hex(),
                        "audio_file": generated_file
                    }
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Failed to contact radio server: {e}")
                return {
                    "success": True,
                    "message": f"Bid accepted and audio generated, but radio server unreachable",
                    "tx_hash": tx_hash.hex(),
                    "audio_file": generated_file
                }
                
        except Exception as e:
            print(f"❌ Audio generation error: {e}")
            return {
                "success": True,
                "message": f"Bid accepted but audio generation failed: {str(e)}",
                "tx_hash": tx_hash.hex()
            }
            
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def reject_bid(bid_id):
    """Reject a bid by sending a transaction"""
    try:
        if not account:
            return {"success": False, "message": "Owner account not configured"}
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(account.address)
        
        transaction = contract.functions.rejectBid(bid_id).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Sign transaction
        signed_txn = account.sign_transaction(transaction)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            return {"success": True, "message": f"Bid {bid_id} rejected successfully", "tx_hash": tx_hash.hex()}
        else:
            return {"success": False, "message": "Transaction failed"}
            
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

# FastHTML app setup
app, rt = fast_app(debug=True)

# UI Components
def admin_styles():
    """CSS styles matching retro green-on-black aesthetic"""
    return Style("""
        body {
            margin: 0;
            padding: 20px;
            background-color: #000;
            color: #00ff00;
            font-family: monospace;
            overflow-x: hidden;
        }
        
        #ascii-header {
            text-align: center;
            line-height: 1.1;
            margin-bottom: 30px;
            font-size: 10px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1, h2 {
            color: #00ff00;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 30px;
        }
        
        .bids-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .bid-card {
            background-color: #001100;
            border: 2px solid #00ff00;
            padding: 20px;
            position: relative;
        }
        
        .bid-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #00ff00;
        }
        
        .bid-id {
            font-size: 18px;
            font-weight: bold;
            color: #00ff00;
        }
        
        .bid-timestamp {
            font-size: 12px;
            color: #00aa00;
        }
        
        .bid-info {
            margin-bottom: 15px;
        }
        
        .bid-info-row {
            display: flex;
            margin-bottom: 8px;
        }
        
        .bid-label {
            color: #00aa00;
            min-width: 100px;
            text-transform: uppercase;
        }
        
        .bid-value {
            color: #00ff00;
            flex: 1;
        }
        
        .bid-message {
            background-color: #000;
            border: 1px solid #00ff00;
            padding: 15px;
            margin-bottom: 15px;
            color: #00ff00;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .bid-actions {
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        
        .btn {
            background-color: #000;
            color: #00ff00;
            border: 2px solid #00ff00;
            padding: 10px 30px;
            font-family: monospace;
            font-size: 14px;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.2s;
        }
        
        .btn:hover {
            background-color: #00ff00;
            color: #000;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-approve {
            border-color: #00ff00;
            color: #00ff00;
        }
        
        .btn-approve:hover {
            background-color: #00ff00;
            color: #000;
        }
        
        .btn-reject {
            border-color: #ff0000;
            color: #ff0000;
        }
        
        .btn-reject:hover {
            background-color: #ff0000;
            color: #000;
        }
        
        .status-message {
            padding: 15px;
            margin: 20px 0;
            text-align: center;
            border: 2px solid;
            font-family: monospace;
        }
        
        .status-success {
            border-color: #00ff00;
            background-color: rgba(0, 255, 0, 0.1);
            color: #00ff00;
        }
        
        .status-error {
            border-color: #ff0000;
            background-color: rgba(255, 0, 0, 0.1);
            color: #ff0000;
        }
        
        .status-info {
            border-color: #00ffff;
            background-color: rgba(0, 255, 255, 0.1);
            color: #00ffff;
        }
        
        .no-bids {
            text-align: center;
            padding: 40px;
            color: #00aa00;
            font-size: 16px;
        }
        
        .refresh-btn {
            display: block;
            margin: 0 auto 30px auto;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #00ffff;
            font-size: 14px;
        }
    """)

def bid_card(bid):
    """Individual bid card component"""
    return Div(
        Div(
            Div(f"BID #{bid['id']}", cls="bid-id"),
            Div(format_timestamp(bid['timestamp']), cls="bid-timestamp"),
            cls="bid-header"
        ),
        Div(
            Div(
                Span("Bidder:", cls="bid-label"),
                Span(format_address(bid['bidder']), cls="bid-value"),
                cls="bid-info-row"
            ),
            Div(
                Span("Amount:", cls="bid-label"),
                Span(f"{format_amount(bid['amount'])} USDC", cls="bid-value"),
                cls="bid-info-row"
            ),
            Div(
                Span("Token:", cls="bid-label"),
                Span(format_address(bid['token']), cls="bid-value"),
                cls="bid-info-row"
            ),
            cls="bid-info"
        ),
        Div(
            Div("Message:", cls="bid-label", style="margin-bottom: 5px;"),
            Div(bid['transcript'], cls="bid-message"),
        ),
        Div(
            Button(
                "Approve",
                cls="btn btn-approve",
                hx_post=f"/approve/{bid['id']}",
                hx_target="#bids-list",
                hx_swap="outerHTML"
            ),
            Button(
                "Reject",
                cls="btn btn-reject",
                hx_post=f"/reject/{bid['id']}",
                hx_target="#bids-list",
                hx_swap="outerHTML"
            ),
            cls="bid-actions"
        ),
        cls="bid-card",
        id=f"bid-{bid['id']}"
    )

def bids_list_component(bids, message=None):
    """Component showing all bids with optional status message"""
    content = []
    
    if message:
        msg_class = "status-success" if message.get("success") else "status-error"
        content.append(
            Div(message.get("message", ""), cls=f"status-message {msg_class}")
        )
    
    if not bids:
        content.append(
            Div("No pending bids at the moment.", cls="no-bids")
        )
    else:
        content.append(
            Div(*[bid_card(bid) for bid in bids], cls="bids-container")
        )
    
    return Div(*content, id="bids-list")

# Routes
@rt('/')
def get():
    ascii_art = """d8888b. d8888b.  .d88b.  d8888b.  .d88b.   .d88b.   .d8b.  d8b   db d8888b.  .d8b.        .d8b.  d8888b. .88b  d88. d888888b d8b   db 
88  `8D 88  `8D .8P  Y8. 88  `8D .8P  Y8. .8P  Y8. d8' `8b 888o  88 88  `8D d8' `8b      d8' `8b 88  `8D 88'YbdP`88   `88'   888o  88 
88oodD' 88oobY' 88    88 88oodD' 88    88 88    88 88ooo88 88V8o 88 88   88 88ooo88      88ooo88 88   88 88  88  88    88    88V8o 88 
88~~~   88`8b   88    88 88~~~   88    88 88    88 88~~~88 88 V8o88 88   88 88~~~88      88~~~88 88   88 88  88  88    88    88 V8o88 
88      88 `88. `8b  d8' 88      `8b  d8' `8b  d8' 88   88 88  V888 88  .8D 88   88      88   88 88  .8D 88  88  88   .88.   88  V888 
88      88   YD  `Y88P'  88       `Y88P'   `Y88P'  YP   YP VP   V8P Y8888D' YP   YP      YP   YP Y8888D' YP  YP  YP Y888888P VP   V8P"""
    
    bids = get_pending_bids()
    
    return Html(
        Head(
            Title("Radio Sponsor Admin - Bid Manager"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
            admin_styles()
        ),
        Body(
            Div(
                Pre(ascii_art, id="ascii-header"),
                H1("Radio Sponsorship - Pending Bids"),
                Button(
                    "Refresh Bids",
                    cls="btn refresh-btn",
                    hx_get="/bids",
                    hx_target="#bids-list",
                    hx_swap="outerHTML"
                ),
                bids_list_component(bids),
                cls="container"
            )
        )
    )

@rt('/bids')
def get_bids():
    """HTMX endpoint to refresh bids list"""
    bids = get_pending_bids()
    return bids_list_component(bids)

@rt('/approve/{bid_id}')
def post(bid_id: int):
    """Approve a bid"""
    result = accept_bid(bid_id)
    bids = get_pending_bids()
    return bids_list_component(bids, message=result)

@rt('/reject/{bid_id}')
def post(bid_id: int):
    """Reject a bid"""
    result = reject_bid(bid_id)
    bids = get_pending_bids()
    return bids_list_component(bids, message=result)

if __name__ == '__main__':
    serve()

