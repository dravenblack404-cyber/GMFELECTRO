import streamlit as st
from collections import namedtuple
from ortools.sat.python import cp_model
import plotly.graph_objects as go
import time

# Style
st.set_page_config(
    page_title="GMF Electroplating Optimizer", 
    layout="wide", 
    page_icon="assets/icon.png"
)

# CSS Inject
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# CSS code
# Gantikan seluruh blok st.markdown("""<style>...""") kamu dengan yang ini:
st.markdown("""
<style>
    /* ================================================================================
    TEMA DASAR (LIGHT THEME)
    ================================================================================
    */

    :root {
        --primary-color-dark: #0062E6;
        --primary-color-light: #007FFF;
        --light-text-color: #FFFFFF;
        
        /* BARU: Variabel warna yang bisa beradaptasi */
        --app-bg-start: #F0F2F6;
        --app-bg-end: #FFFFFF;
        --header-bg-start: #E9ECEF;
        --header-bg-end: #F8F9FA;
        --header-text-primary: #31333F;
        --header-text-secondary: #6c757d;
        --sidebar-bg: #F0F2F6;
        --card-bg: rgba(255, 255, 255, 0.8);
        --border-color: #E6E6E6;
    }

    /* ================================================================================
    TEMA GELAP (DARK THEME) - Didefinisikan di dalam media query
    ================================================================================
    */

    @media (prefers-color-scheme: dark) {
        :root {
            /* BARU: Ganti nilai variabel untuk dark mode */
            --app-bg-start: #0F1116; /* Abu-abu sangat gelap */
            --app-bg-end: #181A20;   /* Sedikit lebih terang */
            --header-bg-start: #2A2C34;
            --header-bg-end: #22242A;
            --header-text-primary: #FFFFFF; /* Teks jadi putih */
            --header-text-secondary: #A0A0A0; /* Abu-abu terang untuk subjudul */
            --sidebar-bg: #1A1C22;
            --card-bg: rgba(42, 44, 52, 0.8); /* Warna kartu jadi gelap transparan */
            --border-color: #3E3F42; /* Border juga jadi lebih gelap */
        }
    }

    /* ================================================================================
    ATURAN GAYA (Tidak perlu diubah, karena sudah menggunakan variabel)
    ================================================================================
    */

    .stApp {
        background: linear-gradient(to bottom, var(--app-bg-start) 0%, var(--app-bg-end) 30%);
    }
    
    .custom-header {
        background: linear-gradient(135deg, var(--header-bg-start) 0%, var(--header-bg-end) 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: var(--header-text-primary);
        text-align: center;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); 
    }
    .custom-header h1 {
        color: var(--header-text-primary);
        font-size: 2.5em;
        margin-bottom: 0.2em;
    }
    .custom-header p {
        color: var(--header-text-secondary);
        font-size: 1.1em;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
    }
    [data-testid="stSidebar"] h2 {
        color: var(--primary-color-dark);
    }
    
    .stButton>button {
        border: none;
        border-radius: 10px;
        color: var(--light-text-color);
        background: linear-gradient(135deg, var(--primary-color-dark) 0%, var(--primary-color-light) 100%);
        padding: 12px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(0, 127, 255, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, var(--primary-color-light) 0%, var(--primary-color-dark) 100%);
        box-shadow: 0 6px 20px rgba(0, 127, 255, 0.3);
        transform: translateY(-2px);
    }

    .st-emotion-cache-134p638 {
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* DIUBAH: Menggunakan variabel --card-bg */
    .st-emotion-cache-1fplaw { /* Selector untuk st.container(border=True) */
        background-color: var(--card-bg);
        backdrop-filter: blur(5px);
    }
</style>
""", unsafe_allow_html=True)

# PARAMETER
PackedItem = namedtuple('PackedItem', ['name', 'position', 'dimension'])

# Header
st.markdown("""
<div class="custom-header">
    <h1>📦 GMF Electroplating Tank Optimizer</h1>
    <p>Smart Tools for Optimizing Electroplating Tank Capacity and Efficiency</p>
</div>
""", unsafe_allow_html=True)

