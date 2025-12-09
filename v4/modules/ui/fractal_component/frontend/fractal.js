/**
 * Fractal Navigation Component - JavaScript Implementation
 *
 * Interactive Sierpinski triangle navigation with adaptive geometric patterns.
 * Supports multi-level hierarchical exploration of financial data.
 *
 * @author djabi
 * @version 1.0
 * @date 2025-11-22
 */

// ==============================
// GLOBAL STATE
// ==============================

let hierarchyData = {};
let currentNode = 'TR';
let navigationStack = ['TR'];
let hoveredTriangle = null;
let animationInProgress = false;
const ANIMATION_DURATION = 350; // ms - réduit de 700ms pour plus de réactivité
const FRAME_RATE = 60;
const FRAMES_PER_ANIMATION = Math.round(ANIMATION_DURATION / (1000 / FRAME_RATE));

// Throttle mousemove to prevent excessive redraws
let lastMouseMoveTime = 0;
const MOUSEMOVE_THROTTLE = 16; // ~60fps = 16ms between redraws

// Canvas setup
let canvas, ctx, rect;
let canvasWidth, canvasHeight;
let triangles = [];
let centerX, centerY;

// ==============================
// INITIALIZATION
// ==============================

/**
 * Initialize the component when Streamlit sends data
 */
Streamlit.setComponentValue(null);

window.addEventListener('load', () => {
    canvas = document.getElementById('fractalCanvas');
    ctx = canvas.getContext('2d');

    // Set canvas size
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Streamlit data handler
    Streamlit.setFrameHeight(document.body.scrollHeight);

    // Listen for data from Streamlit
    window.parent.addEventListener('streamlit:render', () => {
        const receivedData = Streamlit.getComponentValue();
        if (receivedData && receivedData.data) {
            hierarchyData = receivedData.data;
            currentNode = 'TR';
            navigationStack = ['TR'];
            update();
        }
    });

    // Button handlers
    document.getElementById('backBtn').addEventListener('click', handleBack);
    document.getElementById('resetBtn').addEventListener('click', handleReset);

    // Canvas interaction
    canvas.addEventListener('click', handleCanvasClick);
    canvas.addEventListener('mousemove', handleCanvasMouseMove);
    canvas.addEventListener('mouseleave', handleCanvasMouseLeave);

    // Initial render
    update();
});

/**
 * Resize canvas to fill container
 */
function resizeCanvas() {
    const container = document.querySelector('.fractal-container');
    canvasWidth = container.clientWidth || window.innerWidth;
    canvasHeight = container.clientHeight || window.innerHeight;

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    centerX = canvasWidth / 2;
    centerY = canvasHeight / 2;
}

// ==============================
// MAIN UPDATE & RENDER
// ==============================

/**
 * Main update and render loop
 */
function update() {
    if (animationInProgress) return;

    const node = hierarchyData[currentNode];
    if (!node) {
        renderErrorState();
        return;
    }

    // Update UI
    updateInfoPanel(node);
    updateBreadcrumb(node);
    updateZoomIndicator();
    updateControlButtons();

    // Render triangles
    render(node);
}

/**
 * Render the current state
 */
function render(node) {
    // Clear canvas
    ctx.fillStyle = 'rgba(15, 23, 42, 0.05)';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Get triangles for current level
    triangles = [];

    const childCount = node.children.length;

    if (childCount === 0) {
        // Leaf node - show message
        renderLeafNodeMessage();
        return;
    }

    // Determine pattern based on child count
    if (childCount === 1) {
        triangles = getRenderSingleTriangle(node.children[0]);
    } else if (childCount === 2) {
        triangles = getRenderTwoTriangles(node);
    } else if (childCount === 3) {
        triangles = getRenderThreeTriangles(node);
    } else if (childCount === 4) {
        triangles = getRenderFourTriangles(node);
    } else if (childCount === 5) {
        triangles = getRenderFiveTriangles(node);
    } else if (childCount === 6) {
        triangles = getRenderSixTriangles(node);
    } else {
        triangles = getRenderManyTriangles(node);
    }

    // Draw all triangles
    triangles.forEach((tri, idx) => {
        const childCode = node.children[idx];
        const childNode = hierarchyData[childCode];

        drawTriangle(tri, childNode, idx);
    });
}

// ==============================
// GEOMETRIC PATTERNS
// ==============================

/**
 * Single triangle - center
 */
