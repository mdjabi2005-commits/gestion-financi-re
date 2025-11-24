/**
 * Fractal Navigation Component - JavaScript Implementation
 *
 * Interactive Sierpinski triangle navigation with adaptive geometric patterns.
 * Supports multi-level hierarchical exploration of financial data.
 *
 * @author djabi
 * @version 1.1 (Standalone - no Streamlit component lib)
 * @date 2025-11-23
 */

// ==============================
// GLOBAL STATE - SINGLE DECLARATIONS
// ==============================

let hierarchyData = {};
let currentNode = 'TR';
let navigationStack = ['TR'];
let selectedNodes = new Set();  // NOUVEAU: Nœuds sélectionnés
let isSelectionMode = false;    // NOUVEAU: Mode sélection actif
let hoveredTriangle = null;
let animationInProgress = false;

const ANIMATION_DURATION = 700; // ms
const FRAME_RATE = 60;
const FRAMES_PER_ANIMATION = Math.round(ANIMATION_DURATION / (1000 / FRAME_RATE));

// Canvas setup
let canvas = null;
let ctx = null;
let canvasWidth = 0;
let canvasHeight = 0;
let triangles = [];
let centerX = 0;
let centerY = 0;

// ==============================
// INITIALIZATION
// ==============================

/**
 * Initialize when page loads
 */
window.addEventListener('load', () => {
    console.log('[FRACTAL] ✅ Page loaded');

    canvas = document.getElementById('fractalCanvas');
    if (!canvas) {
        console.error('[FRACTAL] ❌ Canvas not found!');
        return;
    }

    ctx = canvas.getContext('2d');
    console.log('[FRACTAL] ✅ Canvas and context ready');

    // Set canvas size
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Button handlers
    const backBtn = document.getElementById('backBtn');
    const resetBtn = document.getElementById('resetBtn');

    if (backBtn) backBtn.addEventListener('click', handleBack);
    if (resetBtn) resetBtn.addEventListener('click', handleReset);

    // Canvas interaction
    canvas.addEventListener('click', handleCanvasClick);
    canvas.addEventListener('mousemove', handleCanvasMouseMove);
    canvas.addEventListener('mouseleave', handleCanvasMouseLeave);

    console.log('[FRACTAL] ✅ Event listeners attached');

    // Initial render with injected data
    if (typeof window.hierarchyDataInjected !== 'undefined') {
        hierarchyData = window.hierarchyDataInjected;
        console.log('[FRACTAL] ✅ Hierarchy data injected:', Object.keys(hierarchyData).length, 'nodes');
        currentNode = 'TR';
        navigationStack = ['TR'];
        update();
    } else {
        console.warn('[FRACTAL] ⚠️  No hierarchy data injected yet');
    }
});

/**
 * Resize canvas to fill container
 */
function resizeCanvas() {
    const container = document.querySelector('.fractal-container');
    if (!container) {
        console.warn('[FRACTAL] Container not found for resize');
        return;
    }

    canvasWidth = container.clientWidth || 800;
    canvasHeight = container.clientHeight || 600;

    if (canvas) {
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;
    }

    centerX = canvasWidth / 2;
    centerY = canvasHeight / 2;

    console.log('[FRACTAL] ✅ Canvas resized:', canvasWidth, 'x', canvasHeight);
}

// ==============================
// UTILITY FUNCTIONS - LEVEL DETECTION
// ==============================

/**
 * Détecte si le nœud est au dernier niveau (mode sélection)
 *
 * HIÉRARCHIE:
 * - navigationStack[0] = 'TR' (Niveau 0 - Racine)
 * - navigationStack[1] = 'REVENUS'/'DEPENSES' (Niveau 1 - Types)
 * - navigationStack[2] = 'CAT_*' (Niveau 2 - Catégories) → SÉLECTION MODE
 * - navigationStack[3+] = 'SUBCAT_*' (Niveau 3+ - Sous-catégories) → SÉLECTION MODE
 *
 * currentLevel = navigationStack.length - 1
 * Donc : currentLevel >= 2 = Mode sélection ✓
 */
