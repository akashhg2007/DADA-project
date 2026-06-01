# UrbanPulse - Bangalore Traffic & AQI Correlation Insights

This document outlines the top 3 critical analytical insights derived from the unified Traffic, AQI, and Weather master dataset.

## Key Insights

### 1. Strong Positive Coupling Between Traffic Congestion & Localized AQI
Analysis of localized monitoring stations shows a pronounced correlation between vehicle congestion levels and AQI readings.
*   **Highest Station Correlation**: **Silk Board** exhibited the strongest congestion-to-AQI relationship with a **Pearson r of 0.726**. This is driven by high vehicle idle times and emissions build-up at major junctions.
*   **Station Breakdown**:
    - **BTM Layout**: Pearson $r$ = `0.669`
    - **Hebbal**: Pearson $r$ = `0.664`
    - **Peenya**: Pearson $r$ = `0.711`
    - **Silk Board**: Pearson $r$ = `0.726`
    - **Whitefield**: Pearson $r$ = `0.631`

### 2. Vehicle Speed as a Leading Indicator of Fine Particulate Matter (PM2.5)
A strong negative correlation exists between average travel speed and PM2.5 concentrations ($r$ = `-0.582`).
*   **The Dynamics**: As traffic slows down and average speeds drop, PM2.5 concentrations surge. This is visible in scatter plots comparing slow crawl hours against free-flowing intervals.
*   **Weekend vs. Weekday Split**: Weekend patterns show lower overall base congestion spikes, allowing speeds to remain higher and PM2.5 levels to settle down compared to intense weekday work commutes.

### 3. AQI Primary Drivers & Environmental Interactions
The correlation matrix reveals that AQI is heavily driven by **PM2.5** and **PM10** (Pearson $r$ with AQI = `0.910`).
*   **Weather Dynamics**: Wind speed acts as a dispersion factor, showing a negative correlation with AQI. Higher wind speeds help dissipate PM2.5 and PM10 particles, leading to cleaner local air index readings.
*   **Humidity Effect**: Higher humidity correlates with elevated AQI levels, as high moisture binds particulate matter, preventing dispersion and leading to localized pollution layering.