function getRenderSingleTriangle(code) {
    const triangleSize = 150;
    const height = (triangleSize * Math.sqrt(3)) / 2;

    return [{
        p1: { x: centerX - triangleSize / 2, y: centerY + height / 2 },
        p2: { x: centerX + triangleSize / 2, y: centerY + height / 2 },
        p3: { x: centerX, y: centerY - height / 2 },
        code: code
    }];
}

/**
 * Two triangles - Revenus (left) / Dépenses (right)
 */
function getRenderTwoTriangles(node) {
    const triangleSize = 120;
    const height = (triangleSize * Math.sqrt(3)) / 2;
    const spacing = 100;

    return [
        {
            p1: { x: centerX - spacing - triangleSize / 2, y: centerY + height / 2 },
            p2: { x: centerX - spacing + triangleSize / 2, y: centerY + height / 2 },
            p3: { x: centerX - spacing, y: centerY - height / 2 },
            code: node.children[0]
        },
        {
            p1: { x: centerX + spacing - triangleSize / 2, y: centerY + height / 2 },
            p2: { x: centerX + spacing + triangleSize / 2, y: centerY + height / 2 },
            p3: { x: centerX + spacing, y: centerY - height / 2 },
            code: node.children[1]
        }
    ];
}

/**
 * Three triangles - Sierpinski closed triangle
 */
function getRenderThreeTriangles(node) {
    const triangleSize = 100;
    const height = (triangleSize * Math.sqrt(3)) / 2;

    return [
        {
            // Bottom left
            p1: { x: centerX - triangleSize, y: centerY + height / 2 },
            p2: { x: centerX, y: centerY + height / 2 },
            p3: { x: centerX - triangleSize / 2, y: centerY - height / 2 },
            code: node.children[0]
        },
        {
            // Bottom right
            p1: { x: centerX, y: centerY + height / 2 },
            p2: { x: centerX + triangleSize, y: centerY + height / 2 },
            p3: { x: centerX + triangleSize / 2, y: centerY - height / 2 },
            code: node.children[1]
        },
        {
            // Top
            p1: { x: centerX - triangleSize / 2, y: centerY - height / 2 },
            p2: { x: centerX + triangleSize / 2, y: centerY - height / 2 },
            p3: { x: centerX, y: centerY - height - 50 },
            code: node.children[2]
        }
    ];
}

/**
 * Four triangles - Diamond pattern
 */
function getRenderFourTriangles(node) {
    const triangleSize = 90;
    const height = (triangleSize * Math.sqrt(3)) / 2;
    const offset = 70;

    return [
        {
            // Top
            p1: { x: centerX - triangleSize / 2, y: centerY - offset - height / 2 },
            p2: { x: centerX + triangleSize / 2, y: centerY - offset - height / 2 },
            p3: { x: centerX, y: centerY - offset - height - 40 },
            code: node.children[0]
        },
        {
            // Right
            p1: { x: centerX + offset - triangleSize / 2, y: centerY + height / 2 },
            p2: { x: centerX + offset + triangleSize / 2, y: centerY + height / 2 },
            p3: { x: centerX + offset, y: centerY - height / 2 },
            code: node.children[1]
        },
        {
            // Bottom
            p1: { x: centerX - triangleSize / 2, y: centerY + offset + height / 2 },
            p2: { x: centerX + triangleSize / 2, y: centerY + offset + height / 2 },
            p3: { x: centerX, y: centerY + offset - height / 2 },
            code: node.children[2]
        },
        {
            // Left
            p1: { x: centerX - offset - triangleSize / 2, y: centerY + height / 2 },
            p2: { x: centerX - offset + triangleSize / 2, y: centerY + height / 2 },
            p3: { x: centerX - offset, y: centerY - height / 2 },
            code: node.children[3]
        }
    ];
}

/**
 * Five triangles - Pentagonal pattern
 */
function getRenderFiveTriangles(node) {
    const triangleSize = 80;
    const height = (triangleSize * Math.sqrt(3)) / 2;
    const radius = 120;

    const triangles = [];

    for (let i = 0; i < 5; i++) {
        const angle = (i * 2 * Math.PI / 5) - Math.PI / 2;
        const cx = centerX + Math.cos(angle) * radius;
        const cy = centerY + Math.sin(angle) * radius;

        triangles.push({
            p1: { x: cx - triangleSize / 2, y: cy + height / 2 },
            p2: { x: cx + triangleSize / 2, y: cy + height / 2 },
            p3: { x: cx, y: cy - height / 2 },
            code: node.children[i]
        });
    }

    return triangles;
}

