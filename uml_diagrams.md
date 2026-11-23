# MediFlow IMS - UML Diagrams Catalog

This catalog contains six standard UML diagrams describing the architecture, workflows, structure, and execution environment of **MediFlow IMS (Medical Store Inventory System)**. 

All diagrams are written in **Mermaid syntax** and will render natively in supported Markdown previewers (like VS Code, GitHub, Obsidian). You can easily export them to high-resolution images or vector graphics to include in your **Mini Project PowerPoint (PPT)** presentation.

---

## 📋 Table of Contents
1. [Use-Case Diagram](#1-use-case-diagram)
2. [Activity Diagram (Sales Transaction Flow)](#2-activity-diagram-sales-transaction-flow)
3. [Class Diagram](#3-class-diagram)
4. [Component Diagram](#4-component-diagram)
5. [Sequence Diagram (Adding a New Medicine)](#5-sequence-diagram-adding-a-new-medicine)
6. [Deployment Diagram](#6-deployment-diagram)
7. [🖥️ How to Convert Diagrams and Text into a PowerPoint Presentation](#%EF%B8%8F-how-to-convert-diagrams-and-text-into-a-powerpoint-presentation)

---

## 1. Use-Case Diagram

The Use-Case Diagram represents the functional scope of MediFlow IMS from the perspective of the system's primary user (Pharmacist/Administrator) and the secondary system component (the CSV database).

### Mermaid Diagram

```mermaid
graph LR
    %% Actors
    Pharmacist["👤 Pharmacist / Administrator"]
    SystemDB["💾 Flat File DB (CSVs)"]

    %% Use Cases
    UC_Login(["🔑 User Authentication<br>(Login/Register)"])
    UC_Dash(["📊 View Dashboard Analytics<br>(KPIs & Plotly Trends)"])
    UC_AddMed(["➕ Add New Medicine<br>(with validation)"])
    UC_ViewMed(["📋 View & Search Directory<br>(CRUD - Edit/Delete)"])
    UC_UpdateStock(["🔄 Update Stock Levels<br>(Sliders & Alerts)"])
    UC_Sales(["🛒 Process Sales & Billing<br>(Verify, Invoice, Receipt)"])
    UC_Expiry(["⏳ Track Expired Batches<br>(Compliance Reports)"])
    UC_Reports(["📈 Generate Reports<br>(CSV Exporter)"])
    UC_Settings(["⚙️ System Administration<br>(Reset Database, Suppliers)"])

    %% Links
    Pharmacist --> UC_Login
    Pharmacist --> UC_Dash
    Pharmacist --> UC_AddMed
    Pharmacist --> UC_ViewMed
    Pharmacist --> UC_UpdateStock
    Pharmacist --> UC_Sales
    Pharmacist --> UC_Expiry
    Pharmacist --> UC_Reports
    Pharmacist --> UC_Settings

    UC_AddMed --> SystemDB
    UC_ViewMed --> SystemDB
    UC_UpdateStock --> SystemDB
    UC_Sales --> SystemDB
    UC_Expiry --> SystemDB
    UC_Reports --> SystemDB
    UC_Settings --> SystemDB
    UC_Login --> SystemDB

    %% Subgraph styling for system boundary
    subgraph MediFlow IMS System Boundary
        UC_Login
        UC_Dash
        UC_AddMed
        UC_ViewMed
        UC_UpdateStock
        UC_Sales
        UC_Expiry
        UC_Reports
        UC_Settings
    end

    classDef actor fill:#0d9488,stroke:#0f766e,stroke-width:2px,color:#fff,font-weight:bold;
    classDef usecase fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b;
    class Pharmacist,SystemDB actor;
    class UC_Login,UC_Dash,UC_AddMed,UC_ViewMed,UC_UpdateStock,UC_Sales,UC_Expiry,UC_Reports,UC_Settings usecase;
```

### 📝 PPT Slide Notes
- **Title**: Use-Case Diagram: System Boundaries and Actor Interactions
- **Primary Actor**: **Pharmacist / Administrator** interacts with the graphical interface to perform inventory tasks, process bills, and download records.
- **Secondary Actor**: **Flat-File CSV Database System** handles storage operations, ensuring read/write commands trigger dynamically.
- **Key Relationships**: System restricts unauthorized users via the **User Authentication** module. Once logged in, the pharmacist runs core transactional operations which write directly to the CSV files.

---

## 2. Activity Diagram (Sales Transaction Flow)

This diagram tracks the behavioral control flow within the **Sales & Invoicing Module** (`Sales.py`). It highlights validation checkpoints, error states, database writes, and billing updates.

### Mermaid Diagram

```mermaid
flowchart TD
    Start([🟢 Start]) --> ViewSalesPage[Open Sales & Invoicing Page]
    ViewSalesPage --> EnterDetails[Enter Transaction Details:<br>Medicine ID/Name, Quantity, Customer, Price]
    EnterDetails --> CheckStock{Is Stock Quantity<br>Sufficient?}
    
    CheckStock -- No --> ShowStockAlert[Show Insufficient Stock Notification]
    ShowStockAlert --> AdjustQty[Adjust Order Quantity]
    AdjustQty --> EnterDetails
    
    CheckStock -- Yes --> ValidateForm{Validate Price &<br>Numeric Fields}
    
    ValidateForm -- Invalid --> ShowValErr[Display Validation Error Toast]
    ShowValErr --> EditFields[Correct Form Inputs]
    EditFields --> EnterDetails
    
    ValidateForm -- Valid --> AddToCart[Add Item to Bill Cart]
    AddToCart --> CheckMore{Add More Medicines?}
    
    CheckMore -- Yes --> EnterDetails
    
    CheckMore -- No --> ProcessCheckout[Confirm Sales Checkout]
    ProcessCheckout --> UpdateMedsCSV[Deduct Stock Quantities from medicines.csv]
    UpdateMedsCSV --> WriteSalesCSV[Append Sales Transaction to sales.csv]
    WriteSalesCSV --> PrintReceipt[Render Print-Ready Bill Receipt on Screen]
    PrintReceipt --> SuccessToast[Show Transaction Completed Successfully Toast]
    SuccessToast --> End([🔴 End])

    classDef startEnd fill:#0d9488,stroke:#0f766e,stroke-width:2px,color:#fff;
    classDef process fill:#f8fafc,stroke:#64748b,stroke-width:1.5px,color:#1e293b;
    classDef decision fill:#fef08a,stroke:#eab308,stroke-width:2px,color:#854d0e;
    classDef error fill:#fee2e2,stroke:#ef4444,stroke-width:1.5px,color:#991b1b;
    
    class Start,End startEnd;
    class ViewSalesPage,EnterDetails,AddToCart,ProcessCheckout,UpdateMedsCSV,WriteSalesCSV,PrintReceipt,SuccessToast process;
    class CheckStock,ValidateForm,CheckMore decision;
    class ShowStockAlert,AdjustQty,ShowValErr,EditFields error;
```

### 📝 PPT Slide Notes
- **Title**: Activity Diagram: Sales & Billing Workflow
- **Workflow Highlights**:
  - **Stock Check Validation**: Automatically verifies stock volumes in real-time before checkout. If requested levels exceed inventory margins, the transaction is halted.
  - **Data Integrity**: Checks numeric boundaries (e.g., negative prices/quantities) before checkout confirmation.
  - **Atomic DB Update**: Deducts inventory levels from `medicines.csv` and records receipt summaries to `sales.csv` in sequence.

---

## 3. Class Diagram

This Class Diagram details the structural code design. Although Streamlit is script-based, this diagram models the system's logical utility modules, analytical services, and CSV-schema representation fields as classes.

### Mermaid Diagram

```mermaid
classDiagram
    class MedicineCSV {
        +String medicine_id
        +String medicine_name
        +String category
        +String manufacturer
        +String batch_number
        +Date purchase_date
        +Date expiry_date
        +int quantity
        +float unit_price
        +String supplier_name
    }

    class SaleRecordCSV {
        +String invoice_number
        +String medicine_id
        +String medicine_name
        +int quantity_sold
        +float selling_price
        +String customer_name
        +Date sale_date
        +float total_amount
    }

    class SupplierCSV {
        +String supplier_id
        +String supplier_name
        +String contact_person
        +String phone
        +String email
        +String address
    }

    class UserCSV {
        +String username
        +String password_hash
        +String email
        +Date signup_date
    }

    class FileHandler {
        +DATA_DIR: String
        +MEDICINES_FILE: String
        +SALES_FILE: String
        +SUPPLIERS_FILE: String
        +init_files(reset: bool)
        +ensure_directories()
        +generate_sample_medicines() List
        +generate_sample_sales() List
        +load_medicines() DataFrame
        +save_medicines(df: DataFrame) bool
        +load_sales() DataFrame
        +save_sales(df: DataFrame) bool
        +load_suppliers() DataFrame
        +save_suppliers(df: DataFrame) bool
    }

    class AuthManager {
        +USERS_EXCEL: String
        +USERS_CSV: String
        +hash_password(password: String) String
        +init_users_file()
        +load_users() DataFrame
        +save_users(df: DataFrame) bool
        +register_user(username, password, email) Tuple[bool, String]
        +authenticate_user(username, password) Tuple[bool, String]
    }

    class ValidationEngine {
        +validate_medicine_fields(data: dict) Tuple[bool, list]
        +validate_sales_fields(data: dict) Tuple[bool, list]
        +is_date_before(date1, date2) bool
    }

    class AnalyticsEngine {
        +get_dashboard_kpis() dict
        +get_sales_trends() DataFrame
        +get_low_stock_alerts() DataFrame
        +get_expiring_soon_alerts() DataFrame
    }

    class ChartConfig {
        +plot_category_distribution(df: DataFrame) Figure
        +plot_monthly_sales(df: DataFrame) Figure
        +plot_stock_levels_bar(df: DataFrame) Figure
    }

    FileHandler ..> MedicineCSV : manages
    FileHandler ..> SaleRecordCSV : manages
    FileHandler ..> SupplierCSV : manages
    AuthManager ..> UserCSV : manages
    AnalyticsEngine ..> FileHandler : reads from
    ChartConfig ..> AnalyticsEngine : visualizes data of
    ValidationEngine ..> FileHandler : checks duplicates in
```

### 📝 PPT Slide Notes
- **Title**: Class Diagram: Logical Component and Data Model Layout
- **Architectural Separation**:
  - **Data Models**: Represent the tabular columns stored in CSV/Excel sheets (`MedicineCSV`, `SaleRecordCSV`, `SupplierCSV`, `UserCSV`).
  - **Utility Managers**: `FileHandler` coordinates Pandas-based CSV serialization. `AuthManager` handles password hashing and session validations.
  - **Analytical Controllers**: `AnalyticsEngine` filters datasets to compute trends and KPIs. `ChartConfig` generates Plotly visualizations.

---

## 4. Component Diagram

The Component Diagram displays the high-level physical layout of the application. It highlights dependencies between UI elements, underlying utility layers, brand assets, and CSV files.

### Mermaid Diagram

```mermaid
graph TB
    subgraph UI_Layer ["🎨 User Interface Layer (Streamlit Pages)"]
        App["app.py (Main Router / Auth Portal)"]
        Dashboard["Dashboard.py (KPIs & Metrics)"]
        ViewMeds["View_Medicines.py (Inventory Directory & CRUD)"]
        AddMed["Add_Medicine.py (Medicine Registration)"]
        UpdateStock["Update_Stock.py (Stock Adjustments)"]
        Sales["Sales.py (Invoicing & Checkout)"]
        Expiry["Expiry_Tracker.py (Compliance Audits)"]
        Reports["Reports.py (Excel/CSV Export Hub)"]
        Settings["Settings.py (DB Admin & Supplier Panel)"]
    end

    subgraph Business_Logic ["⚙️ Utilities / Business Logic Layer"]
        auth["auth.py (SHA-256 Auth Controller)"]
        validations["validations.py (Form Validations)"]
        analytics["analytics.py (KPI Math Calculators)"]
        charts["charts.py (Plotly Charts Engine)"]
        helper["helper.py (Theme Switcher & Notification Checker)"]
        file_handler["file_handler.py (File Serialization Handler)"]
    end

    subgraph Data_Layer ["💾 Database Layer (Flat-Files)"]
        medicines["medicines.csv"]
        sales_data["sales.csv"]
        suppliers["suppliers.csv"]
        users["users.csv / users.xlsx"]
    end

    subgraph Assets_Layer ["💅 Assets Layer"]
        styles["styles.css (Tailored CSS Rules)"]
        logo["logo.png (Brand Medical Icon)"]
    end

    %% UI to Business Logic relations
    App --> auth
    App --> helper
    Dashboard --> analytics
    Dashboard --> charts
    ViewMeds --> file_handler
    AddMed --> validations
    AddMed --> file_handler
    UpdateStock --> file_handler
    Sales --> file_handler
    Sales --> validations
    Expiry --> file_handler
    Reports --> file_handler
    Settings --> file_handler
    
    %% UI to assets
    App --> styles
    App --> logo

    %% Business Logic to Data Layer
    file_handler --> medicines
    file_handler --> sales_data
    file_handler --> suppliers
    auth --> users

    classDef ui fill:#e0f2fe,stroke:#0284c7,stroke-width:1.5px,color:#0369a1;
    classDef logic fill:#ecfdf5,stroke:#059669,stroke-width:1.5px,color:#047857;
    classDef db fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#b45309;
    classDef asset fill:#faf5ff,stroke:#9333ea,stroke-width:1.5px,color:#7e22ce;

    class App,Dashboard,ViewMeds,AddMed,UpdateStock,Sales,Expiry,Reports,Settings ui;
    class auth,validations,analytics,charts,helper,file_handler logic;
    class medicines,sales_data,suppliers,users db;
    class styles,logo asset;
```

### 📝 PPT Slide Notes
- **Title**: Component Diagram: Application Layers and Dependencies
- **Layer Details**:
  - **UI Layer**: Streamlit pages serving as interactive panels. `app.py` acts as the entrypoint and routing kernel.
  - **Business Logic**: Standalone reusable Python modules dealing with system state, charts, calculations, and inputs.
  - **Data Storage**: A secure sub-folder holding static files (`.csv`, `.xlsx`).
  - **Assets**: CSS stylesheet containing custom theme adjustments, fonts, card layouts, and branding graphics.

---

## 5. Sequence Diagram (Adding a New Medicine)

This Sequence Diagram depicts step-by-step object interactions during the medicine registration workflow, highlighting validation checks, ID checks, file inputs, and UI notifications.

### Mermaid Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Pharmacist as 👤 Pharmacist / Admin
    participant UI as Add_Medicine.py (Form UI)
    participant VAL as validations.py (Validation Engine)
    participant FH as file_handler.py (File Handler)
    participant CSV as medicines.csv (Database File)

    Pharmacist->>UI: Fills Medicine Details & Clicks 'Add Medicine'
    activate UI
    UI->>VAL: validate_medicine_fields(form_data)
    activate VAL
    
    VAL->>FH: load_medicines()
    activate FH
    FH->>VAL: Return Current Medicine DataFrame
    deactivate FH
    
    Note over VAL: Validates ID Unique, Purchase Date < Expiry Date,<br>Positive Price, and Non-empty fields.
    
    alt Validation Fails
        VAL-->>UI: Return Error Messages (e.g. "Duplicate ID", "Invalid Date")
        UI-->>Pharmacist: Display Error Notification Alert
    else Validation Succeeds
        VAL-->>UI: Return True (Validation OK)
        deactivate VAL
        
        UI->>FH: save_new_medicine(form_data)
        activate FH
        FH->>FH: Read CSV -> Append New Record -> Save DataFrame
        FH->>CSV: Write updated CSV payload
        activate CSV
        CSV-->>FH: Write Complete (File I/O Success)
        deactivate CSV
        FH-->>UI: Return Success Confirmation
        deactivate FH
        
        UI-->>Pharmacist: Show Success Toast ("Medicine Added Successfully") & Clear Fields
    end
    deactivate UI
```

### 📝 PPT Slide Notes
- **Title**: Sequence Diagram: Medicine Registration and Validation Flow
- **Execution Flow**:
  1. **User Action**: The pharmacist inputs data and submits the register form.
  2. **Validation Stage**: The UI delegates verification to `validations.py` which loads current records via `file_handler.py` to prevent duplicate IDs.
  3. **Alternative Routes**:
     - *Validation Failure*: Displays appropriate inline toast/alert messages and cancels the write action.
     - *Validation Success*: Appends the object record to the DataFrame and commits it to `medicines.csv` on-disk.
  4. **Feedback loop**: The UI updates, showing a confirmation banner, and resets input components.

---

## 6. Deployment Diagram

This Deployment Diagram illustrates the runtime environment, detailing the local client-server execution model.

### Mermaid Diagram

```mermaid
graph TB
    subgraph Client_Node ["🖥️ Client Node (User's Machine)"]
        Browser["🌐 Web Browser<br>(Chrome, Edge, Firefox)"]
        BrowserUI["React-based UI Client<br>(HTML/CSS/JS DOM)"]
        Browser --> BrowserUI
    end

    subgraph Server_Node ["🐍 Python Application Server (Localhost)"]
        Streamlit["⚙️ Streamlit Web Server Daemon<br>(Runs on Port 8501)"]
        AppRuntime["🚀 MediFlow App Execution Runtime<br>(Python 3.8+)"]
        Modules["📂 utils/ Packages<br>(file_handler, auth, analytics)"]
        
        Streamlit --> AppRuntime
        AppRuntime --> Modules
    end

    subgraph Storage_Node ["💾 Storage Device (Local File System)"]
        CSVFiles["📁 data/ Directory<br>(medicines.csv, sales.csv, suppliers.csv)"]
    end

    %% Communications
    BrowserUI <-->|HTTP / WebSockets<br>Port 8501| Streamlit
    Modules <-->|Local OS File System I/O<br>(Pandas read/write APIs)| CSVFiles

    classDef client fill:#f0f9ff,stroke:#0369a1,stroke-width:2px,color:#0369a1;
    classDef server fill:#f0fdf4,stroke:#15803d,stroke-width:2px,color:#15803d;
    classDef storage fill:#fff7ed,stroke:#c2410c,stroke-width:2px,color:#c2410c;

    class Client_Node,Browser,BrowserUI client;
    class Server_Node,Streamlit,AppRuntime,Modules server;
    class Storage_Node,CSVFiles storage;
```

### 📝 PPT Slide Notes
- **Title**: Deployment Diagram: Localhost Client-Server Execution Architecture
- **Hardware/Node Details**:
  - **Client Machine**: The terminal user operates any modern web browser accessing the local port.
  - **Application Server (Localhost)**: A Python virtual environment running Streamlit. It compiles Python scripts into a reactive web structure rendered dynamically on the browser.
  - **Storage Device**: Represents the local disk where files under `/data` are accessed by Pandas inside the application loop.
- **Protocols**: Websockets (WS) and HTTP protocol (Port 8501) are used for server-client sync, and direct OS storage operations (Local File System I/O) are used for database operations.

---

## 🖥️ How to Convert Diagrams and Text into a PowerPoint Presentation

You can use the following methods to convert the content in this file into PPT slides for your mini-project presentation.

### Method 1: Exporting Mermaid Diagrams as Images (Recommended & Easiest)
You can convert these Mermaid diagrams to high-quality PNG or SVG images and insert them directly into standard PowerPoint slides:

1. **Open the Mermaid Live Editor**:
   - Go to [mermaid.live](https://mermaid.live/) in your web browser.
2. **Copy and Paste the Diagram Code**:
   - Copy any of the Mermaid code blocks from above (only the code inside the ` ```mermaid ` indicators).
   - Paste it into the "Code" panel on the left side of the Mermaid Live Editor page.
3. **Download the Image**:
   - The right side will render the live diagram.
   - Click the **Actions** tab on the bottom-left panel.
   - Choose **PNG** or **SVG** (vector format, ideal for resizing without pixelation).
   - Save the file to your computer.
4. **Insert into PowerPoint**:
   - In PowerPoint, create a new slide with a layout suited for diagrams (e.g., "Title and Content" or a blank slide).
   - Go to **Insert > Pictures > This Device** and select the downloaded diagram.
   - Copy and paste the corresponding **PPT Slide Notes** (provided above) into the PowerPoint presentation notes panel to help you during your viva-voce!

---

### Method 2: Convert directly to PPT using Marp (VS Code Extension)
If you want to compile this Markdown file directly into a styled, professional PowerPoint presentation (`.pptx` file):

1. **Install VS Code Extension**:
   - Search for and install the extension **Marp for VS Code** in the Extensions Marketplace (Ctrl+Shift+X).
2. **Enable HTML and Preview**:
   - Open this `uml_diagrams.md` file.
   - Click the Marp icon at the top of the editor or open the VS Code Command Palette (`Ctrl+Shift+P`) and type `Marp: Toggle Marp feature for current Markdown`.
3. **Format as Slides (Optional Adjustment)**:
   - Marp uses `---` dividers to split slides. We have already structured this file logically.
4. **Export to PPTX**:
   - Click the Marp icon on the VS Code editor menu (or press `Ctrl+Shift+P` -> type `Marp: Export Slide Deck...`).
   - Choose the file format: **PowerPoint document (*.pptx)**.
   - Click **Save**.
   - Your slides will be generated instantly, with text formatting and images compiled automatically!
