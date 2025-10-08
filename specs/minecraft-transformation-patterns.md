# Minecraft Java Edition Transformation Patterns

**Date:** 2025-10-08
**webpage links:** ai_doc/downloaded_pages/crafting.html, ai_doc/downloaded_pages/smelting.html, ai_doc/downloaded_pages/trading.html, ai_doc/downloaded_pages/mob.html, ai_doc/downloaded_pages/witch.html, ai_doc/downloaded_pages/smithing.html, ai_doc/downloaded_pages/stonecutter.html, ai_doc/downloaded_pages/drops.html

## Pattern requirements

The user wants to extract all transformation recipes from Minecraft Java Edition to build a directed graph. Each transformation should capture:
- **Transformation type**: crafting, smelting, trading, mob drops, smithing, stonecutter, etc.
- **Input items**: name and wiki URL for each input item
- **Output items**: name and wiki URL for output item
- **Quantities**: how many of each item (if applicable)

## Pattern found

### 1. Crafting Recipes

**HTML Structure Pattern:**
```
<span class="mcui mcui-Crafting_Table pixel-image">
  <span class="mcui-input">
    <span class="mcui-row">
      <span class="invslot">
        <span class="invslot-item invslot-item-image">
          <span typeof="mw:File">
            <a href="/w/[ITEM_NAME]" title="[ITEM_NAME]">
              <img alt="..." src="/images/Invicon_[ITEM_NAME].png?..." />
            </a>
          </span>
        </span>
      </span>
      <!-- More slots in this row -->
    </span>
    <!-- More rows (3 total for crafting table) -->
  </span>
  <span class="mcui-arrow"></span>
  <span class="mcui-output">
    <span class="invslot invslot-large">
      <span class="invslot-item invslot-item-image">
        <span typeof="mw:File">
          <a href="/w/[OUTPUT_NAME]" title="[OUTPUT_NAME]">
            <img alt="..." src="/images/Invicon_[OUTPUT_NAME].png?..." />
          </a>
        </span>
      </span>
    </span>
  </span>
</span>
```

**Key identifiers:**
- CSS class `mcui-Crafting_Table` indicates crafting recipes
- `mcui-input` contains 9 slots arranged in 3 rows (3x3 grid)
- Each `invslot` can contain 0 or 1 item
- `invslot animated` indicates multiple alternative inputs (animated cycling)
- `mcui-output` contains the result
- Item links are in format `/w/[Item_Name]` (URL-encoded)
- Shapeless recipes are marked with intertwined arrows icon

**Extraction logic:**
1. Find all `<span class="mcui mcui-Crafting_Table pixel-image">`
2. Within `mcui-input`, extract all `<a href="/w/...">` links from `invslot-item-image` spans
3. If `invslot animated`, extract all alternative items (multiple `invslot-item` children)
4. Extract output from `mcui-output` section
5. Grid position matters for shaped recipes (row/column structure preserved)
6. Empty `invslot` (no child `invslot-item`) = no ingredient in that position

### 2. Smelting Recipes

**HTML Structure Pattern:**
Similar to crafting but uses furnace/blast furnace UI. Look for:
```
<span class="mcui mcui-Furnace pixel-image">
```
or
```
<span class="mcui mcui-Blast_Furnace pixel-image">
```

**Key identifiers:**
- `mcui-Furnace` or `mcui-Blast_Furnace` class
- Single input slot (ingredient)
- Fuel slot (usually not captured as part of recipe)
- Single output slot
- May include smelting time information

**Extraction logic:**
1. Find all furnace/blast furnace UI elements
2. Extract input item from input slot
3. Extract output item from output slot
4. Note: Fuel is separate and not part of recipe definition

### 3. Smithing Recipes

**HTML Structure Pattern:**
```
<span class="mcui mcui-Smithing_Table pixel-image">
  <span class="mcui-smithingTable">
    <span class="invslot mcui-input1"> <!-- Template -->
      <span class="invslot-item">
        <a href="/w/[TEMPLATE_NAME]">...</a>
      </span>
    </span>
    <span class="invslot mcui-input2"> <!-- Base item -->
      <span class="invslot-item">
        <a href="/w/[BASE_ITEM]">...</a>
      </span>
    </span>
    <span class="invslot mcui-input3"> <!-- Addition material -->
      <span class="invslot-item">
        <a href="/w/[MATERIAL]">...</a>
      </span>
    </span>
  </span>
  <span class="mcui-arrow"></span>
  <span class="mcui-output">
    <a href="/w/[OUTPUT_NAME]">...</a>
  </span>
</span>
```

**Key identifiers:**
- `mcui-Smithing_Table` class
- Three inputs: `mcui-input1` (template), `mcui-input2` (base), `mcui-input3` (material)
- Single output
- Used for netherite upgrades and armor trims

**Extraction logic:**
1. Find all `mcui-Smithing_Table` elements
2. Extract template from `mcui-input1`
3. Extract base item from `mcui-input2`
4. Extract addition material from `mcui-input3`
5. Extract output item

### 4. Stonecutter Recipes