st.markdown("Selamat datang di **Electroplating Tank Optimizer**. Aplikasi ini dirancang untuk membantu Anda menemukan konfigurasi pemuatan part yang paling efisien di dalam tangki elektroplating.")
st.markdown("For Further Information and Update Please Contact Harist (+6282288659174)")
# --- UI Sidebar ---

st.sidebar.image("assets/logo.png", use_container_width=True) # <-- TAMBAHKAN BARIS INI

st.sidebar.markdown("## ⚙️ Input Parameters")
st.sidebar.markdown("---")

st.sidebar.subheader("Anode:Cathode Ratio")
anode_area_m2 = st.sidebar.number_input("Tank's Total Cathode Area (m²)", min_value=0.1, value=6.4, step=0.1, help="Total luas permukaan anoda yang terpasang di dalam tangki.")
anode_area_cm2 = anode_area_m2 * 10000

min_ratio_str = st.sidebar.text_input("Minimum Ratio (Anode:Cathode)", value="1:5")
max_ratio_str = st.sidebar.text_input("Maximum Ratio (Anode:Cathode)", value="10:1")

try:
    min_ratio_val = float(min_ratio_str.split(':')[0]) / float(min_ratio_str.split(':')[1])
    max_ratio_val = float(max_ratio_str.split(':')[0]) / float(max_ratio_str.split(':')[1])
except:
    st.sidebar.error("Invalid ratio format. Use format like '1:5'.")
    st.stop()

# Anode : Cathode
max_cathode_area = anode_area_cm2 / min_ratio_val
min_cathode_area = anode_area_cm2 / max_ratio_val

st.sidebar.info(f"Target Total Part (Anode) Area per Batch: **{min_cathode_area:,.0f} - {max_cathode_area:,.0f} cm²**")

st.sidebar.markdown("---")
st.sidebar.subheader("Tank & Rack Geometry")
max_racks = st.sidebar.slider("Maximum Racks per Batch", min_value=1, max_value=5, value=3, step=1)
RACK_CLEARANCE = st.sidebar.number_input("Clearance Between Racks (cm)", min_value=0, value=10, step=1)
WALL_CLEARANCE = st.sidebar.number_input("Wall Clearance (cm)", min_value=0, value=10, step=1)
PART_CLEARANCE = st.sidebar.number_input("Part Clearance (cm)", min_value=0, value=5, step=1)
bath_length = st.sidebar.number_input("Tank Length (X) (cm)", min_value=10, value=100, step=10)
bath_height = st.sidebar.number_input("Tank Height (Y) (cm)", min_value=10, value=200, step=10)
bath_width  = st.sidebar.number_input("Tank Width (Z) (cm)", min_value=10, value=300, step=10)
electroplating_bath_dims = {'name': 'Electroplating-Bath', 'width': bath_width, 'height': bath_height, 'length': bath_length}

st.sidebar.markdown("---")
st.sidebar.subheader("Part Definitions")
num_part_types = st.sidebar.number_input("Number of Part Types", min_value=1, max_value=10, value=3)
part_definitions = []
for i in range(num_part_types):
    with st.sidebar.expander(f"Part Type {i+1}"):
        name = st.text_input(f"Part Name {i+1}", value=f"Part-{i+1}")
        # Dimensi untuk packing geometri
        l = st.number_input(f"Length (dimensi box) (cm)", min_value=1, value=40, step=1, key=f"l{i}")
        h = st.number_input(f"Height (dimensi box) (cm)", min_value=1, value=30, step=1, key=f"h{i}")
        w = st.number_input(f"Width (dimensi box) (cm)", min_value=1, value=40, step=1, key=f"w{i}")
        sa = st.number_input(f"Surface Area (cm²)", min_value=1, value=4000, step=100, key=f"sa{i}", help="Ini adalah luas permukaan katoda untuk satu part.")
        qty = st.number_input(f"Quantity", min_value=1, value=10, step=1, key=f"q{i}")
        part_definitions.append({'name': name, 'dims': (l, h, w), 'surface_area': sa, 'quantity': qty})


