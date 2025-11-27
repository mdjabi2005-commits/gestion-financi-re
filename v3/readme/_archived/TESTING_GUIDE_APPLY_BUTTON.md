# 🧪 TESTING GUIDE - "Appliquer les Sélections" Button

## 📋 Overview

This document provides step-by-step instructions to test the new **"✅ Appliquer les Sélections"** button that synchronizes fractal selections with the table display.

---

## 🎯 What Should Happen

1. **User selects triangles** at the last level (selections saved to localStorage)
2. **User clicks "✅ Appliquer les Sélections" button** in the left column
3. **Button handler intercepts click** and reads selections from localStorage
4. **URL is updated** with query parameter: `?fractal_selections=CODE1,CODE2,...`
5. **Page reloads automatically**
6. **Streamlit reads URL params** and displays filtered table in right column

---

## 🧪 Step-by-Step Testing

### SETUP
```
1. Open browser console: F12 → Console tab
2. Clear previous logs (optional)
3. Navigate to: http://localhost:8501/
4. Start fresh Streamlit session
```

### STEP 1️⃣: Navigate to Last Level

```
1. Click: Univers Financier (TR)
2. Click: Revenus (or Dépenses)
3. Click: A category (e.g., Uber, Bureau_Vallée)
4. Click: A subcategory (e.g., Septembre, Octobre, Novembre)

Expected:
- You should see multiple small blue triangles (leaf nodes)
- Console should show: [FRACTAL] ✅ Niveau 3 → MODE SÉLECTION
- isSelectionMode should be: true
- navigationStack length should be: 4
```

### STEP 2️⃣: Select Triangles

```
1. Click on the first triangle (it should turn BRIGHT BLUE with ✓)
2. Click on a second triangle

Expected Console Logs:
[FRACTAL] 🟢 Sélectionné: SUBCAT_REVENUS_UBER_SEPTEMBRE
[FRACTAL] 🟢 Sélectionné: SUBCAT_REVENUS_UBER_OCTOBRE
[FRACTAL] Sélections actuelles: (2) ['SUBCAT_REVENUS_UBER_SEPTEMBRE', 'SUBCAT_REVENUS_UBER_OCTOBRE']

Visual Feedback:
- Triangles turn bright blue
- A checkmark ✓ appears in corners
- Glow effect around selected triangles
```

### STEP 3️⃣: Locate "Appliquer les Sélections" Button

```
1. Scroll DOWN in the LEFT COLUMN (below the triangles)
2. You should see a blue button that says: ✅ Appliquer les Sélections

Expected:
- Button is visible and clickable
- Button spans full width of left column
- It's positioned right after the horizontal separator line (---)
```

### STEP 4️⃣: Click the Button

```
1. Click the "✅ Appliquer les Sélections" button

Expected Console Logs:
[BUTTON-SETUP] Found apply button
[BUTTON-HANDLER] Button clicked!
[BUTTON-HANDLER] Found selections: SUBCAT_REVENUS_UBER_SEPTEMBRE,SUBCAT_REVENUS_UBER_OCTOBRE
[BUTTON-HANDLER] Updating URL to: /?fractal_selections=SUBCAT_REVENUS_UBER_SEPTEMBRE%2CSUBCAT_REVENUS_UBER_OCTOBRE
[BUTTON-HANDLER] ✅ URL updated, reloading...

Visual Feedback:
- Button might briefly appear pressed/highlighted
- Page should reload automatically after ~100ms
- You should hear/see loading indicator briefly
```

### STEP 5️⃣: Verify URL Update

```
1. After reload completes, check the browser address bar
2. Look for: ?fractal_selections=SUBCAT_...

Expected URL Format:
http://localhost:8501/?fractal_selections=SUBCAT_REVENUS_UBER_SEPTEMBRE,SUBCAT_REVENUS_UBER_OCTOBRE

(The exact format may have encoded characters like %2C for comma, that's normal)
```

### STEP 6️⃣: Check Right Column for Table

