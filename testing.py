from fasthtml.common import *

app, rt = fast_app(debug=True, static_path='static')

# Web3 component functions
def web3_styles():
    """CSS styles for Web3 wallet integration matching retro aesthetic"""
    return Style("""
        /* Wallet connection button */
        #wallet-section {
            text-align: center;
            margin: 30px 0;
            font-family: monospace;
        }
        
        #wallet-button, #bid-button {
            background-color: #000;
            color: #00ff00;
            border: 2px solid #00ff00;
            padding: 12px 24px;
            font-family: monospace;
            font-size: 16px;
            cursor: pointer;
            margin: 0 10px;
            text-transform: uppercase;
            transition: all 0.2s;
        }
        
        #wallet-button:hover, #bid-button:hover {
            background-color: #00ff00;
            color: #000;
        }
        
        #wallet-button:disabled, #bid-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        #wallet-status {
            margin-top: 10px;
            color: #00ff00;
            font-family: monospace;
            font-size: 14px;
        }
        
        /* Bid submission modal */
        #bid-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            z-index: 1000;
        }
        
        #bid-modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: #000;
            border: 2px solid #00ff00;
            padding: 30px;
            min-width: 400px;
            max-width: 600px;
            font-family: monospace;
        }
        
        #bid-modal h2 {
            color: #00ff00;
            text-align: center;
            margin-bottom: 20px;
            font-size: 18px;
            text-transform: uppercase;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: #00ff00;
            margin-bottom: 5px;
            font-size: 14px;
            text-transform: uppercase;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            background-color: #000;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 10px;
            font-family: monospace;
            font-size: 14px;
            box-sizing: border-box;
        }
        
        .form-group textarea {
            height: 100px;
            resize: vertical;
        }
        
        .form-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 25px;
        }
        
        .modal-button {
            background-color: #000;
            color: #00ff00;
            border: 2px solid #00ff00;
            padding: 12px 24px;
            font-family: monospace;
            font-size: 14px;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.2s;
        }
        
        .modal-button:hover {
            background-color: #00ff00;
            color: #000;
        }
        
        .modal-button.cancel {
            border-color: #666;
            color: #666;
        }
        
        .modal-button.cancel:hover {
            background-color: #666;
            color: #000;
        }
        
        .close-button {
            position: absolute;
            top: 10px;
            right: 15px;
            color: #00ff00;
            font-size: 20px;
            cursor: pointer;
            font-family: monospace;
            font-weight: bold;
        }
        
        .close-button:hover {
            color: #fff;
        }
        
        /* Status messages */
        #status-message {
            margin-top: 15px;
            padding: 10px;
            text-align: center;
            font-family: monospace;
            font-size: 14px;
            border: 1px solid;
        }
        
        #status-message.success {
            color: #00ff00;
            border-color: #00ff00;
            background-color: rgba(0, 255, 0, 0.1);
        }
        
        #status-message.error {
            color: #ff0000;
            border-color: #ff0000;
            background-color: rgba(255, 0, 0, 0.1);
        }
        
        #status-message.info {
            color: #00ffff;
            border-color: #00ffff;
            background-color: rgba(0, 255, 255, 0.1);
        }
        
        .hidden {
            display: none !important;
        }
    """)

def wallet_button():
    """Wallet connection button component"""
    return Div(
        Button("Connect Wallet", id="wallet-button", onclick="connectWallet()"),
        Button("Submit Bid", id="bid-button", onclick="openBidModal()", class_="hidden"),
        Div(id="wallet-status", class_="hidden"),
        id="wallet-section"
    )

