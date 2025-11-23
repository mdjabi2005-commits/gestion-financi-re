/**
 * Bubble Navigation Component - D3.js Implementation
 * Handles animated bubble transitions and category navigation
 */

let currentData = null;
let isAnimating = false;

/**
 * Fonction principale pour afficher les bulles
 */
function renderBubbles(data) {
    currentData = data;
    const container = d3.select("#bubble-container");

    // Vider le container
    container.selectAll("*").remove();

    // Créer l'univers
    const universe = container.append("div")
        .attr("class", "bubble-universe");

    // Afficher selon le niveau
    if (data.level === 'main') {
        renderMainBubble(universe, data);
    } else if (data.level === 'categories') {
        renderCategoryBubbles(universe, data);
    } else if (data.level === 'subcategories') {
        renderSubcategoryView(universe, data);
    }

    // Mettre à jour la hauteur
    updateHeight();
}

/**
 * Affiche la bulle principale
 */
function renderMainBubble(universe, data) {
    const mainBubble = universe.append("div")
        .attr("class", "main-bubble")
        .on("click", function() {
            if (isAnimating) return;
            isAnimating = true;

            // Animation d'explosion
            d3.select(this)
                .classed("exploding", true);

            // Envoyer l'événement à Streamlit après l'animation
            setTimeout(() => {
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: {
                        action: "navigate",
                        level: "categories"
                    }
                }, "*");
            }, 800);
        });

    // Contenu
    mainBubble.append("div")
        .attr("class", "bubble-title")
        .text("💰 TOTAL DÉPENSES");

    mainBubble.append("div")
        .attr("class", "bubble-amount")
        .text(`${formatNumber(data.total)}€`);

    mainBubble.append("div")
        .attr("class", "bubble-info")
        .html(`${data.categoriesCount} catégories<br>${data.transactionsCount} transactions`);

    mainBubble.append("div")
        .attr("class", "bubble-hint")
        .text("👆 Cliquez pour explorer");
}

/**
 * Affiche les bulles de catégories
 */
function renderCategoryBubbles(universe, data) {
    // Breadcrumb
    const breadcrumb = universe.append("div")
        .attr("class", "breadcrumb");

    breadcrumb.append("span")
        .attr("class", "back-link")
        .text("← Retour")
        .on("click", function() {
            if (isAnimating) return;
            isAnimating = true;

            window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: { action: "back", level: "main" }
            }, "*");
        });

    breadcrumb.append("span")
        .text(" / Catégories");

    // Calcul des positions circulaires
    const centerX = 400;
    const centerY = 300;
    const categories = data.categories || [];

    if (categories.length === 0) {
        universe.append("div")
            .attr("class", "loading")
            .text("Aucune catégorie trouvée");
        return;
    }

    const angleStep = (2 * Math.PI) / categories.length;
    const maxAmount = Math.max(...categories.map(c => c.amount || 0));

    // Créer les bulles
    categories.forEach((cat, i) => {
        const angle = i * angleStep - Math.PI / 2;
        const radius = 200;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);

        // Taille proportionnelle
        const size = Math.max(70, Math.min(140, 80 + (cat.amount / maxAmount) * 60));

        // Obtenir la couleur
        const color = getCategoryColor(cat.name);

        const bubble = universe.append("div")
            .attr("class", "category-bubble")
            .style("left", `${x}px`)
            .style("top", `${y}px`)
            .style("width", `${size}px`)
            .style("height", `${size}px`)
            .style("background", `linear-gradient(135deg, ${color} 0%, ${adjustColor(color, -20)} 100%)`)
            .style("animation-delay", `${i * 0.08}s`)
            .on("click", function() {
                if (isAnimating) return;
                isAnimating = true;

                // Animation de sélection
                d3.select(this)
                    .classed("selecting", true);

                setTimeout(() => {
                    window.parent.postMessage({
                        type: "streamlit:setComponentValue",
                        value: {
                            action: "select",
                            category: cat.name,
                            level: "subcategories"
                        }
                    }, "*");
                }, 400);
            });

        // Contenu de la bulle
        bubble.append("div")
            .attr("class", "bubble-cat-name")
            .text(cat.name);

        bubble.append("div")
            .attr("class", "bubble-cat-amount")
            .text(`${formatNumber(cat.amount)}€`);

        bubble.append("div")
            .attr("class", "bubble-cat-count")
            .text(`${cat.count} items`);
    });
}

