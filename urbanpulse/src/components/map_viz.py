import streamlit as st
import folium
from streamlit_folium import st_folium
from branca.element import Element
import pandas as pd
import geopandas as gpd

def get_congestion_color(congestion):
    """Calculates a smooth mathematical hex gradient from #10B981 (success/green) to #EF4444 (danger/red)"""
    try:
        c = max(0.0, min(100.0, float(congestion)))
    except (ValueError, TypeError):
        c = 0.0
    t = c / 100.0
    
    # Success Color (#10B981): RGB(16, 185, 129)
    # Danger Color (#EF4444): RGB(239, 68, 68)
    r = int(16 + t * (239 - 16))
    g = int(185 + t * (68 - 185))
    b = int(129 + t * (68 - 129))
    
    return f"#{r:02x}{g:02x}{b:02x}"

def render_aqi_map(ward_gdf, traffic_df):
    """
    Renders an interactive glassmorphic spatial map showing Bangalore ward-level AQI 
    choropleths and live traffic junctions overlay markers.
    
    Parameters:
    ward_gdf (geopandas.GeoDataFrame): GeoDataFrame containing BBMP ward polygons and assigned_aqi
    traffic_df (pandas.DataFrame): DataFrame containing TomTom junction logs (latitude, longitude, congestion_level, etc.)
    """
    # 1. Compute dynamic map center
    if not ward_gdf.empty:
        # Use center centroid of all boundaries
        if hasattr(ward_gdf.geometry, 'union_all'):
            centroid = ward_gdf.geometry.union_all().centroid
        else:
            centroid = ward_gdf.geometry.unary_union.centroid
        map_center = [centroid.y, centroid.x]
    else:
        map_center = [12.9716, 77.5946] # default center on Bangalore city
        
    # 2. Initialize Folium Map with CartoDB dark_matter aesthetic
    m = folium.Map(
        location=map_center,
        zoom_start=11.5,
        tiles="CartoDB dark_matter",
        control_scale=True
    )
    
    # 3. Add Choropleth layer for wards
    if not ward_gdf.empty and "assigned_aqi" in ward_gdf.columns:
        # Ensure WARD_NO is present as string column
        if "WARD_NO" not in ward_gdf.columns:
            ward_gdf["WARD_NO"] = ward_gdf.index.astype(str)
        else:
            ward_gdf["WARD_NO"] = ward_gdf["WARD_NO"].astype(str)
            
        choropleth = folium.Choropleth(
            geo_data=ward_gdf,
            name="BBMP Ward AQI Choropleth",
            data=ward_gdf,
            columns=["WARD_NO", "assigned_aqi"],
            key_on="feature.properties.WARD_NO",
            fill_color="YlOrRd",
            fill_opacity=0.7,
            line_opacity=0.3,
            line_color="#1E293B",
            line_weight=0.5,
            highlight=True,
            legend_name="Interpolated Spatial AQI Index"
        ).add_to(m)
        
        # Add rich hover tooltips to the choropleth layer
        tooltip_fields = []
        tooltip_aliases = []
        
        for col, alias in [("WARD_NO", "Ward ID:"), ("WARD_NAME", "Ward Name:"), ("assigned_aqi", "Assigned AQI:"), ("assigned_station", "Closest Monitor:")]:
            if col in ward_gdf.columns:
                tooltip_fields.append(col)
                tooltip_aliases.append(alias)
                
        if tooltip_fields:
            folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases,
                style=(
                    "background-color: #0F172A; "
                    "color: #F1F5F9; "
                    "font-family: 'Inter', sans-serif; "
                    "font-size: 12px; "
                    "padding: 8px 12px; "
                    "border: 1px solid rgba(255,255,255,0.1); "
                    "border-radius: 8px; "
                    "box-shadow: 0 4px 20px rgba(0,0,0,0.5);"
                ),
                localize=True
            ).add_to(choropleth.geojson)
            
    # 4. Add Custom Floating HTML Legend with Glass Class (positioned bottomright)
    legend_html = """
    <div style="
        position: fixed; 
        bottom: 30px; 
        right: 30px; 
        width: 160px; 
        z-index: 9999; 
        font-family: 'Inter', sans-serif;
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 0.8rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important;
    ">
        <div style="font-size: 0.75rem; text-transform: uppercase; color: #94A3B8; font-weight: 700; letter-spacing: 1px; margin-bottom: 0.5rem;">AQI Spectrum</div>
        <div style="display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.75rem; color: #E2E8F0;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 10px; height: 10px; background: #FFEDA0; border-radius: 2px; border: 0.5px solid rgba(0,0,0,0.2);"></div>
                <span>0 - 50 (Good)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 10px; height: 10px; background: #FEB24C; border-radius: 2px; border: 0.5px solid rgba(0,0,0,0.2);"></div>
                <span>51 - 100 (Moderate)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 10px; height: 10px; background: #FD8D3C; border-radius: 2px; border: 0.5px solid rgba(0,0,0,0.2);"></div>
                <span>101 - 150 (Poor)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 10px; height: 10px; background: #F03B20; border-radius: 2px; border: 0.5px solid rgba(0,0,0,0.2);"></div>
                <span>151 - 200 (Unhealthy)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 10px; height: 10px; background: #BD0026; border-radius: 2px; border: 0.5px solid rgba(0,0,0,0.2);"></div>
                <span>200+ (Severe)</span>
            </div>
        </div>
        <div style="margin-top: 0.6rem; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.4rem;">
            <div style="font-size: 0.65rem; text-transform: uppercase; color: #94A3B8; font-weight: 700; letter-spacing: 0.8px; margin-bottom: 0.2rem;">Traffic Nodes</div>
            <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.7rem; color: #94A3B8;">
                <span style="color:#10B981; font-weight:bold;">Flow</span>
                <div style="flex-grow: 1; height: 4px; background: linear-gradient(to right, #10B981, #EF4444); border-radius: 2px;"></div>
                <span style="color:#EF4444; font-weight:bold;">Jammed</span>
            </div>
        </div>
    </div>
    """
    m.get_root().html.add_child(Element(legend_html))
    
    # 5. Render Traffic Junction Circle Markers
    if not traffic_df.empty:
        required_cols = ["latitude", "longitude", "congestion_level", "junction_name"]
        if all(c in traffic_df.columns for c in required_cols):
            for _, row in traffic_df.iterrows():
                try:
                    lat = float(row["latitude"])
                    lon = float(row["longitude"])
                    cong = float(row["congestion_level"])
                except (ValueError, TypeError):
                    continue
                    
                # Skip invalid coords
                if pd.isna(lat) or pd.isna(lon):
                    continue
                    
                # Radius = congestion_level / 5
                marker_radius = max(3.0, cong / 5.0)
                
                # Get dynamic color gradient from #10B981 to #EF4444
                marker_color = get_congestion_color(cong)
                
                # Build stats popup HTML
                speed = row.get("avg_speed_kmph", "N/A")
                aqi_val = row.get("AQI", "N/A")
                if isinstance(aqi_val, float) or isinstance(aqi_val, int):
                    aqi_val = int(aqi_val)
                    
                popup_content = f"""
                <div style="
                    font-family: 'Inter', sans-serif; 
                    font-size: 11px; 
                    width: 170px; 
                    color: #F1F5F9; 
                    background: #0F172A; 
                    border-radius: 8px; 
                    padding: 8px;
                    line-height: 1.4;
                ">
                    <h4 style="margin: 0 0 5px 0; font-size: 12px; font-weight: 700; color: #4F46E5;">🚦 {row['junction_name']}</h4>
                    <div style="border-top: 1px solid rgba(255,255,255,0.1); margin-top: 4px; padding-top: 4px;">
                        <b>Congestion Index:</b> <span style="color: {marker_color}; font-weight: bold;">{int(cong)}%</span><br/>
                        <b>Travel Speed:</b> <span style="font-weight: 600;">{speed} km/h</span><br/>
                        <b>Ambient AQI Score:</b> <span style="font-weight: 600;">{aqi_val}</span>
                    </div>
                </div>
                """
                
                # Add marker to map
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=marker_radius,
                    color=marker_color,
                    fill=True,
                    fill_color=marker_color,
                    fill_opacity=0.75,
                    weight=1.5,
                    popup=folium.Popup(popup_content, max_width=200)
                ).add_to(m)
                
    # 6. streamlit-folium rendering wrapped inside glassmorphic containers
    with st.container():
        st.markdown('<div class="glass" style="padding:0.5rem !important;">', unsafe_allow_html=True)
        st_folium(m, height=500, returned_objects=[])
        st.markdown('</div>', unsafe_allow_html=True)