def bid_modal():
    """Bid submission modal component"""
    return Div(
        Div(
            Span("×", class_="close-button", onclick="closeBidModal()"),
            H2("Submit Sponsorship Bid"),
            Form(
                Div(
                    Label("Token Address:", for_="token-address"),
                    Select(
                        Option("Select a token...", value="", disabled=True, selected=True),
                        Option("USDC (Mock)", value="0x..."),  # Will be updated with actual addresses
                        Option("USDT (Mock)", value="0x..."),
                        Option("DAI (Mock)", value="0x..."),
                        name="token-address",
                        id="token-address",
                        required=True
                    ),
                    class_="form-group"
                ),
                Div(
                    Label("Amount:", for_="bid-amount"),
                    Input(
                        type="number",
                        name="bid-amount", 
                        id="bid-amount",
                        placeholder="Enter amount (e.g., 100)",
                        step="0.000001",
                        min="0",
                        required=True
                    ),
                    class_="form-group"
                ),
                Div(
                    Label("Sponsorship Message:", for_="bid-message"),
                    Textarea(
                        name="bid-message",
                        id="bid-message", 
                        placeholder="Enter your radio sponsorship message...",
                        rows="4",
                        required=True
                    ),
                    class_="form-group"
                ),
                Div(
                    Button("Submit Bid", type="button", class_="modal-button", onclick="submitBid()"),
                    Button("Cancel", type="button", class_="modal-button cancel", onclick="closeBidModal()"),
                    class_="form-buttons"
                ),
                onsubmit="event.preventDefault(); submitBid();"
            ),
            Div(id="status-message", class_="hidden"),
            id="bid-modal-content"
        ),
        id="bid-modal",
        onclick="if(event.target === this) closeBidModal()"
    )