function isLastLevel(node) {
    const currentLevel = navigationStack.length - 1;
    const nodeCode = currentNode;

    console.log('[FRACTAL] ═══════════════════════════════════');
    console.log('[FRACTAL] isLastLevel() Check:');
    console.log('[FRACTAL]   navigationStack:', navigationStack);
    console.log('[FRACTAL]   currentLevel:', currentLevel);
    console.log('[FRACTAL]   currentNode:', nodeCode);
    console.log('[FRACTAL]   node.children:', node?.children?.length || 0);

    // Mode sélection au niveau 2+ (Catégories et Sous-catégories)
    // Level 0 (TR) → Navigation
    // Level 1 (REVENUS/DEPENSES) → Navigation
    // Level 2+ (CAT_* and SUBCAT_*) → SÉLECTION
    if (currentLevel >= 2) {
        console.log('[FRACTAL] ✅ Niveau', currentLevel, '→ MODE SÉLECTION');
        console.log('[FRACTAL] ═══════════════════════════════════');
        return true;
    }

    console.log('[FRACTAL] ❌ Niveau', currentLevel, '→ MODE NAVIGATION');
    console.log('[FRACTAL] ═══════════════════════════════════');
    return false;
}

// ==============================
// MAIN UPDATE & RENDER
// ==============================

/**
 * Main update and render loop
 */
function update() {
    if (animationInProgress) return;

    console.log('[FRACTAL] 🔄 Update called for node:', currentNode);

    const node = hierarchyData[currentNode];
    if (!node) {
        console.error('[FRACTAL] ❌ Node not found:', currentNode);
        renderErrorState();
        return;
    }

    // Détecter si on est en mode sélection (dernier niveau)
    isSelectionMode = isLastLevel(node);
    console.log('[FRACTAL] Mode sélection:', isSelectionMode);

    // Update UI
    updateInfoPanel(node);
    updateBreadcrumb(node);
    updateZoomIndicator();
    updateControlButtons();

    // Render triangles
    render(node);

    // Envoyer l'état à Streamlit
    sendSelectionToStreamlit();
}

/**
 * Render the current state
 */