# --- LOGIKA BACKEND & FUNGSI (Tidak diubah) ---
def get_rotations(dims):
    w, h, d = dims
    rotations = {(w, h, d), (w, d, h), (h, w, d), (h, d, w), (d, w, h), (d, h, w)}
    return list(rotations)

def visualize_with_plotly(packed_items, container_dims, container_name):
    data = []
    def get_cuboid_vertices(position, dimension):
        x, y, z = position
        w, h, d = dimension
        return [(x, y, z), (x + w, y, z), (x + w, y + h, z), (x, y + h, z), (x, y, z + d), (x + w, y, z + d), (x + w, y + h, z + d), (x, y + h, z + d)]
    for item in packed_items:
        verts = get_cuboid_vertices(item.position, item.dimension)
        data.append(go.Mesh3d(x=[v[0] for v in verts], y=[v[1] for v in verts], z=[v[2] for v in verts], i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 2, 5, 1, 2, 5, 6], opacity=0.8, name=item.name, hoverinfo='name'))
    container_verts = get_cuboid_vertices((0,0,0), (container_dims['length'], container_dims['height'], container_dims['width']))
    cx, cy, cz = zip(*container_verts)
    data.append(go.Scatter3d(x=cx, y=cy, z=cz, mode='lines', line=dict(color='black', width=3), name='Container'))
    layout = go.Layout(title=f"<b>Interactive 3D View: {container_name}</b>", scene=dict(xaxis=dict(title='Length (X)'), yaxis=dict(title='Height (Y)'), zaxis=dict(title='Width (Z)')), margin=dict(l=0, r=0, b=0, t=40))
    fig = go.Figure(data=data, layout=layout)
    return fig