def web3_scripts():
    """JavaScript for Web3 wallet integration using Viem"""
    return Script("""
        // Import Viem from CDN
        import { createPublicClient, createWalletClient, custom, http, parseEther, formatEther } from 'https://esm.sh/viem@2.7.0';
        import { defineChain } from 'https://esm.sh/viem@2.7.0/chains';
        
        // Define ARC Testnet chain
        const arcTestnet = defineChain({
            id: 1209,
            name: 'ARC Testnet',
            network: 'arc-testnet',
            nativeCurrency: {
                decimals: 18,
                name: 'ARC',
                symbol: 'ARC',
            },
            rpcUrls: {
                default: { http: ['https://rpc.testnet.arc.network'] },
                public: { http: ['https://rpc.testnet.arc.network'] },
            },
            blockExplorers: {
                default: { name: 'Explorer', url: 'https://explorer.testnet.arc.network' },
            },
        });
        
        // RadioSponsor contract configuration
        const RADIO_SPONSOR_ADDRESS = '0x0000000000000000000000000000000000000000'; // TODO: Replace with deployed contract address
        
        // RadioSponsor ABI (key functions only)
        const RADIO_SPONSOR_ABI = [
            {
                "type": "function",
                "name": "submitBid",
                "inputs": [
                    {"name": "_token", "type": "address"},
                    {"name": "_amount", "type": "uint256"},
                    {"name": "_transcript", "type": "string"}
                ],
                "outputs": [],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "nextBidId",
                "inputs": [],
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view"
            }
        ];
        
        // ERC20 ABI for token approval
        const ERC20_ABI = [
            {
                "type": "function",
                "name": "approve",
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "allowance",
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"}
                ],
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view"
            }
        ];
        
        // Global state
        let walletClient = null;
        let publicClient = null;
        let userAddress = null;
        
        // Initialize public client
        publicClient = createPublicClient({
            chain: arcTestnet,
            transport: http()
        });
        
        // Status message helper
        function showStatus(message, type = 'info') {
            const statusEl = document.getElementById('status-message');
            statusEl.textContent = message;
            statusEl.className = type;
            statusEl.classList.remove('hidden');
            
            if (type === 'success') {
                setTimeout(() => {
                    statusEl.classList.add('hidden');
                }, 5000);
            }
        }
        
        // Connect wallet function
        window.connectWallet = async function() {
            try {
                if (!window.ethereum) {
                    showStatus('Please install MetaMask or another Web3 wallet', 'error');
                    return;
                }
                
                // Request account access
                const accounts = await window.ethereum.request({ 
                    method: 'eth_requestAccounts' 
                });
                
                userAddress = accounts[0];
                
                // Create wallet client
                walletClient = createWalletClient({
                    chain: arcTestnet,
                    transport: custom(window.ethereum)
                });
                
                // Check if on correct network
                const chainId = await window.ethereum.request({ method: 'eth_chainId' });
                if (parseInt(chainId) !== arcTestnet.id) {
                    try {
                        await window.ethereum.request({
                            method: 'wallet_switchEthereumChain',
                            params: [{ chainId: '0x' + arcTestnet.id.toString(16) }],
                        });
                    } catch (switchError) {
                        if (switchError.code === 4902) {
                            await window.ethereum.request({
                                method: 'wallet_addEthereumChain',
                                params: [{
                                    chainId: '0x' + arcTestnet.id.toString(16),
                                    chainName: arcTestnet.name,
                                    nativeCurrency: arcTestnet.nativeCurrency,
                                    rpcUrls: [arcTestnet.rpcUrls.default.http[0]],
                                    blockExplorerUrls: [arcTestnet.blockExplorers.default.url]
                                }]
                            });
                        } else {
                            throw switchError;
                        }
                    }
                }
                
                // Update UI
                const walletButton = document.getElementById('wallet-button');
                const bidButton = document.getElementById('bid-button');
                const statusDiv = document.getElementById('wallet-status');
                
                walletButton.textContent = userAddress.substring(0, 6) + '...' + userAddress.substring(38);
                walletButton.onclick = disconnectWallet;
                bidButton.classList.remove('hidden');
                statusDiv.textContent = 'Connected to ARC Testnet';
                statusDiv.classList.remove('hidden');
                
            } catch (error) {
                console.error('Wallet connection error:', error);
                showStatus('Failed to connect wallet: ' + error.message, 'error');
            }
        };
        
        // Disconnect wallet function
        window.disconnectWallet = function() {
            walletClient = null;
            userAddress = null;
            
            const walletButton = document.getElementById('wallet-button');
            const bidButton = document.getElementById('bid-button');
            const statusDiv = document.getElementById('wallet-status');
            
            walletButton.textContent = 'Connect Wallet';
            walletButton.onclick = connectWallet;
            bidButton.classList.add('hidden');
            statusDiv.classList.add('hidden');
        };
        
        // Open bid modal
        window.openBidModal = function() {
            if (!userAddress) {
                showStatus('Please connect your wallet first', 'error');
                return;
            }
            document.getElementById('bid-modal').style.display = 'block';
        };
        
        // Close bid modal
        window.closeBidModal = function() {
            document.getElementById('bid-modal').style.display = 'none';
            document.getElementById('status-message').classList.add('hidden');
        };
        
        // Submit bid function
        window.submitBid = async function() {
            try {
                if (!walletClient || !userAddress) {
                    showStatus('Please connect your wallet first', 'error');
                    return;
                }
                
                // Get form values
                const tokenAddress = document.getElementById('token-address').value;
                const amount = document.getElementById('bid-amount').value;
                const message = document.getElementById('bid-message').value;
                
                if (!tokenAddress || !amount || !message) {
                    showStatus('Please fill in all fields', 'error');
                    return;
                }
                
                showStatus('Preparing transaction...', 'info');
                
                // Convert amount to Wei (assuming 18 decimals)
                const amountWei = parseEther(amount);
                
                // Check and approve token if needed
                showStatus('Checking token allowance...', 'info');
                const allowance = await publicClient.readContract({
                    address: tokenAddress,
                    abi: ERC20_ABI,
                    functionName: 'allowance',
                    args: [userAddress, RADIO_SPONSOR_ADDRESS]
                });
                
                if (allowance < amountWei) {
                    showStatus('Approving token spend...', 'info');
                    const approveTx = await walletClient.writeContract({
                        address: tokenAddress,
                        abi: ERC20_ABI,
                        functionName: 'approve',
                        args: [RADIO_SPONSOR_ADDRESS, amountWei],
                        account: userAddress
                    });
                    
                    showStatus('Waiting for approval confirmation...', 'info');
                    await publicClient.waitForTransactionReceipt({ hash: approveTx });
                }
                
                // Submit bid to contract
                showStatus('Submitting bid...', 'info');
                const bidTx = await walletClient.writeContract({
                    address: RADIO_SPONSOR_ADDRESS,
                    abi: RADIO_SPONSOR_ABI,
                    functionName: 'submitBid',
                    args: [tokenAddress, amountWei, message],
                    account: userAddress
                });
                
                showStatus('Waiting for transaction confirmation...', 'info');
                await publicClient.waitForTransactionReceipt({ hash: bidTx });
                
                showStatus('Bid submitted successfully!', 'success');
                
                // Reset form
                document.getElementById('token-address').value = '';
                document.getElementById('bid-amount').value = '';
                document.getElementById('bid-message').value = '';
                
                // Close modal after a delay
                setTimeout(() => {
                    closeBidModal();
                }, 2000);
                
            } catch (error) {
                console.error('Bid submission error:', error);
                showStatus('Failed to submit bid: ' + error.message, 'error');
            }
        };
        
        // Handle account changes
        if (window.ethereum) {
            window.ethereum.on('accountsChanged', function (accounts) {
                if (accounts.length === 0) {
                    disconnectWallet();
                } else if (accounts[0] !== userAddress) {
                    userAddress = accounts[0];
                    const walletButton = document.getElementById('wallet-button');
                    walletButton.textContent = userAddress.substring(0, 6) + '...' + userAddress.substring(38);
                }
            });
            
            window.ethereum.on('chainChanged', function () {
                window.location.reload();
            });
        }
    """, type="module")

