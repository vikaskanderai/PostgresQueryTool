# Project Specification: Phase 2 - Granular Script Generator

## 1. Goal
Close the "Granularity Gap" by allowing users to selectively pick database objects (Tables, Views, Procedures, Functions) and generate a single, dependency-ordered DDL script using a high-performance backend engine.

## 2. Updated System Workflow
1.  **Authentication:** User connects as Superuser (Phase 1/2 logic).
2.  **Feature Selector (New):** A high-priority popup appears offering two paths:
    *   **Path A:** Real-Time Query Streamer.
    *   **Path B:** Script Generator.
3.  **Object Selection:** User searches and selects specific objects from a categorized list.
4.  **Generation:** The app calls the `generate_deployment_scripts` function in Postgres.
5.  **Export:** User previews, copies, or downloads the generated SQL script.

---

## 3. Modular Architecture Additions
```text
pg_logger/
├── backend/
│   ├── script_engine.py    # Logic to list objects and call the DDL function
│   └── ddl_template.sql    # The PL/pgSQL function code for injection
└── frontend/
    ├── selector.py         # Feature Selection Modal
    └── script_ui.py        # Object Picker and Script Preview components
```

---

## 4. Technical Components

### **A. Feature Selection Modal (`frontend/selector.py`)**
*   **Design:** Two large interactive cards with icons and descriptions.
*   **Logic:** Sets `AppState.current_page` to either "monitor" or "generator".

### **B. Object Discovery (`backend/script_engine.py`)**
*   **Purpose:** Populate the UI "Picker" with available objects.
*   **SQL Logic:** Query `pg_class` (tables/views) and `pg_proc` (functions/procs), excluding system schemas (`pg_catalog`, `information_schema`).
*   **Output:** A list of strings in `schema.object_name` format.

### **C. The Scripting Engine**
*   **Function Integration:** The app uses the `generate_deployment_scripts(TEXT[])` PL/pgSQL function.
*   **Injection:** Upon first use, the app checks if the function exists; if not, it prompts the user to "Initialize Scripting Engine" (executes the DDL).
*   **Execution:** Calls the function via `asyncpg.fetchval()` passing the array of selected strings.

---

## 5. UI/UX Requirements
*   **The Picker:** A searchable, paginated list of checkboxes.
*   **Categorization:** Tabs to filter between "Tables," "Views," and "Logic (Procs/Functions)."
*   **Live Counter:** Floating badge showing the count of currently selected objects.
*   **The Previewer:** A syntax-highlighted read-only text area showing the result of the `RETURN TEXT` from the SQL function.

---

## 6. Developer Task Checklist: Phase 2

### **Step 1: The Gateway**
- [ ] Create `frontend/selector.py` modal component.
- [ ] Add `AppState.selected_feature` logic to `state.py`.
- [ ] Update `AppState.connect_to_database` to trigger the selector upon success.

### **Step 2: Metadata Discovery**
- [ ] Implement `backend/script_engine.py` to fetch object names categorized by type.
- [ ] Build the searchable checklist in `frontend/script_ui.py`.
- [ ] Add "Select All / Deselect All" functionality.

### **Step 3: Engine Integration**
- [ ] Create a "Check/Initialize Engine" button in the UI to inject the PL/pgSQL function code.
- [ ] Implement the `generate_script` action: Gathers selected strings -> Calls DB function -> Stores result in `AppState.generated_sql`.

### **Step 4: Export & Polish**
- [ ] Implement "Copy to Clipboard" using `rx.set_clipboard`.
- [ ] Implement "Download .sql" button.
- [ ] Add a "Switch Feature" button in the header to return to the Selector.

---

## 7. Competitive Edge Reminder
*   **Granularity:** Unlike `pg_dump`, we allow picking a **single Function**.
*   **Dependency Awareness:** The PL/pgSQL backend ensures Tables are created before Views that depend on them.
*   **Native Performance:** Generating scripts inside the DB is 10x faster than pulling raw metadata to the client.