```
1. Look at the RIGHT COLUMN after page reloads
2. Below "📊 Transactions Filtrées" you should see:

✅ EXPECTED RESULT:
┌─────────────────────────────────────────┐
│ 🎯 Filtres Actifs                       │
│ 🔹 Septembre                            │ ❌ (to remove)
│ 🔹 Octobre                              │ ❌ (to remove)
│                                         │
│ ─────────────────────────────────────── │
│                                         │
│ 📋 Trans.  [count]                      │
│ 💹 Rev.    [amount]€                    │
│ 💸 Dép.    [amount]€                    │
│ 📈 Solde   [amount]€                    │
│                                         │
│ ─────────────────────────────────────── │
│                                         │
│ Transactions:                           │
│ [Table with filtered rows]              │
│                                         │
│ 💾 Exporter CSV                         │
└─────────────────────────────────────────┘

❌ IF TABLE IS MISSING:
[Table not visible or empty message shown]
```

---

## 🔍 DEBUG CHECKLIST

Mark each item as you verify:

### JavaScript Side (F12 → Console)
```
[ ] See [BUTTON-SETUP] Found apply button
[ ] See [BUTTON-HANDLER] Button clicked! when you click button
[ ] See Found selections: [something not empty]
[ ] See URL updated to: [has fractal_selections param]
[ ] See URL updated, reloading... message
[ ] NO red error messages
```

### Python/Streamlit Side (Right Column DEBUG)
```
[ ] Expand "🔍 DEBUG - État Actuel"
[ ] See "URL Query Params:" shows fractal_selections
[ ] See "Session State Filters:" (if visible)
[ ] See selections_from_url is NOT empty
[ ] See "Parsed X codes from URL:" message
```

### Visual UI
```
[ ] Button "✅ Appliquer les Sélections" is visible
[ ] Triangles show blue glow when selected
[ ] Triangles show checkmark ✓
[ ] Table appears in right column AFTER button click
[ ] Filters badges show with ❌ remove buttons
[ ] Statistics cards show numbers
[ ] Transactions table shows data rows
```

---

## 🐛 Troubleshooting

### ISSUE #1: Button doesn't appear

**Possible Causes:**
- Streamlit didn't reload the page
- You're not scrolled down in the left column

**Solutions:**
```
1. Scroll DOWN in the left column to see the button
2. If still not visible, refresh the page (F5)
3. Check console for errors: F12 → Console tab
4. Look for any error messages in red
```

### ISSUE #2: Button appears but nothing happens

**Possible Causes:**
- JavaScript handler not initialized
- Click event not being captured

**Solutions:**
```
1. Open F12 → Console
2. Manually run:
   const state = JSON.parse(localStorage.getItem('fractal_state_v6') || '{}');
   console.log('State:', state);
   console.log('Selections:', state.selectedNodes);

3. If empty → you didn't select any triangles first
4. If present → JavaScript handler issue
```

### ISSUE #3: Console shows logs but URL doesn't change

**Possible Causes:**
- `window.history.replaceState()` failed
- Permission issues with URL modification

**Solutions:**
```
1. Check browser console for errors
2. Try manually in console:
   window.history.replaceState({}, '', '/?test=1');
   console.log('URL now:', window.location.href);

3. If URL doesn't change → browser security issue
4. Try different browser (Chrome, Firefox, etc.)
```

### ISSUE #4: URL changes but table doesn't appear

**Possible Causes:**
- Streamlit not reading query params correctly
- Selections don't match any transactions in database
- Table rendering issue

**Solutions:**
```
1. Check the DEBUG section (expand on right column)
2. Verify: "URL Query Params:" shows the selections
3. Verify: "selections_from_url" is NOT empty
4. Check: "Parsed X codes from URL:" count > 0

5. If DEBUG shows 0 codes parsed:
   → The URL parsing is failing
   → Check the exact URL in address bar

6. If DEBUG shows codes but no table:
   → The database might not have transactions for those selections
   → Try selecting a different category
```

### ISSUE #5: Console shows "No selections found"

**Cause:**
- You didn't select any triangles before clicking the button

**Solution:**
```
1. Make sure triangles turn BLUE when you click them
2. You should see green checkmarks on selected triangles
3. Console should show: [FRACTAL] 🟢 Sélectionné: ...
4. THEN click the button
```

---

## 🎯 Expected Console Output (Full Success)