**HTML Structure Pattern:**
Similar to crafting but simpler - one input, one output. Look for stonecutter-specific classes or tables showing stone block conversions.

**Key identifiers:**
- Typically shown in tables or simple input→output format
- One input block → multiple possible output options
- More efficient than crafting table for certain recipes

### 5. Trading (Villagers)

**HTML Structure Pattern:**
```
<table class="wikitable">
  <tr>
    <th>Level</th>
    <th>Item wanted</th>
    <th>Item given</th>
    <th>Trades in stock</th>
    <!-- More columns -->
  </tr>
  <tr>
    <td>Novice</td>
    <td>15 × <a href="/w/Coal">Coal</a></td>
    <td><a href="/w/Emerald">Emerald</a></td>
    <td>16</td>
    <!-- More columns -->
  </tr>
</table>
```

**Key identifiers:**
- `<table class="wikitable">` with trading data
- `data-description="[Villager_Type]"` attribute identifies villager profession
- Columns: "Item wanted", "Item given"
- Quantities indicated before item name (e.g., "15 × ")
- Item links in format `/w/[Item_Name]`
- Multiple items may be required (addition/concatenation)
- Villager level affects available trades

**Extraction logic:**
1. Find all `<table class="wikitable">` with trading structure
2. Identify villager type from `data-description` or header
3. For each row, extract "Item wanted" and "Item given"
4. Parse quantities (number before "×")
5. Extract item names and links
6. Note trading level (Novice, Apprentice, Journeyman, Expert, Master)

### 6. Mob Drops

**HTML Structure Pattern:**
```
<h2>Drops</h2>
<table class="wikitable">
  <tr>
    <th>Item</th>
    <th>Quantity / Chance / Average</th>
  </tr>
  <tr>
    <td><a href="/w/Redstone_Dust">Redstone Dust</a></td>
    <td>4–8</td>
    <td>100.00%</td>
    <td>6.00</td>
  </tr>
</table>
```

**Key identifiers:**
- Section heading `<h2>Drops</h2>` or similar
- `<table class="wikitable">` containing drop data
- Columns for item, quantity, chance/probability
- Multiple looting levels shown (Default, Looting I, II, III)
- Probability percentages or fractions
- Quantity ranges (e.g., "4–8", "0–6")

**Extraction logic:**
1. Identify mob from page title or heading
2. Find "Drops" section (look for `id="Drops"` or heading)
3. Extract table with drop information
4. For each row:
   - Extract item name and link
   - Extract quantity (base/default)
   - Extract probability/chance
   - Note: Looting affects quantities
5. Source entity: mob being killed
6. Output: dropped items with probabilities

### 7. General Item Link Pattern

**All item references use this pattern:**
```html
<a href="/w/[Item_Name]" title="[Item Name]">
  <img alt="Invicon [Item Name].png: ..." src="/images/Invicon_[Item_Name].png?..." />
</a>
```

**Item URL format:**
- Base URL: `https://minecraft.wiki`
- Item path: `/w/[Item_Name]`
- Names are URL-encoded (spaces become underscores)
- Example: "Iron Ingot" → `/w/Iron_Ingot`

**Extraction steps:**
1. Find `<a>` tags with `href="/w/..."`
2. Extract `href` attribute value
3. Extract `title` attribute for display name
4. Full URL = `https://minecraft.wiki` + href value
5. Item name can be extracted from either href (decode underscores) or title attribute

### 8. Animated/Alternative Ingredients

**Pattern for multiple alternative inputs:**
```html
<span class="invslot animated">
  <span class="invslot-item invslot-item-image animated-active">
    <a href="/w/Iron_Ingot">Iron Ingot</a>
  </span>
  <span class="invslot-item invslot-item-image">
    <a href="/w/Gold_Ingot">Gold Ingot</a>
  </span>
  <span class="invslot-item invslot-item-image">
    <a href="/w/Diamond">Diamond</a>
  </span>
</span>
```

**Key identifiers:**
- `invslot animated` class indicates alternatives
- Multiple `invslot-item` children = OR relationship
- Only one is used per recipe execution
- `animated-active` indicates currently displayed item

**Graph representation:**
- Create multiple recipe edges, one per alternative
- OR relationship between alternatives (not AND)

## Ambiguous finding

### 1. Bedrock Edition vs Java Edition

**Issue:** Some pages contain both Bedrock and Java Edition information.

**Indicators to filter Java Edition only:**
- Look for headers/sections marked "Java Edition"
- Tables may have columns for different editions
- Check for class or data attributes containing "java"
- Icon/sprite files may indicate edition: `EntitySprite_` patterns

**Recommended approach:**
- Filter out sections marked "Bedrock Edition" or "Bedrock-specific"
- When tables have edition columns, only extract Java Edition rows
- Look for text like "In Java Edition" or edition-specific headers

### 2. Recipe Variants and Tags

**Issue:** Some recipes accept item tags/groups (e.g., "any wood planks").

**Pattern:**
- Generic item names like "Planks", "Wood", "Logs"
- Hover text or data attributes may list valid items
- May need to expand tags to individual items or create tag nodes

