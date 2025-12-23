# ⚡ Quick Reference Card

## 🎯 Problem & Solution (One Page)

### The Problem
**You:** "Je vois pas de tableau quand j'arrive à la dernière profondeur"
**You see:** Triangles but no table
**Why:** URL synchronization fails in Streamlit iframes

### The Solution
**Click the button:** ✅ Appliquer les Sélections

---

## 🚀 Three-Step Workflow

### 1️⃣ NAVIGATE & SELECT
```
Go to last level: TR → Type → Category → SubCategory
Click triangles you want to analyze
→ Triangles turn BLUE
→ Checkmarks appear ✓
```

### 2️⃣ APPLY SELECTIONS
```
Scroll down in left column
Click button: ✅ Appliquer les Sélections
→ Console shows: [BUTTON-HANDLER] Button clicked!
→ Page reloads after ~100ms
```

### 3️⃣ VIEW TABLE
```
Right column shows:
- Filter badges (your selections)
- Statistics (count, amounts)
- Transaction table (your data) ✅
```

---

## 📍 Button Location

```
LEFT COLUMN (60% of screen)
├─ 🔺 Navigation Visuelle (triangles)
├─ (many triangles)
├─ ─── (separator line)
└─ ✅ Appliquer les Sélections (BLUE BUTTON)  ← CLICK HERE

RIGHT COLUMN (40% of screen)
├─ 📊 Transactions Filtrées
├─ 🎯 Filtres Actifs
├─ 📊 Statistiques
└─ 📋 Tableau (appears after button click)
```

---

## 🔍 Console Logs to Expect

**Good signs:**
```javascript
[BUTTON-SETUP] Found apply button ✅
[BUTTON-HANDLER] Button clicked! ✅
[BUTTON-HANDLER] Found selections: SUBCAT_... ✅
[BUTTON-HANDLER] ✅ URL updated, reloading... ✅
```

**Bad signs:**
```javascript
[BUTTON-HANDLER] No selections found ❌
// → You didn't select any triangles first
```

---

## ✅ Quick Checklist

- [ ] Navigated to last level (4 levels deep)
- [ ] Selected at least 1 triangle (turned blue)
- [ ] Scrolled down in left column
- [ ] Found button "✅ Appliquer les Sélections"
- [ ] Clicked the button
- [ ] Saw console logs [BUTTON-HANDLER]
- [ ] Page reloaded
- [ ] Table appeared in right column

---

## 🐛 Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| Can't find button | Scroll down in LEFT column |
| Button exists but nothing happens | Check console (F12) for errors |
| No console logs | Button might not have been found, reload page |
| URL doesn't change | Try different browser (Chrome > Firefox) |
| Table still doesn't appear | See TESTING_GUIDE_APPLY_BUTTON.md for detailed help |

---

## 📱 Browser Access

```
Open: http://localhost:8501/
```

### Essential Shortcuts
- **F12** → Open console
- **F5** → Reload page
- **Ctrl+Shift+I** → Developer tools (Windows)
- **Cmd+Option+I** → Developer tools (Mac)

---

## 🎯 Success Scenario

```
Start: No table visible
         ↓
Select triangles (blue + ✓)
         ↓
Click "✅ Appliquer les Sélections"
         ↓
Console shows: [BUTTON-HANDLER] Syncing selections
         ↓
URL updates: ?fractal_selections=SUBCAT_...
         ↓
Page reloads (~100ms)
         ↓
END: Table appears with your filtered data ✅
```

---

## 📊 Multi-Selection Example

```
Can select across different categories:

SELECT STEP 1:
  Navigate: TR → Revenus → Uber → Septembre
  Click Septembre (BLUE)

SELECT STEP 2:
  Navigate BACK to Revenus
  Navigate to Bureau → March
  Click March (BLUE)

Now you have 2 selections:
  ✓ Septembre (Uber)
  ✓ March (Bureau)

APPLY:
  Click button
  Table shows BOTH months combined ✅
```

---

## 💡 Tips & Tricks

1. **Multiple selections work!** Select as many as you want before clicking button

2. **Remove filters later:** After table appears, click ❌ on filter badges to remove them

3. **CSV export:** Click 💾 Exporter CSV to save filtered data

4. **Navigate while filtered:** Filters stay active if you navigate to other categories

5. **Check console early:** If issues, open F12 → Console tab first

---

## 📞 When to Ask for Help

**Check these first:**
1. Console shows blue checkmarks when selecting? → Yes? Go to step 2
2. Can find the button? → Yes? Go to step 3
3. Console shows [BUTTON-HANDLER] logs? → If no, reload page and try again

**If still stuck:**
→ See: `TESTING_GUIDE_APPLY_BUTTON.md` (full troubleshooting guide)
→ Or: `IMPLEMENTATION_COMPLETE.md` (technical details)

---

## 📋 Key Files

| File | Purpose |
|------|---------|
| `IMPLEMENTATION_COMPLETE.md` | Overview of solution |
| `TESTING_GUIDE_APPLY_BUTTON.md` | **← Detailed testing guide** |
| `SOLUTION_TABLE_MISSING.md` | How the feature works |
| `QUICK_FIX_TABLE_MISSING.md` | Alternative fixes (if needed) |

---

## ⚙️ Technical Summary

```
Fractal.js (JavaScript)
  ↓ saves selections to
localStorage: fractal_state_v6
  ↓ button reads from
fractal_unified.py (Python/Streamlit)
  ↓ button handler updates
URL: ?fractal_selections=SUBCAT_...
  ↓ page reloads
Streamlit re-renders
  ↓ reads URL params
Python filters transactions
  ↓ displays
Table in right column ✅
```

---

## 🎉 You're Ready!

**The workflow is simple:**
1. Select → Click → Wait for table ✅

**If questions arise:**
- Check console logs first
- Read TESTING_GUIDE_APPLY_BUTTON.md
- Report with console output

---

**Happy analyzing! 📊**

For detailed step-by-step instructions, see: `TESTING_GUIDE_APPLY_BUTTON.md`