/**
 * Six triangles - Hexagon with connections
 */
function getRenderSixTriangles(node) {
    const triangleSize = 80;
    const height = (triangleSize * Math.sqrt(3)) / 2;
    const radius = 130;

    const triangles = [];
    const positions = [];

    // Draw hexagon structure
    for (let i = 0; i < 6; i++) {
        const angle = (i * 2 * Math.PI / 6);
        const cx = centerX + Math.cos(angle) * radius;
        const cy = centerY + Math.sin(angle) * radius;

        positions.push({ cx, cy });

        triangles.push({
            p1: { x: cx - triangleSize / 2, y: cy + height / 2 },
            p2: { x: cx + triangleSize / 2, y: cy + height / 2 },
            p3: { x: cx, y: cy - height / 2 },
            code: node.children[i]
        });
    }

    // Draw dotted connections
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.2)';
    ctx.setLineDash([5, 5]);
    ctx.lineWidth = 1;

    for (let i = 0; i < positions.length; i++) {
        const next = (i + 1) % positions.length;
        ctx.beginPath();
        ctx.moveTo(positions[i].cx, positions[i].cy);
        ctx.lineTo(positions[next].cx, positions[next].cy);
        ctx.stroke();
    }

    ctx.setLineDash([]);

    return triangles;
}

/**
 * Seven or more triangles - Circular pattern
 */
function getRenderManyTriangles(node) {
    const childCount = node.children.length;
    const triangleSize = Math.max(50, 200 / Math.sqrt(childCount));
    const height = (triangleSize * Math.sqrt(3)) / 2;
    const radius = Math.min(200, 50 + childCount * 15);

    const triangles = [];

    for (let i = 0; i < childCount; i++) {
        const angle = (i * 2 * Math.PI / childCount) - Math.PI / 2;
        const cx = centerX + Math.cos(angle) * radius;
        const cy = centerY + Math.sin(angle) * radius;

        triangles.push({
            p1: { x: cx - triangleSize / 2, y: cy + height / 2 },
            p2: { x: cx + triangleSize / 2, y: cy + height / 2 },
            p3: { x: cx, y: cy - height / 2 },
            code: node.children[i]
        });
    }

    return triangles;
}

// ==============================
// TRIANGLE RENDERING
// ==============================

/**
 * Draw a single triangle
 */
function drawTriangle(tri, nodeData, index) {
    const { p1, p2, p3 } = tri;

    // Remplissage du triangle
    ctx.fillStyle = nodeData ? nodeData.color : '#6b7280';
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.lineTo(p3.x, p3.y);
    ctx.closePath();
    ctx.fill();

    // Bordure (fine et discrète)
    ctx.strokeStyle = hoveredTriangle === index ?
        'rgba(255, 255, 255, 0.6)' : 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = hoveredTriangle === index ? 3 : 2;
    ctx.stroke();

    // Contenu du triangle (emoji + label + montant)
    if (nodeData) {
        const centroidX = (p1.x + p2.x + p3.x) / 3;
        const centroidY = (p1.y + p2.y + p3.y) / 3;

        // 1. Emoji (en haut)
        ctx.font = '24px sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(getCategoryEmoji(nodeData.label), centroidX, centroidY - 15);

        // 2. Label (au milieu)
        ctx.font = 'bold 12px sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.fillText(nodeData.label, centroidX, centroidY + 10);

        // 3. Montant (en bas)
        ctx.font = '11px monospace';
        ctx.fillStyle = 'rgba(16, 185, 129, 0.8)';
        const amount = nodeData.amount || nodeData.total;
        ctx.fillText(formatCurrency(amount), centroidX, centroidY + 25);
    }
}

// ==============================
// INTERACTION HANDLERS
// ==============================

/**
 * Handle canvas click
 */
function handleCanvasClick(e) {
    if (animationInProgress) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Find clicked triangle
    for (let i = 0; i < triangles.length; i++) {
        const tri = triangles[i];
        if (isPointInTriangle(clickX, clickY, tri)) {
            handleZoomIn(tri.code);
            return;
        }
    }
}

/**
 * Handle canvas mouse move (hover) - Throttled for performance
 */