When everything works, your console should show this sequence:

```javascript
// Initial page load
[BUTTON-SETUP] Found apply button
[SYNC-INIT] Initializing URL-based synchronization...
[SYNC-URL] syncStateToURL called
[SYNC-URL]   selections: (0) []  // Empty because no selections yet
...

// After selecting triangles
[FRACTAL] ✅ Niveau 3 → MODE SÉLECTION
[FRACTAL] 🟢 Sélectionné: SUBCAT_REVENUS_UBER_SEPTEMBRE
[FRACTAL] 🟢 Sélectionné: SUBCAT_REVENUS_UBER_OCTOBRE
[FRACTAL] Sélections actuelles: (2) ['SUBCAT_REVENUS_UBER_SEPTEMBRE', 'SUBCAT_REVENUS_UBER_OCTOBRE']

// After clicking button
[BUTTON-HANDLER] Button clicked!
[BUTTON-HANDLER] Found selections: SUBCAT_REVENUS_UBER_SEPTEMBRE,SUBCAT_REVENUS_UBER_OCTOBRE
[BUTTON-HANDLER] Updating URL to: /?fractal_selections=SUBCAT_REVENUS_UBER_SEPTEMBRE%2CSUBCAT_REVENUS_UBER_OCTOBRE
[BUTTON-HANDLER] ✅ URL updated, reloading...

// After page reload
[BUTTON-SETUP] Found apply button  // Button setup on new page
...
// Table should now appear in right column
```

---

## 📊 Test Scenarios

### Scenario 1: Single Selection
```
1. Navigate: TR → Revenus → Uber → Septembre
2. Click ONE triangle
3. Click button
4. Expected: Table with September data only
```

### Scenario 2: Multi-Selection (Same Category)
```
1. Navigate: TR → Revenus → Uber
2. See 4 triangles (months)
3. Click Septembre, then Octobre, then Novembre (3 selections)
4. Click button
5. Expected: Table with September + October + November combined
```

### Scenario 3: Multi-Selection (Different Categories)
```
1. Navigate: TR → Revenus → Uber → Septembre
2. Click Septembre (gets blue + checkmark)
3. Navigate BACK to Revenus
4. Navigate to Bureau → March
5. Click March (gets blue + checkmark, now 2 selected total)
6. Click button
7. Expected: Table with September + March combined
```

### Scenario 4: Deselection
```
1. Navigate: TR → Revenus → Uber → Septembre
2. Click Septembre (turns blue)
3. Click Septembre AGAIN (should turn back to normal, un-selected)
4. Verify: Console shows different selection count
5. Click button
6. Expected: Should either show error or table for remaining selections
```

---

## 📝 Report Template

If issues occur, provide:

```
1. **Browser & OS:**
   Chrome/Firefox, Windows/Mac/Linux

2. **Console Screenshot:**
   [Paste all [BUTTON-*] and [FRACTAL] logs]

3. **URL in Address Bar:**
   [Paste exact URL shown]

4. **DEBUG Section Output:**
   [Screenshot of right column DEBUG expander]

5. **Selections Made:**
   [List what triangles you selected]

6. **What Happened:**
   [Step by step what you did and observed]

7. **What Was Expected:**
   [What should have happened]
```

---

## 🎉 Success Criteria

✅ **Complete Success:**
- Button appears below triangles
- Button click is registered (console shows [BUTTON-HANDLER] logs)
- URL updates with fractal_selections parameter
- Page reloads
- Table appears in right column with filtered data
- Filters show as badges with remove buttons
- Statistics show correct counts/amounts

✅ **Partial Success (Good Starting Point):**
- Button appears and can be clicked
- Console shows some [BUTTON-HANDLER] logs
- [Even if table doesn't appear yet, we can debug]

❌ **Failure (Needs Investigation):**
- Button doesn't appear
- No console logs appear when clicking button
- JavaScript errors in console (red messages)

---

## 🚀 Next Steps if Successful

1. Test multiple different categories and selections
2. Test the remove buttons (❌) on filter badges
3. Test the CSV export button
4. Test navigating to different levels while filters active
5. Test clearing all selections

---

**Let me know the results of this testing! 🧪**
