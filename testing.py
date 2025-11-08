from fasthtml.common import *

app, rt = fast_app(debug=True, static_path='static')

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
            """)
        ),
        Body(
            Pre(ascii_art, id="ascii-header"),
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
            """, type="module")
        )
    )

serve()