# Custom route to serve STL files (not in default static extensions)
@rt("/{fname:path}.stl")
def get_stl(fname: str):
    return FileResponse(f'static/{fname}.stl')

@rt('/')
def get():
    ascii_art = """d8888b. d8888b.  .d88b.  d8888b.  .d88b.   d888b   .d8b.  d8b   db d8888b.  .d8b.        .d8b.  db    db d888888b  .d88b.  .88b  d88.  .d8b.  d888888b  .d88b.  d8b   db 
88  `8D 88  `8D .8P  Y8. 88  `8D .8P  Y8. 88' Y8b d8' `8b 888o  88 88  `8D d8' `8b      d8' `8b 88    88 `~~88~~' .8P  Y8. 88'Ybd`88 d8' `8b `~~88~~' .8P  Y8. 888o  88 
88oodD' 88oobY' 88    88 88oodD' 88    88 88      88ooo88 88V8o 88 88   88 88ooo88      88ooo88 88    88    88    88    88 88  88  88 88ooo88    88    88    88 88V8o 88 
88~~~   88`8b   88    88 88~~~   88    88 88  ooo 88~~~88 88 V8o88 88   88 88~~~88      88~~~88 88    88    88    88    88 88  88  88 88~~~88    88    88    88 88 V8o88 
88      88 `88. `8b  d8' 88      `8b  d8' 88. ~8~ 88   88 88  V888 88  .8D 88   88      88   88 88b  d88    88    `8b  d8' 88  88  88 88   88    88    `8b  d8' 88  V888 
88      88   YD  `Y88P'  88       `Y88P'   Y888P  YP   YP VP   V8P Y8888D' YP   YP      YP   YP ~Y8888P'    YP     `Y88P'  YP  YP  YP YP   YP    YP     `Y88P'  VP   V8P"""
    
    return Html(
        Head(
            Title("Propaganda Automation"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            # Import map for Three.js ES6 modules
            Script("""{
                "imports": {
                    "three": "https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.module.js",
                    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/"
                }
            }""", type="importmap"),
            Style("""
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
                }
                #ascii-container {
                    width: 100%;
                    height: 600px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
            """),
            web3_styles()
        ),
        Body(
            Pre(ascii_art, id="ascii-header"),
            wallet_button(),
            Div(id="ascii-container"),
            Script("""
                // ES6 Module imports
                import * as THREE from 'three';
                import { STLLoader } from 'three/addons/loaders/STLLoader.js';
                import { AsciiEffect } from '/AsciiEffect.js';

                // ========== CONFIGURATION VARIABLES ==========
                // Adjust these to orient and size the model as desired
                const rotationOffsetX = -1.57;      // Rotation around X axis (radians)
                const rotationOffsetY = 0;      // Rotation around Y axis (radians)
                const rotationOffsetZ = 0;      // Rotation around Z axis (radians)
                const sizeMultiplier = 1.0;     // Scale multiplier (1.0 = original size)
                const autoRotationSpeed = 0.01; // Speed of continuous rotation
                const aspectRatioDivisor = 1.0; // Divisor for aspect ratio
                // ============================================

                // Simplified version - just rotating FDR model
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x000000);

                // Lighting
                const pointLight = new THREE.PointLight(0xffffff, 1, 0, 0);
                pointLight.position.set(100, 100, 400);
                scene.add(pointLight);

                // Camera
                const camera = new THREE.PerspectiveCamera(
                    45,
                    window.innerWidth / (600 * aspectRatioDivisor * 1.6),
                    0.1,
                    2000
                );

                // Renderer
                const renderer = new THREE.WebGLRenderer();

                // ASCII Effect
                const characters = ' .:-+*=%@#';
                const effect = new AsciiEffect(
                    renderer,
                    characters,
                    { invert: true, resolution: 0.15, scale: 2 }
                );
                effect.setSize(window.innerWidth, 600 * aspectRatioDivisor);
                effect.domElement.style.color = 'white';
                effect.domElement.style.backgroundColor = 'black';

                document.getElementById('ascii-container').appendChild(effect.domElement);

                // Material
                const material = new THREE.MeshStandardMaterial({
                    flatShading: true,
                    side: THREE.DoubleSide
                });

                // Load FDR STL
                const loader = new STLLoader();
                let mesh;

                loader.load('/fdr.stl', function(geometry) {
                    geometry.computeVertexNormals();
                    geometry.center(); // Center the geometry at origin

                    mesh = new THREE.Mesh(geometry, material);

                    // Calculate camera position BEFORE scaling (using original geometry size)
                    geometry.computeBoundingBox();
                    const bbox = geometry.boundingBox;
                    const size = new THREE.Vector3();
                    bbox.getSize(size);
                    const maxDim = Math.max(size.x, size.y, size.z);

                    // Position camera based on ORIGINAL (unscaled) size
                    camera.position.set(maxDim * 1.5, maxDim * 0.5, maxDim * 2);
                    camera.lookAt(0, 0, 0);

                    // NOW apply size multiplier (after camera is positioned)
                    mesh.scale.set(sizeMultiplier, sizeMultiplier, sizeMultiplier);

                    // Apply rotation offsets for initial orientation
                    mesh.rotation.x = rotationOffsetX;
                    mesh.rotation.y = rotationOffsetY;
                    mesh.rotation.z = rotationOffsetZ;

                    // Center the mesh at origin (0, 0, 0)
                    mesh.position.set(0, 0, 0);

                    scene.add(mesh);

                    // Start animation
                    animate();
                });

                function animate() {
                    requestAnimationFrame(animate);

                    if (mesh) {
                        mesh.rotation.z += autoRotationSpeed; // Rotate continuously
                    }

                    effect.render(scene, camera);
                }

                // Handle window resize
                window.addEventListener('resize', function() {
                    camera.aspect = window.innerWidth / (600 * aspectRatioDivisor * 1.6);
                    camera.updateProjectionMatrix();
                    effect.setSize(window.innerWidth, 600 * aspectRatioDivisor);
                });
            """, type="module"),
            bid_modal(),
            web3_scripts()
        )
    )

serve()