**Recommended approach:**
- Option 1: Create a tag node that links to all valid items
- Option 2: Create separate edges for each valid item in the tag
- Option 3: Store tag information as metadata on the edge

### 3. Quantity Information

**Issue:** Quantities are sometimes implicit.

**Examples:**
- No quantity shown = 1 item
- "15 × Coal" = 15 coal items required
- Crafting grid may show multiple of same item in different slots

**Recommended approach:**
- Count occurrences of same item in crafting grid
- Parse "N × Item" format in trading
- Default to 1 if no quantity specified
- For ranges (e.g., "4–8"), use average or store as range

### 4. Shapeless vs Shaped Recipes

**Issue:** Some crafting recipes care about ingredient position (shaped), others don't (shapeless).

**Indicators:**
- Shapeless marked with intertwined arrows icon
- Class or data attribute may indicate recipe type
- Text annotation "shapeless" may appear

**Recommended approach:**
- Add recipe metadata: `shaped` or `shapeless`
- Shaped recipes preserve grid positions
- Shapeless recipes just list ingredients

### 5. Conditional Drops

**Issue:** Mob drops have probabilities and conditions (looting level, player-killed vs natural death, etc.).

**Recommended approach:**
- Store probability as edge weight or metadata
- Default to base drop rate (no looting)
- May want separate edges for different looting levels
- Note conditions in edge metadata (e.g., "requires_player_kill")

### 6. Enchanted Items

**Issue:** Some outputs are enchanted (e.g., "Enchanted Diamond Sword").

**Pattern:**
- Item name includes "Enchanted"
- Image filename may contain "Enchanted"
- Enchantments vary and are random

**Recommended approach:**
- Treat as separate item or add metadata flag
- Link to base item page if enchanted version redirects

### 7. Stonecutter Efficiency

**Issue:** Stonecutter provides more efficient recipes than crafting table for certain items.

**Recommended approach:**
- Track transformation type (crafting vs stonecutter)
- Both edges may exist for same input→output
- Stonecutter typically produces more output for same input

### 8. Recipe Unlocking

**Issue:** Some recipes require unlocking via achievements/advancements.

**Recommended approach:**
- This affects game mechanics but not graph structure
- May add as edge metadata if needed

## Notes

### Additional Transformation Types to Consider

1. **Brewing**: Potions created in brewing stands
   - Similar pattern to smelting (base + ingredient → result)
   - Look for brewing stand UI patterns

2. **Enchanting**: Adding enchantments to items
   - Input: item + lapis lazuli
   - Output: enchanted item
   - Randomized, level-dependent

3. **Composting**: Converting items to bone meal
   - Multiple items can be composted
   - Look for composter-related tables

4. **Loot Chests**: Items found in generated chests
   - Listed in loot table pages
   - Probability-based

5. **Natural Generation**: Blocks that generate naturally
   - Not really a "transformation" but affects item availability
   - May be out of scope

### Data Structure Recommendation

For building the graph, consider this structure:

```json
{
  "transformation_type": "crafting|smelting|trading|mob_drop|smithing|stonecutter|brewing|...",
  "inputs": [
    {
      "item_name": "Iron Ingot",
      "item_url": "https://minecraft.wiki/w/Iron_Ingot",
      "quantity": 9,
      "position": {"row": 0, "col": 0}  // For shaped recipes only
    }
  ],
  "outputs": [
    {
      "item_name": "Block of Iron",
      "item_url": "https://minecraft.wiki/w/Block_of_Iron",
      "quantity": 1
    }
  ],
  "metadata": {
    "shaped": true,
    "probability": 1.0,  // For mob drops
    "villager_type": "Armorer",  // For trading
    "villager_level": "Novice",  // For trading
    "looting_level": 0  // For mob drops
  }
}
```

### Parsing Strategy

1. **Download all relevant pages**:
   - Main recipe pages (crafting, smelting, etc.)
   - Individual mob pages for drops
   - Trading page with all villager types
   - Smithing, stonecutter pages

2. **Parse HTML**:
   - Use BeautifulSoup or similar HTML parser
   - Search for specific CSS classes and structures
   - Extract all `<a>` tags with `/w/` hrefs

3. **Build graph**:
   - Nodes: unique items (by URL)
   - Edges: transformations (directed, with type and metadata)
   - Consider using NetworkX or similar graph library

4. **Handle special cases**:
   - Animated slots → multiple edges
   - Probability-based drops → weighted edges
   - Alternative recipes → multiple edges same input/output

### File Organization Recommendation

- `items/`: Extract and cache all unique items
- `transformations/`: Extract all transformation recipes by type
- `graph/`: Build final graph structure
- Consider JSON or CSV intermediate format for easier debugging

### Java Edition Filtering

To ensure only Java Edition content:
1. Check page headers for edition indicators
2. Look for "Java Edition" text in sections
3. Avoid "Bedrock Edition" or "Bedrock-specific" sections
4. Some pages have tabbed interfaces - select Java tab
5. When in doubt, prefer information without edition qualifiers (usually Java)