function handleCanvasMouseMove(e) {
    const now = Date.now();

    // Throttle mousemove events to prevent excessive redraws
    if (now - lastMouseMoveTime < MOUSEMOVE_THROTTLE) {
        return;
    }
    lastMouseMoveTime = now;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    let hoveredIndex = null;
    let hoveredData = null;

    // Find hovered triangle
    for (let i = 0; i < triangles.length; i++) {
        const tri = triangles[i];
        if (isPointInTriangle(mouseX, mouseY, tri)) {
            hoveredIndex = i;
            hoveredData = hierarchyData[tri.code];
            break;
        }
    }

    // Only redraw if hover state changed
    if (hoveredIndex !== hoveredTriangle) {
        hoveredTriangle = hoveredIndex;
        canvas.style.cursor = hoveredIndex !== null ? 'pointer' : 'default';
        render(hierarchyData[currentNode]);
    }

    // Show/hide tooltip
    const tooltip = document.getElementById('tooltip');
    if (hoveredData) {
        tooltip.style.display = 'block';
        tooltip.style.left = (e.clientX - rect.left + 15) + 'px';
        tooltip.style.top = (e.clientY - rect.top - 10) + 'px';

        const amount = hoveredData.amount || hoveredData.total;
        const percentage = hoveredData.percentage || 0;

        tooltip.innerHTML = `
            <div class="label">${hoveredData.label}</div>
            <div class="value">${formatCurrency(amount)}</div>
            <div class="percentage">${percentage.toFixed(1)}%</div>
        `;
    } else {
        tooltip.style.display = 'none';
    }
}

/**
 * Handle canvas mouse leave
 */
function handleCanvasMouseLeave() {
    hoveredTriangle = null;
    document.getElementById('tooltip').style.display = 'none';
    render(hierarchyData[currentNode]);
}

/**
 * Handle zoom in - Optimized animation
 */
async function handleZoomIn(targetCode) {
    if (!targetCode || animationInProgress) return;

    animationInProgress = true;

    // Update state immediately (don't wait for animation)
    navigationStack.push(targetCode);
    currentNode = targetCode;

    // Shorter, simpler fade animation
    const FAST_ANIMATION_FRAMES = Math.max(6, Math.floor(FRAMES_PER_ANIMATION / 2));
    for (let frame = 0; frame < FAST_ANIMATION_FRAMES; frame++) {
        const progress = frame / FAST_ANIMATION_FRAMES;
        ctx.globalAlpha = progress;
        render(hierarchyData[currentNode]);
        ctx.globalAlpha = 1;
        await delay(1000 / FRAME_RATE);
    }

    animationInProgress = false;

    // Send event to Streamlit
    Streamlit.setComponentValue({
        action: 'zoom',
        code: targetCode,
        level: navigationStack.length,
        timestamp: Date.now(),
        current_node: currentNode
    });

    update();
}

/**
 * Handle back button - Optimized for speed
 */
async function handleBack() {
    if (navigationStack.length <= 1 || animationInProgress) return;

    animationInProgress = true;

    // Update state immediately
    navigationStack.pop();
    currentNode = navigationStack[navigationStack.length - 1];

    // Quick fade effect
    const FAST_ANIMATION_FRAMES = Math.max(6, Math.floor(FRAMES_PER_ANIMATION / 2));
    for (let frame = 0; frame < FAST_ANIMATION_FRAMES; frame++) {
        const progress = frame / FAST_ANIMATION_FRAMES;
        ctx.globalAlpha = progress;
        render(hierarchyData[currentNode]);
        ctx.globalAlpha = 1;
        await delay(1000 / FRAME_RATE);
    }

    animationInProgress = false;

    // Send event
    Streamlit.setComponentValue({
        action: 'back',
        code: currentNode,
        level: navigationStack.length,
        timestamp: Date.now(),
        current_node: currentNode
    });

    update();
}

/**
 * Handle reset button - Optimized for speed
 */
async function handleReset() {
    if (currentNode === 'TR' || animationInProgress) return;

    animationInProgress = true;

    // Update state immediately
    navigationStack = ['TR'];
    currentNode = 'TR';

    // Quick fade animation
    const FAST_ANIMATION_FRAMES = Math.max(6, Math.floor(FRAMES_PER_ANIMATION / 2));
    for (let frame = 0; frame < FAST_ANIMATION_FRAMES; frame++) {
        const progress = frame / FAST_ANIMATION_FRAMES;
        ctx.globalAlpha = 1 - progress;
        render(hierarchyData[currentNode]);
        ctx.globalAlpha = 1;
        await delay(1000 / FRAME_RATE);
    }

    animationInProgress = false;

    Streamlit.setComponentValue({
        action: 'reset',
        code: 'TR',
        level: 0,
        timestamp: Date.now(),
        current_node: 'TR'
    });

    update();
}

