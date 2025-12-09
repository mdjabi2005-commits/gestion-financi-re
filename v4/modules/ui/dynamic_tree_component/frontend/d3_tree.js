/**
 * D3.js Hierarchical Tree - Streamlit Custom Component
 * Vertical tree with all nodes visible and connected branches
 */

// Global state
let selectedCodes = new Set();
let hierarchyData = null;

// Wait for Streamlit
function initD3Tree() {
    if (typeof window.Streamlit === 'undefined') {
        console.log('[D3_TREE] Waiting for Streamlit...');
        setTimeout(initD3Tree, 100);
        return;
    }

    console.log('[D3_TREE] Streamlit found!');
    const Streamlit = window.Streamlit;

    function onRenderEvent(event) {
        const data = event.detail;

        if (!data || !data.args) {
            console.error('[D3_TREE] No data from Python');
            return;
        }

        console.log('[D3_TREE] Received data:', data.args);

        hierarchyData = data.args.hierarchy;
        const height = data.args.height || 800;

        renderTree(hierarchyData, height);

        Streamlit.setFrameHeight(height + 50);
    }

    function renderTree(hierarchy, containerHeight) {
        // Clear previous tree
        d3.select('#tree-container').selectAll('*').remove();

        // Convert flat hierarchy to D3 tree structure
        const root = convertToD3Hierarchy(hierarchy);

        // Tree layout
        const width = window.innerWidth || 1000;
        const treeLayout = d3.tree().size([width - 200, containerHeight - 200]);

        // Compute tree layout
        const treeData = treeLayout(root);

        // Create SVG
        const svg = d3.select('#tree-container')
            .append('svg')
            .attr('width', width)
            .attr('height', containerHeight)
            .append('g')
            .attr('transform', 'translate(100, 50)');

        // Draw links (branches)
        svg.selectAll('.link')
            .data(treeData.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y)
            );

        // Draw nodes
        const nodes = svg.selectAll('.node')
            .data(treeData.descendants())
            .enter()
            .append('g')
            .attr('class', d => `node ${selectedCodes.has(d.data.code) ? 'selected' : ''}`)
            .attr('transform', d => `translate(${d.x}, ${d.y})`)
            .on('click', function (event, d) {
                handleNodeClick(d, this);
            });

        // Node rectangles
        nodes.append('rect')
            .attr('x', -60)
            .attr('y', -20)
            .attr('width', 120)
            .attr('height', 40)
            .attr('rx', 5)
            .attr('fill', d => {
                if (selectedCodes.has(d.data.code)) return '#9333ea';
                return d.data.color || '#64748b';
            });

        // Node text (label)
        nodes.append('text')
            .attr('dy', -5)
            .attr('text-anchor', 'middle')
            .style('font-size', '11px')
            .text(d => {
                const label = d.data.label || d.data.code;
                return label.length > 12 ? label.substring(0, 12) + '...' : label;
            });

        // Node text (amount)
        nodes.append('text')
            .attr('dy', 10)
            .attr('text-anchor', 'middle')
            .style('font-size', '10px')
            .style('fill', '#22d3ee')
            .text(d => {
                const amount = d.data.amount || d.data.total || 0;
                return `${Math.abs(amount).toLocaleString('fr-FR')} €`;
            });
    }

    function handleNodeClick(nodeData, nodeElement) {
        const code = nodeData.data.code;

        // Special case: clicking root = reset
        if (code === 'TR') {
            console.log('[D3_TREE] Reset all selections');
            selectedCodes.clear();
            renderTree(hierarchyData, 800);
            Streamlit.setComponentValue({ codes: [], action: 'reset' });
            return;
        }

        // Toggle selection
        if (selectedCodes.has(code)) {
            selectedCodes.delete(code);
            console.log('[D3_TREE] Removed:', code);
        } else {
            selectedCodes.add(code);
            console.log('[D3_TREE] Added:', code);
        }

        // Re-render
        renderTree(hierarchyData, 800);

        // Send to Python
        Streamlit.setComponentValue({
            codes: Array.from(selectedCodes),
            action: 'multi-select'
        });
    }

    function convertToD3Hierarchy(flatHierarchy) {
        // Build tree from flat structure
        const buildNode = (code) => {
            if (!flatHierarchy[code]) return null;

            const node = flatHierarchy[code];
            const children = (node.children || [])
                .map(childCode => buildNode(childCode))
                .filter(child => child !== null);

            return {
                code: code,
                label: node.label,
                color: node.color,
                amount: node.amount || node.total,
                children: children.length > 0 ? children : undefined
            };
        };

        const treeData = buildNode('TR');
        return d3.hierarchy(treeData);
    }

    // Register Streamlit events
    Streamlit.setComponentReady();
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRenderEvent);
    console.log('[D3_TREE] Component ready!');
}

// Start
initD3Tree();
