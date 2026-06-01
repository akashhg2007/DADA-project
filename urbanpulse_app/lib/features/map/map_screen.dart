import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/glass_container.dart';
import '../dashboard/dashboard_provider.dart';
import '../../models/aqi_model.dart';

/// Map screen showing Bangalore wards colored by real-time AQI levels and
/// traffic junction circles, wrapped in a glassmorphic container with custom bottom sheets.
class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  List<_WardPolygon> _wards = [];
  bool _loadingGeo = true;

  @override
  void initState() {
    super.initState();
    _loadGeoJson();
  }

  Future<void> _loadGeoJson() async {
    try {
      final raw = await rootBundle.loadString('assets/bangalore_wards.geojson');
      final geoJson = json.decode(raw) as Map<String, dynamic>;
      final features = geoJson['features'] as List;

      final wards = <_WardPolygon>[];
      for (final f in features) {
        final props = f['properties'] as Map<String, dynamic>? ?? {};
        final name = props['WARD_NAME'] ?? props['name'] ?? 'Unknown';
        final geometry = f['geometry'] as Map<String, dynamic>;
        final type = geometry['type'] as String;

        List<List<dynamic>> rings = [];
        if (type == 'Polygon') {
          rings = (geometry['coordinates'] as List).cast<List<dynamic>>();
        } else if (type == 'MultiPolygon') {
          for (final poly in geometry['coordinates'] as List) {
            rings.addAll((poly as List).cast<List<dynamic>>());
          }
        }

        for (final ring in rings) {
          final points = ring.map<LatLng>((coord) {
            final c = coord as List;
            return LatLng((c[1] as num).toDouble(), (c[0] as num).toDouble());
          }).toList();
          if (points.length > 2) {
            wards.add(_WardPolygon(name: name.toString(), points: points));
          }
        }
      }
      if (mounted) {
        setState(() {
          _wards = wards;
          _loadingGeo = false;
        });
      }
    } catch (e) {
      debugPrint('GeoJSON load error: $e');
      if (mounted) setState(() => _loadingGeo = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final liveAqiAsync = ref.watch(liveAqiProvider);
    final trafficAsync = ref.watch(trafficJunctionsProvider);

    // Build real-time lookup mapping ward names to AQI readings
    final Map<String, AqiModel> aqiLookup = {};
    if (liveAqiAsync.hasValue) {
      for (final model in liveAqiAsync.value!) {
        aqiLookup[model.ward.toLowerCase().trim()] = model;
      }
    }

    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title Header
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Spatial AQI Map',
                      style: Theme.of(context).textTheme.headlineMedium),
                  const SizedBox(height: 4),
                  Text(
                    'Ward-level AQI heatmap with traffic junction overlays',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Map Box
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: GlassContainer(
                  padding: EdgeInsets.zero,
                  child: Stack(
                    children: [
                      FlutterMap(
                        options: MapOptions(
                          initialCenter: const LatLng(12.9716, 77.5946),
                          initialZoom: 11.2,
                          onTap: (_, point) => _handleMapTap(point, aqiLookup),
                        ),
                        children: [
                          // 1. CartoDB Dark Matter tile layer
                          TileLayer(
                            urlTemplate:
                                'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                            subdomains: const ['a', 'b', 'c', 'd'],
                            userAgentPackageName: 'com.urbanpulse.app',
                          ),

                          // 2. PolygonLayer: Wards colored dynamically by AQI
                          if (!_loadingGeo)
                            PolygonLayer(
                              polygons: _wards.map((w) {
                                final model = aqiLookup[w.name.toLowerCase().trim()];
                                final aqiVal = model?.aqi ?? 0.0;
                                final color = _aqiColor(aqiVal);

                                return Polygon(
                                  points: w.points,
                                  color: color.withOpacity(0.32),
                                  borderColor: color.withOpacity(0.65),
                                  borderStrokeWidth: 1.2,
                                  isFilled: true,
                                );
                              }).toList(),
                            ),

                          // 3. CircleLayer (Traffic Circle Markers)
                          trafficAsync.when(
                            loading: () => const CircleLayer(circles: []),
                            error: (_, __) => const CircleLayer(circles: []),
                            data: (junctions) => CircleLayer(
                              circles: junctions.map((j) {
                                final lat = (j['latitude'] as num).toDouble();
                                final lng = (j['longitude'] as num).toDouble();
                                final cong = (j['congestion_level'] as num).toDouble();
                                
                                // Radius is exactly congestion / 4
                                final radius = (cong / 4.0).clamp(3.0, 24.0);

                                return CircleMarker(
                                  point: LatLng(lat, lng),
                                  radius: radius,
                                  color: _congColor(cong).withOpacity(0.75),
                                  borderColor: Colors.white24,
                                  borderStrokeWidth: 0.8,
                                );
                              }).toList(),
                            ),
                          ),
                        ],
                      ),

                      // Loading indicator overlay
                      if (_loadingGeo)
                        const Center(
                          child: CircularProgressIndicator(
                            color: AppColors.primary,
                            strokeWidth: 2,
                          ),
                        ),

                      // 4. Custom Legend Widget in bottomRight
                      Positioned(
                        bottom: 12,
                        right: 12,
                        child: GlassContainer(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text(
                                'AQI Scale',
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              const SizedBox(height: 6),
                              _legendRow(const Color(0xFF10B981), 'Good (0-50)'),
                              _legendRow(const Color(0xFFF59E0B), 'Moderate (51-100)'),
                              _legendRow(const Color(0xFFEF4444), 'Unhealthy (101+)'),
                              const Divider(height: 10, color: Colors.white10),
                              const Text(
                                'Junction Congestion',
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 9,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  Container(
                                    width: 6,
                                    height: 6,
                                    decoration: const BoxDecoration(
                                      color: AppColors.danger,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 6),
                                  const Text(
                                    'Radius ∝ Congestion / 4',
                                    style: TextStyle(color: AppColors.textDim, fontSize: 8),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  // ── Ray-casting Point-in-Polygon Tap Handler ──────────
  void _handleMapTap(LatLng point, Map<String, AqiModel> aqiLookup) {
    for (final w in _wards) {
      if (_pointInPolygon(point, w.points)) {
        final model = aqiLookup[w.name.toLowerCase().trim()];
        _showWardStatsSheet(w.name, model);
        return;
      }
    }
  }

  bool _pointInPolygon(LatLng test, List<LatLng> polygon) {
    bool inside = false;
    int j = polygon.length - 1;
    for (int i = 0; i < polygon.length; j = i++) {
      if (((polygon[i].latitude > test.latitude) !=
              (polygon[j].latitude > test.latitude)) &&
          (test.longitude <
              (polygon[j].longitude - polygon[i].longitude) *
                      (test.latitude - polygon[i].latitude) /
                      (polygon[j].latitude - polygon[i].latitude) +
                  polygon[i].longitude)) {
        inside = !inside;
      }
    }
    return inside;
  }

  // ── Show Stats Bottom Sheet ───────────────────────────
  void _showWardStatsSheet(String wardName, AqiModel? model) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      barrierColor: Colors.black.withOpacity(0.4),
      builder: (context) {
        final aqi = model?.aqi ?? 0.0;
        final pm25 = model?.pm25 ?? 0.0;
        final cong = model?.congestion ?? 0.0;
        
        return Container(
          margin: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          child: GlassContainer(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Ward Title Row
                Row(
                  children: [
                    const Icon(Icons.location_on, color: AppColors.primary, size: 24),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        wardName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: AppColors.textDim, size: 20),
                      onPressed: () => Navigator.pop(context),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
                const Divider(height: 24, color: Colors.white12),

                // Metrics Grid
                Row(
                  children: [
                    // AQI Indicator Box
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
                        decoration: BoxDecoration(
                          color: _aqiColor(aqi).withOpacity(0.12),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: _aqiColor(aqi).withOpacity(0.35)),
                        ),
                        child: Column(
                          children: [
                            Text(
                              aqi > 0 ? aqi.toInt().toString() : '—',
                              style: TextStyle(
                                color: _aqiColor(aqi),
                                fontSize: 28,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            const SizedBox(height: 2),
                            const Text(
                              'Air Quality (AQI)',
                              style: TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.w500),
                            ),
                            const SizedBox(height: 1),
                            Text(
                              _aqiLabel(aqi),
                              style: TextStyle(color: _aqiColor(aqi), fontSize: 9, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),

                    // PM2.5 Stat Box
                    Expanded(
                      child: _statColumn(
                        label: 'Fine Dust (PM2.5)',
                        value: pm25 > 0 ? '${pm25.toStringAsFixed(1)} µg/m³' : '—',
                        subtitle: 'Health Threshold: 35',
                        icon: Icons.bubble_chart,
                        accentColor: AppColors.primaryLight,
                      ),
                    ),
                    const SizedBox(width: 12),

                    // Congestion Stat Box
                    Expanded(
                      child: _statColumn(
                        label: 'Traffic Clog',
                        value: cong > 0 ? '${cong.toStringAsFixed(0)}%' : '—',
                        subtitle: cong > 60 ? 'Heavy Congestion' : 'Flowing',
                        icon: Icons.traffic,
                        accentColor: _congColor(cong),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _statColumn({
    required String label,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color accentColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Column(
        children: [
          Icon(icon, color: accentColor, size: 20),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(color: Colors.white70, fontSize: 9, fontWeight: FontWeight.w500),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 1),
          Text(
            subtitle,
            style: TextStyle(color: AppColors.textDim, fontSize: 8),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  // ── Legend row helper ─────────────────────────────────
  Widget _legendRow(Color color, String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 5),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            label,
            style: const TextStyle(color: AppColors.textDim, fontSize: 9, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  // ── Colors and thresholds helpers ─────────────────────
  Color _aqiColor(double aqi) {
    if (aqi <= 0) return AppColors.textDim;
    if (aqi <= 50) return const Color(0xFF10B981);
    if (aqi <= 100) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  String _aqiLabel(double aqi) {
    if (aqi <= 0) return '—';
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    return 'Unhealthy';
  }

  Color _congColor(double cong) {
    if (cong < 35) return const Color(0xFF10B981);
    if (cong < 65) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }
}

class _WardPolygon {
  final String name;
  final List<LatLng> points;
  const _WardPolygon({required this.name, required this.points});
}