// ==============================
// UTILITY FUNCTIONS
// ==============================

/**
 * Check if point is inside triangle (barycentric coordinates)
 */
function isPointInTriangle(px, py, tri) {
    const { p1, p2, p3 } = tri;

    const denominator = ((p2.y - p3.y) * (p1.x - p3.x) + (p3.x - p2.x) * (p1.y - p3.y));
    if (denominator === 0) return false;

    const a = ((p2.y - p3.y) * (px - p3.x) + (p3.x - p2.x) * (py - p3.y)) / denominator;
    const b = ((p3.y - p1.y) * (px - p3.x) + (p1.x - p3.x) * (py - p3.y)) / denominator;
    const c = 1 - a - b;

    return a >= 0 && b >= 0 && c >= 0;
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(Math.abs(amount));
}

/**
 * Get emoji for category
 */
function getCategoryEmoji(label) {
    const emojiMap = {
        // Types principaux
        'Revenus': '💼',
        'Dépenses': '🛒',

        // Catégories de revenus
        'Salaire': '💵',
        'Freelance': '🖥️',
        'Investissement': '📈',
        'Autres revenus': '💰',

        // Catégories de dépenses
        'Alimentation': '🍔',
        'Supermarché': '🛒',
        'Restaurant': '🍽️',
        'Boulangerie': '🥖',

        'Transport': '🚗',
        'Autoroute': '🛣️',
        'Essence': '⛽',
        'Stationnement': '🅿️',

        'Logement': '🏠',
        'Loyer': '🏠',

        'Santé': '⚕️',
        'Loisirs': '🎮',

        'Factures': '📄',
        'Abonnement': '📱',

        'Vêtements': '👕',
        'Education': '📚',
        'Uca': '🎓',

        'Banque': '🏦',
        'Assurance': '🛡️',

        'Divers': '📦'
    };

    return emojiMap[label] || '📁';
}

/**
 * Delay helper
 */
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Update info panel
 */
function updateInfoPanel(node) {
    const level = navigationStack.length;
    const total = node.total || node.amount || 0;
    const categories = node.children ? node.children.length : 0;
    const zoom = (level / 3).toFixed(1);

    document.getElementById('levelDisplay').textContent = level;
    document.getElementById('totalDisplay').textContent = formatCurrency(total);
    document.getElementById('categoriesDisplay').textContent = categories;
    document.getElementById('zoomDisplay').textContent = zoom + 'x';

    // Update colors
    const levelColor = level === 1 ? '#10b981' : level === 2 ? '#f59e0b' : '#ef4444';
    document.getElementById('levelDisplay').style.color = levelColor;
}

/**
 * Update breadcrumb
 */
function updateBreadcrumb(node) {
    const path = navigationStack.map(code => {
        const n = hierarchyData[code];
        return n ? n.label : code;
    }).join(' → ');

    document.getElementById('breadcrumbText').innerHTML = path;
}

/**
 * Update zoom indicator
 */
function updateZoomIndicator() {
    const level = navigationStack.length;
    const progress = (level / 3) * 100;
    document.getElementById('zoomProgress').style.width = progress + '%';
}

/**
 * Update control buttons
 */
function updateControlButtons() {
    const backBtn = document.getElementById('backBtn');
    const resetBtn = document.getElementById('resetBtn');

    backBtn.disabled = navigationStack.length <= 1;
    resetBtn.disabled = currentNode === 'TR';
}

/**
 * Render error state
 */
function renderErrorState() {
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    ctx.fillStyle = '#ef4444';
    ctx.font = 'bold 24px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Erreur: Données non disponibles', centerX, centerY);
}

/**
 * Render leaf node message
 */
function renderLeafNodeMessage() {
    const node = hierarchyData[currentNode];
    const transactions = node.transactions || 0;

    ctx.fillStyle = 'rgba(15, 23, 42, 0.5)';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    ctx.fillStyle = '#10b981';
    ctx.font = 'bold 20px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${node.label}`, centerX, centerY - 30);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '16px sans-serif';
    ctx.fillText(`${transactions} transaction(s)`, centerX, centerY + 20);
    ctx.fillText(formatCurrency(node.amount || 0), centerX, centerY + 50);
}