/**
 * Affiche les sous-catégories filtrées
 */
function renderSubcategoryView(universe, data) {
    // Breadcrumb
    const breadcrumb = universe.append("div")
        .attr("class", "breadcrumb");

    breadcrumb.append("span")
        .attr("class", "back-link")
        .text("← Retour")
        .on("click", function() {
            if (isAnimating) return;
            isAnimating = true;

            window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: { action: "back", level: "categories" }
            }, "*");
        });

    breadcrumb.append("span")
        .text(` / ${data.selected_category}`);

    // Afficher les statistiques
    const stats = universe.append("div")
        .style("padding", "40px 20px")
        .style("color", "white")
        .style("text-align", "center");

    stats.append("h2")
        .style("font-size", "28px")
        .style("margin-bottom", "20px")
        .text(`📊 ${data.selected_category}`);

    const metricsRow = stats.append("div")
        .style("display", "grid")
        .style("grid-template-columns", "repeat(3, 1fr)")
        .style("gap", "20px")
        .style("margin-bottom", "40px");

    // Métrique: Total
    const metric1 = metricsRow.append("div");
    metric1.append("div")
        .style("font-size", "28px")
        .style("font-weight", "700")
        .style("color", "#60a5fa")
        .text(`${formatNumber(data.total)}€`);
    metric1.append("div")
        .style("font-size", "12px")
        .style("opacity", "0.8")
        .style("margin-top", "8px")
        .text("Total");

    // Métrique: Nombre de sous-catégories
    const metric2 = metricsRow.append("div");
    metric2.append("div")
        .style("font-size", "28px")
        .style("font-weight", "700")
        .style("color", "#34d399")
        .text(data.subcategoriesCount || 0);
    metric2.append("div")
        .style("font-size", "12px")
        .style("opacity", "0.8")
        .style("margin-top", "8px")
        .text("Sous-catégories");

    // Métrique: Nombre de transactions
    const metric3 = metricsRow.append("div");
    metric3.append("div")
        .style("font-size", "28px")
        .style("font-weight", "700")
        .style("color", "#fbbf24")
        .text(data.transactionsCount || 0);
    metric3.append("div")
        .style("font-size", "12px")
        .style("opacity", "0.8")
        .style("margin-top", "8px")
        .text("Transactions");
}

/**
 * Obtient la couleur pour une catégorie
 */
function getCategoryColor(categoryName) {
    const colors = {
        'Alimentation': '#10b981',
        'Transport': '#3b82f6',
        'Loisirs': '#f59e0b',
        'Logement': '#8b5cf6',
        'Santé': '#ef4444',
        'Shopping': '#ec4899',
        'Autres': '#6b7280'
    };
    return colors[categoryName] || '#6b7280';
}

/**
 * Ajuste une couleur hex (assombrit ou éclaircit)
 */
function adjustColor(color, percent) {
    const num = parseInt(color.replace("#", ""), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
        (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
        (B < 255 ? B < 1 ? 0 : B : 255))
        .toString(16).slice(1);
}

/**
 * Formate un nombre pour l'affichage
 */
function formatNumber(num) {
    if (!num) return "0";
    return Math.round(num).toLocaleString('fr-FR');
}

/**
 * Met à jour la hauteur du composant dans Streamlit
 */
function updateHeight() {
    // Attendre un peu pour que le DOM soit rendu
    setTimeout(() => {
        const element = document.querySelector('.bubble-universe');
        if (element) {
            const height = element.offsetHeight + 40;
            window.parent.postMessage({
                type: "streamlit:setFrameHeight",
                height: height
            }, "*");
        }
    }, 100);
}

/**
 * Initialisation - Attendre que Streamlit soit prêt
 */
window.addEventListener('load', function() {
    // Signaler à Streamlit que le composant est prêt
    window.parent.postMessage({
        type: "streamlit:componentReady"
    }, "*");

    // Écouter les messages de Streamlit
    window.addEventListener("message", function(event) {
        if (event.data.type === "streamlit:render") {
            const args = event.data.args;
            if (args && args[0]) {
                renderBubbles(args[0]);
            }
        }
    });
});

// Gérer les données initiales (peuvent être envoyées au chargement)
if (window.componentData) {
    renderBubbles(window.componentData);
}