function render(node) {
    if (!ctx || !canvas) {
        console.error('[FRACTAL] ❌ Canvas context not available');
        return;
    }

    console.log('[FRACTAL] 🎨 Rendering node:', node.code, 'with', (node.children || []).length, 'children');

    // Clear canvas
    ctx.fillStyle = 'rgba(15, 23, 42, 0.05)';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Get triangles for current level
    triangles = [];

    const childCount = (node.children || []).length;

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

    console.log('[FRACTAL] 🔺 Generated', triangles.length, 'triangles');

    // Draw all triangles
    triangles.forEach((tri, idx) => {
        const childCode = node.children[idx];
        const childNode = hierarchyData[childCode];

        drawTriangle(tri, childNode, idx);
    });

    console.log('[FRACTAL] ✅ Render complete');
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

    const isSelected = nodeData && selectedNodes.has(nodeData.code);
    const isHovered = hoveredTriangle === index;

    // Draw triangle
    ctx.fillStyle = nodeData ? nodeData.color : '#6b7280';
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.lineTo(p3.x, p3.y);
    ctx.closePath();
    ctx.fill();

    // Draw border (style différent si sélectionné)
    if (isSelected) {
        // Bordure brillante + glow pour sélection
        ctx.strokeStyle = '#3b82f6';  // Bleu brillant
        ctx.lineWidth = 4;
        ctx.shadowBlur = 15;
        ctx.shadowColor = '#3b82f6';
    } else if (isHovered) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.lineWidth = 3;
        ctx.shadowBlur = 0;
    } else {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1.5;
        ctx.shadowBlur = 0;
    }
    ctx.stroke();
    ctx.shadowBlur = 0;  // Reset shadow

    // Draw label
    if (nodeData) {
        const centroidX = (p1.x + p2.x + p3.x) / 3;
        const centroidY = (p1.y + p2.y + p3.y) / 3;

        // Checkmark si sélectionné
        if (isSelected) {
            ctx.fillStyle = '#3b82f6';
            ctx.font = 'bold 20px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('✓', centroidX + 15, centroidY - 15);
        }

        // Emoji
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.font = '24px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(getCategoryEmoji(nodeData.label), centroidX, centroidY - 10);

        // Label
        ctx.font = 'bold 12px sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.fillText(nodeData.label, centroidX, centroidY + 10);

        // Amount
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
 * Handle canvas click - Navigation OU Sélection
 */
function handleCanvasClick(e) {
    if (animationInProgress) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    console.log('[FRACTAL] 🖱️ Click at:', clickX, clickY);

    // Find clicked triangle
    for (let i = 0; i < triangles.length; i++) {
        const tri = triangles[i];
        if (isPointInTriangle(clickX, clickY, tri)) {
            const node = hierarchyData[currentNode];
            const childCode = tri.code;
            const childNode = hierarchyData[childCode];

            console.log('[FRACTAL] ✅ Clicked triangle:', childCode);

            if (!childNode) break;

            // MODE SÉLECTION (dernier niveau)
            if (isSelectionMode) {
                console.log('[FRACTAL] Mode SÉLECTION - Toggle:', childCode);
                toggleSelection(childCode);
            }
            // MODE NAVIGATION (niveaux supérieurs)
            else if (childNode.children && childNode.children.length > 0) {
                console.log('[FRACTAL] Mode NAVIGATION - Zoom:', childCode);
                handleZoomIn(childCode);
            } else {
                console.log('[FRACTAL] Feuille sans enfants - Pas de navigation');
            }

            return;
        }
    }

    console.log('[FRACTAL] ⚠️  No triangle under click');
}

/**
 * Toggle selection d'un nœud
 */
function toggleSelection(nodeCode) {
    if (selectedNodes.has(nodeCode)) {
        selectedNodes.delete(nodeCode);
        console.log('[FRACTAL] 🔴 Désélectionné:', nodeCode);
    } else {
        selectedNodes.add(nodeCode);
        console.log('[FRACTAL] 🟢 Sélectionné:', nodeCode);
    }

    console.log('[FRACTAL] Sélections actuelles:', Array.from(selectedNodes));

    // Re-render pour afficher le changement
    render(hierarchyData[currentNode]);

    // Envoyer l'état à Streamlit
    sendSelectionToStreamlit();
}

/**
 * Handle canvas mouse move (hover)
 */
function handleCanvasMouseMove(e) {
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

    hoveredTriangle = hoveredIndex;
    canvas.style.cursor = hoveredIndex !== null ? 'pointer' : 'default';

    // Show/hide tooltip
    const tooltip = document.getElementById('tooltip');
    if (hoveredData && tooltip) {
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
    } else if (tooltip) {
        tooltip.style.display = 'none';
    }

    // Redraw
    render(hierarchyData[currentNode]);
}

/**
 * Handle canvas mouse leave
 */
function handleCanvasMouseLeave() {
    hoveredTriangle = null;
    const tooltip = document.getElementById('tooltip');
    if (tooltip) tooltip.style.display = 'none';
    render(hierarchyData[currentNode]);
}

/**
 * Handle zoom in
 */
async function handleZoomIn(targetCode) {
    if (!targetCode || animationInProgress) return;

    console.log('[FRACTAL] 🔍 Zooming to:', targetCode);

    animationInProgress = true;

    // Animation: fade out current, fade in new
    for (let frame = 0; frame < FRAMES_PER_ANIMATION; frame++) {
        const progress = frame / FRAMES_PER_ANIMATION;

        ctx.fillStyle = `rgba(15, 23, 42, ${0.05 + progress * 0.15})`;
        ctx.fillRect(0, 0, canvasWidth, canvasHeight);

        // Scale effect
        const scale = 1 + progress * 0.2;
        ctx.save();
        ctx.globalAlpha = 1 - progress;
        ctx.translate(centerX, centerY);
        ctx.scale(scale, scale);
        ctx.translate(-centerX, -centerY);
        render(hierarchyData[currentNode]);
        ctx.restore();

        await delay(1000 / FRAME_RATE);
    }

    // Update state
    navigationStack.push(targetCode);
    currentNode = targetCode;

    // ✅ NE PAS réinitialiser la sélection !
    // Les filtres doivent rester actifs pour permettre le multi-filtrage
    console.log('[FRACTAL] ✅ Navigation vers', targetCode);
    console.log('[FRACTAL] 📌 Filtres conservés:', Array.from(selectedNodes));

    // Fade in new
    for (let frame = 0; frame < FRAMES_PER_ANIMATION; frame++) {
        const progress = frame / FRAMES_PER_ANIMATION;

        ctx.globalAlpha = progress;
        render(hierarchyData[currentNode]);
        ctx.globalAlpha = 1;

        await delay(1000 / FRAME_RATE);
    }

    animationInProgress = false;

    console.log('[FRACTAL] ✅ Zoom complete');
    update();
}

/**
 * Handle back button
 */
function handleBack() {
    if (navigationStack.length <= 1 || animationInProgress) return;

    console.log('[FRACTAL] ⏮️ Going back');

    animationInProgress = true;
    navigationStack.pop();
    currentNode = navigationStack[navigationStack.length - 1];

    // ✅ CONSERVER LES SÉLECTIONS pour permettre le multi-filtrage
    console.log('[FRACTAL] 📌 Filtres conservés:', Array.from(selectedNodes));

    // Simple fade effect
    const originalNode = hierarchyData[currentNode];
    for (let frame = 0; frame < Math.floor(FRAMES_PER_ANIMATION / 2); frame++) {
        const progress = frame / (FRAMES_PER_ANIMATION / 2);
        ctx.globalAlpha = progress;
        render(originalNode);
        ctx.globalAlpha = 1;
    }

    animationInProgress = false;

    console.log('[FRACTAL] ✅ Back complete');
    update();
}

/**
 * Handle reset button
 */
function handleReset() {
    if (currentNode === 'TR' || animationInProgress) return;

    console.log('[FRACTAL] 🏠 Resetting to root');

    navigationStack = ['TR'];
    currentNode = 'TR';

    // Réinitialiser la sélection
    selectedNodes.clear();
    console.log('[FRACTAL] 🔄 Sélection réinitialisée');

    animationInProgress = true;

    for (let frame = 0; frame < FRAMES_PER_ANIMATION; frame++) {
        const progress = frame / FRAMES_PER_ANIMATION;
        const scale = 1 + progress * 0.3;

        ctx.save();
        ctx.globalAlpha = 1 - progress;
        ctx.translate(centerX, centerY);
        ctx.scale(scale, scale);
        ctx.translate(-centerX, -centerY);
        render(hierarchyData[currentNode]);
        ctx.restore();
    }

    animationInProgress = false;

    console.log('[FRACTAL] ✅ Reset complete');
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
        minimumFractionDigits: 0
    }).format(amount);
}