def find_optimal_layout_for_one_bath(parts_available, bath, num_racks, min_area, max_area, time_limit=30.0):
    # (Fungsi solver sama persis, tidak perlu diubah)
    model = cp_model.CpModel()
    num_parts = len(parts_available)
    is_packed = [[model.NewBoolVar(f'is_packed_{p}_r{r}') for r in range(num_racks)] for p in range(num_parts)]
    x_vars = [model.NewIntVar(0, bath['length'], f'x_{p}') for p in range(num_parts)]
    y_vars = [model.NewIntVar(0, bath['height'], f'y_{p}') for p in range(num_parts)]
    dx_vars = [model.NewIntVar(0, bath['length'], f'dx_{p}') for p in range(num_parts)]
    dy_vars = [model.NewIntVar(0, bath['height'], f'dy_{p}') for p in range(num_parts)]
    dz_vars = [model.NewIntVar(0, bath['width'], f'dz_{p}') for p in range(num_parts)]
    max_depth_per_rack = [model.NewIntVar(0, bath['width'], f'max_depth_r{r}') for r in range(num_racks)]
    padded_dx_vars = [model.NewIntVar(0, bath['length'], f'padded_dx_{p}') for p in range(num_parts)]
    padded_dy_vars = [model.NewIntVar(0, bath['height'], f'padded_dy_{p}') for p in range(num_parts)]
    end_x_vars = [model.NewIntVar(0, bath['length'], f'end_x_{p}') for p in range(num_parts)]
    end_y_vars = [model.NewIntVar(0, bath['height'], f'end_y_{p}') for p in range(num_parts)]
    
    part_volumes = [p['volume'] for p in parts_available]
    part_surface_areas = [p['surface_area'] for p in parts_available]

    total_packed_area = sum(is_packed[p][r] * part_surface_areas[p] for p in range(num_parts) for r in range(num_racks))
    model.Add(total_packed_area >= int(min_area))
    model.Add(total_packed_area <= int(max_area))
    
    for p in range(num_parts):
        is_part_actually_packed = model.NewBoolVar(f'is_actually_packed_{p}')
        model.Add(sum(is_packed[p]) == is_part_actually_packed)
        rotations = parts_available[p]['rotations']
        l_p_r = [model.NewBoolVar(f'l_{p}_{r}') for r in range(len(rotations))]
        model.Add(sum(l_p_r) == is_part_actually_packed)
        for r, rot in enumerate(rotations):
            model.Add(dx_vars[p] == rot[0]).OnlyEnforceIf(l_p_r[r])
            model.Add(dy_vars[p] == rot[1]).OnlyEnforceIf(l_p_r[r])
            model.Add(dz_vars[p] == rot[2]).OnlyEnforceIf(l_p_r[r])
        model.Add(padded_dx_vars[p] == dx_vars[p] + PART_CLEARANCE).OnlyEnforceIf(is_part_actually_packed)
        model.Add(padded_dy_vars[p] == dy_vars[p] + PART_CLEARANCE).OnlyEnforceIf(is_part_actually_packed)
        model.Add(padded_dx_vars[p] == 0).OnlyEnforceIf(is_part_actually_packed.Not())
        model.Add(padded_dy_vars[p] == 0).OnlyEnforceIf(is_part_actually_packed.Not())
        model.Add(end_x_vars[p] == x_vars[p] + padded_dx_vars[p])
        model.Add(end_y_vars[p] == y_vars[p] + padded_dy_vars[p])
        model.Add(x_vars[p] >= WALL_CLEARANCE).OnlyEnforceIf(is_part_actually_packed)
        model.Add(y_vars[p] >= WALL_CLEARANCE).OnlyEnforceIf(is_part_actually_packed)
        model.Add(end_x_vars[p] <= bath['length'] - WALL_CLEARANCE).OnlyEnforceIf(is_part_actually_packed)
        model.Add(end_y_vars[p] <= bath['height'] - WALL_CLEARANCE).OnlyEnforceIf(is_part_actually_packed)

    for r in range(num_racks):
        x_intervals_r = [model.NewOptionalIntervalVar(x_vars[p], padded_dx_vars[p], end_x_vars[p], is_packed[p][r], f'x_int_p{p}_r{r}') for p in range(num_parts)]
        y_intervals_r = [model.NewOptionalIntervalVar(y_vars[p], padded_dy_vars[p], end_y_vars[p], is_packed[p][r], f'y_int_p{p}_r{r}') for p in range(num_parts)]
        model.AddNoOverlap2D(x_intervals_r, y_intervals_r)
        is_rack_used = model.NewBoolVar(f'is_rack_used_{r}')
        model.Add(sum(is_packed[p][r] for p in range(num_parts)) > 0).OnlyEnforceIf(is_rack_used)
        model.Add(sum(is_packed[p][r] for p in range(num_parts)) == 0).OnlyEnforceIf(is_rack_used.Not())
        model.Add(max_depth_per_rack[r] == 0).OnlyEnforceIf(is_rack_used.Not())
        for p in range(num_parts):
            model.Add(dz_vars[p] <= max_depth_per_rack[r]).OnlyEnforceIf(is_packed[p][r])

    num_racks_used_expr = sum(is_rack_used for r in range(num_racks))
    num_gaps = model.NewIntVar(0, num_racks, 'num_gaps')
    model.Add(num_gaps >= num_racks_used_expr - 1)
    total_width_used = sum(max_depth_per_rack) + num_gaps * RACK_CLEARANCE
    model.Add(total_width_used <= bath['width'] - (2 * WALL_CLEARANCE))
    model.Maximize(sum(is_packed[p][r] * part_volumes[p] for p in range(num_parts) for r in range(num_racks)))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)
    
    packed_racks_result, remaining_parts_result = [], []
    packed_indices = set()
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        rack_depths = [solver.Value(md) for md in max_depth_per_rack]
        current_z = WALL_CLEARANCE
        for r in range(num_racks):
            items_on_this_rack = []
            for p in range(num_parts):
                if solver.BooleanValue(is_packed[p][r]):
                    packed_indices.add(p)
                    dim_dx, dim_dy, dim_dz = solver.Value(dx_vars[p]), solver.Value(dy_vars[p]), solver.Value(dz_vars[p])
                    pos_x, pos_y = solver.Value(x_vars[p]), solver.Value(y_vars[p])
                    items_on_this_rack.append(PackedItem(name=parts_available[p]['name'], position=(pos_x, pos_y, current_z), dimension=(dim_dx, dim_dy, dim_dz)))
            if items_on_this_rack:
                packed_racks_result.append(items_on_this_rack)
                current_z += rack_depths[r] + RACK_CLEARANCE
    for p in range(num_parts):
        if p not in packed_indices:
            remaining_parts_result.append(parts_available[p])
    return packed_racks_result, remaining_parts_result