/**
 * Get emoji for category
 */
function getCategoryEmoji(label) {
    const emojiMap = {
        'Revenus': '💼',
        'Dépenses': '🛒',
        'Salaire': '💵',
        'Freelance': '🖥️',
        'Investissement': '📈',
        'Alimentation': '🍔',
        'Transport': '🚗',
        'Logement': '🏠',
        'Santé': '⚕️',
        'Loisirs': '🎮',
        'Factures': '📄',
        'Vêtements': '👕',
        'Education': '📚'
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

    const levelDisplay = document.getElementById('levelDisplay');
    const totalDisplay = document.getElementById('totalDisplay');
    const categoriesDisplay = document.getElementById('categoriesDisplay');
    const zoomDisplay = document.getElementById('zoomDisplay');

    if (levelDisplay) levelDisplay.textContent = level;
    if (totalDisplay) totalDisplay.textContent = formatCurrency(total);
    if (categoriesDisplay) categoriesDisplay.textContent = categories;
    if (zoomDisplay) zoomDisplay.textContent = zoom + 'x';

    // Update colors
    if (levelDisplay) {
        const levelColor = level === 1 ? '#10b981' : level === 2 ? '#f59e0b' : '#ef4444';
        levelDisplay.style.color = levelColor;
    }
}

/**
 * Update breadcrumb
 */
function updateBreadcrumb(node) {
    const path = navigationStack.map(code => {
        const n = hierarchyData[code];
        return n ? n.label : code;
    }).join(' → ');

    const breadcrumbText = document.getElementById('breadcrumbText');
    if (breadcrumbText) breadcrumbText.innerHTML = path;
}

/**
 * Update zoom indicator
 */
function updateZoomIndicator() {
    const level = navigationStack.length;
    const progress = (level / 3) * 100;
    const zoomProgress = document.getElementById('zoomProgress');
    if (zoomProgress) zoomProgress.style.width = progress + '%';
}

/**
 * Update control buttons
 */
function updateControlButtons() {
    const backBtn = document.getElementById('backBtn');
    const resetBtn = document.getElementById('resetBtn');

    if (backBtn) backBtn.disabled = navigationStack.length <= 1;
    if (resetBtn) resetBtn.disabled = currentNode === 'TR';
}

/**
 * Render error state
 */
function renderErrorState() {
    if (!ctx) return;

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
    if (!ctx) return;

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

/**
 * Synchroniser automatiquement l'URL quand on est au Niveau 3 avec sélections
 */
function autoSyncURLAtLevel3() {
    // Vérifier si on est au Niveau 3 (dernière profondeur)
    if (navigationStack.length === 4 && selectedNodes.size > 0) {
        console.log('[FRACTAL-AUTO-SYNC] ✅ Niveau 3 détecté avec sélections');
        console.log('[FRACTAL-AUTO-SYNC] Sélections:', Array.from(selectedNodes));

        try {
            // Construire l'URL avec les sélections
            const selections = Array.from(selectedNodes).join(',');
            const newUrl = window.location.pathname + '?fractal_selections=' + encodeURIComponent(selections);

            console.log('[FRACTAL-AUTO-SYNC] 🔄 Mise à jour automatique de l\'URL');
            console.log('[FRACTAL-AUTO-SYNC] Nouvelle URL:', newUrl);

            // Mettre à jour l'URL sans recharger la page
            window.history.replaceState({}, '', newUrl);

            console.log('[FRACTAL-AUTO-SYNC] ✅ URL synchronisée automatiquement');
            console.log('[FRACTAL-AUTO-SYNC] Le tableau devrait maintenant être visible dans Streamlit');
        } catch (e) {
            console.log('[FRACTAL-AUTO-SYNC] ⚠️  Erreur lors de la sync URL:', e);
        }
    }
}

/**
 * Envoyer l'état de sélection à Streamlit
 */
function sendSelectionToStreamlit() {
    const state = {
        action: isSelectionMode ? 'selection' : 'navigation',
        currentNode: currentNode,
        selectedNodes: Array.from(selectedNodes),
        level: navigationStack.length,
        isSelectionMode: isSelectionMode
    };

    console.log('[FRACTAL] 📤 Envoi à Streamlit:', state);

    // Sauvegarder dans sessionStorage et localStorage pour que Streamlit puisse le lire
    try {
        window.sessionStorage.setItem('fractal_state_v6', JSON.stringify(state));
        window.localStorage.setItem('fractal_state_v6', JSON.stringify(state));
        console.log('[FRACTAL] ✅ État sauvegardé en storage');
    } catch (e) {
        console.log('[FRACTAL] ℹ️ Storage non disponible:', e);
    }

    // Essayer aussi postMessage pour communication avec parent
    if (typeof window.parent !== 'undefined' && window.parent !== window) {
        try {
            window.parent.postMessage({
                type: 'fractal_state',
                data: state
            }, '*');
            console.log('[FRACTAL] 📨 postMessage envoyé');
        } catch (e) {
            console.log('[FRACTAL] ℹ️ postMessage non disponible');
        }
    }

    // Trigger a custom event que Streamlit peut écouter
    try {
        const event = new CustomEvent('fractalStateChanged', {
            detail: state
        });
        document.dispatchEvent(event);
        console.log('[FRACTAL] 🔔 CustomEvent envoyé');
    } catch (e) {
        console.log('[FRACTAL] ℹ️ CustomEvent non disponible');
    }

    // AUTO-SYNC: Si on est au Niveau 3 avec sélections, synchroniser l'URL automatiquement
    autoSyncURLAtLevel3();
}