# Button
if st.button("🚀 Find Optimal Packing", type="primary"):
    all_parts = []
    for part_type in part_definitions:
        dims, qty = part_type['dims'], part_type['quantity']
        l, h, w = dims
        volume = l * h * w
        surface_area = part_type['surface_area'] 
        for i in range(qty):
            all_parts.append({
                'name': f"{part_type['name']}-{i+1}", 
                'rotations': get_rotations(dims), 
                'volume': volume, 
                'dims': dims,
                'surface_area': surface_area
            })

    final_batches = []
    parts_to_pack = all_parts[:]
    batch_num = 1
    
    with st.spinner(f'🚀 Optimizing... This might take a few moments.'):
        progress_bar = st.progress(0, text="Initializing...")
        
        while parts_to_pack:
            num_remaining = len(parts_to_pack)
            progress_text = f"Optimizing Batch #{batch_num} for {num_remaining} remaining parts..."
            progress_bar.text(progress_text)
            
            packed_racks, remaining_parts = find_optimal_layout_for_one_bath(parts_to_pack, electroplating_bath_dims, max_racks, min_cathode_area, max_cathode_area)
            
            if not packed_racks:
                st.warning(f"Solver couldn't fit the {len(parts_to_pack)} remaining parts into a new batch while satisfying the A:C ratio. These parts are left over.")
                break
                
            final_batches.append(packed_racks)
            parts_to_pack = remaining_parts
            progress_done = (len(all_parts) - len(parts_to_pack)) / len(all_parts)
            progress_bar.progress(progress_done, text=progress_text)
            batch_num += 1
        
        progress_bar.progress(1.0, text="Optimization Complete!")
        time.sleep(1) # Beri waktu sejenak untuk user membaca pesan selesai
        progress_bar.empty()

    st.success("✅ Optimization complete!")

    if not final_batches:
        st.error("No parts could be packed. Please check your dimensions, clearances, and A:C ratio constraints.")
    else:
        st.markdown("---")
        st.markdown("## 📊 Final Packing Results")
        
        for i, racks_in_batch in enumerate(final_batches, start=1):
            # Menggunakan st.container sebagai kartu hasil
            with st.container(border=True):
                st.subheader(f"Batch {i} (Utilizing {len(racks_in_batch)} of {max_racks} max Racks)")
                
                all_items_in_batch = [item for rack in racks_in_batch for item in rack]
                
                # Menghitung total surface area untuk batch ini dengan benar
                packed_names_in_batch = {item.name for item in all_items_in_batch}
                total_batch_surface_area = sum(p['surface_area'] for p in all_parts if p['name'] in packed_names_in_batch)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Total Part Surface Area (Anode)", value=f"{total_batch_surface_area:,.0f} cm²")
                with col2:
                    st.info(f"Target Range: {min_cathode_area:,.0f} - {max_cathode_area:,.0f} cm²")
                
                st.plotly_chart(visualize_with_plotly(all_items_in_batch, electroplating_bath_dims, f"Batch {i}"), use_container_width=True)
                
                with st.expander("Show Part Details for this Batch"):
                    # Membuat tabel detail yang lebih rapi
                    details_data = []
                    for item in sorted(all_items_in_batch, key=lambda x: x.name):
                        details_data.append({
                            "Part Name": item.name,
                            "Position (X, Y, Z)": f"({item.position[0]}, {item.position[1]}, {item.position[2]})",
                            "Dimensions (L, H, W)": f"{item.dimension[0]} x {item.dimension[1]} x {item.dimension[2]}"
                        })

                    st.dataframe(details_data, use_container_width=True)



