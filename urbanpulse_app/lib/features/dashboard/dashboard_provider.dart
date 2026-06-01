import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/api_config.dart';
import '../../models/aqi_model.dart';
import '../forecast/forecast_screen.dart' show forecastParamsProvider;

// ── Live AQI ──────────────────────────────────────────────────────────────────

/// Live AQI readings — one entry per Bangalore ward/junction.
///
/// Usage:
/// ```dart
/// final liveAsync = ref.watch(liveAqiProvider);
/// liveAsync.when(data: buildUI, loading: Shimmer, error: ErrorCard);
/// ```
///
/// Pull-to-refresh:
/// ```dart
/// ref.invalidate(liveAqiProvider);
/// ```
final liveAqiProvider = FutureProvider<List<AqiModel>>((ref) async {
  final response = await ApiClient.instance.get(ApiConfig.liveAqi);
  final List data = response.data as List;
  return data
      .map((j) => AqiModel.fromJson(j as Map<String, dynamic>))
      .toList();
});

// ── History AQI ───────────────────────────────────────────────────────────────

/// Ward filter applied to [historyAqiProvider].
/// Set to 'All' for city-wide aggregate.
final historyWardProvider = StateProvider<String>((ref) => 'All');

/// Historical AQI data points (default: last 7 days, all wards aggregated).
///
/// Automatically re-fetches when [historyWardProvider] changes.
/// Pull-to-refresh: `ref.invalidate(historyAqiProvider)`.
final historyAqiProvider = FutureProvider<List<AqiPoint>>((ref) async {
  final ward = ref.watch(historyWardProvider);
  final response = await ApiClient.instance.get(
    ApiConfig.historyAqi,
    queryParameters: {'ward': ward, 'days': 7},
  );
  final List data = response.data as List;
  return data.map((j) {
    final m = AqiModel.fromJson(j as Map<String, dynamic>);
    return AqiPoint(time: m.parsedTimestamp, value: m.aqi);
  }).toList();
});

// ── Traffic Junctions ─────────────────────────────────────────────────────────

/// Latest traffic telemetry for each monitored junction (raw JSON maps).
final trafficJunctionsProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final response = await ApiClient.instance.get(ApiConfig.trafficJunctions);
  final List data = response.data as List;
  return data.cast<Map<String, dynamic>>();
});

// ── Forecast ──────────────────────────────────────────────────────────────────

/// 24-hour baseline AQI forecast (no what-if parameters).
final forecastProvider = FutureProvider<List<AqiPoint>>((ref) async {
  final response = await ApiClient.instance.get(ApiConfig.forecastAqi);
  final List data = response.data as List;
  return data.map((j) {
    final m = AqiModel.fromJson(j as Map<String, dynamic>);
    return AqiPoint(time: m.parsedTimestamp, value: m.aqi);
  }).toList();
});

/// What-if forecast — automatically re-fires whenever [forecastParamsProvider]
/// changes (debounced in [ForecastScreen]).
final whatIfForecastProvider = FutureProvider<List<AqiPoint>>((ref) async {
  final params = ref.watch(forecastParamsProvider);
  final response = await ApiClient.instance.post(
    ApiConfig.forecastWhatIf,
    data: {'trafficAdjust': params.trafficAdjust, 'rainMm': params.rainMm},
  );
  final List data = response.data as List;
  return data.map((j) {
    final m = AqiModel.fromJson(j as Map<String, dynamic>);
    return AqiPoint(time: m.parsedTimestamp, value: m.aqi);
  }).toList();
});

// ── Dashboard KPI ─────────────────────────────────────────────────────────────

/// Aggregated KPI metrics computed from live AQI + traffic data.
class DashboardKpi {
  /// Average AQI across all monitored wards.
  final double cityAqi;

  /// Average vehicle speed across all monitored junctions (km/h).
  final double avgSpeed;

  /// Ward name with the highest live AQI reading.
  final String worstWard;

  /// AQI value of the worst ward.
  final double worstAqi;

  /// Number of wards where AQI exceeds 150 (Unhealthy threshold).
  final int alertCount;

  const DashboardKpi({
    required this.cityAqi,
    required this.avgSpeed,
    required this.worstWard,
    required this.worstAqi,
    required this.alertCount,
  });
}

/// Provides [DashboardKpi] by combining live AQI and traffic telemetry.
///
/// Pull-to-refresh: `ref.invalidate(dashboardKpiProvider)`.
final dashboardKpiProvider = FutureProvider<DashboardKpi>((ref) async {
  // Watch the liveAqiProvider so KPI auto-refreshes when live data refreshes
  final liveAsync = await ref.watch(liveAqiProvider.future);

  if (liveAsync.isEmpty) {
    return const DashboardKpi(
      cityAqi: 0,
      avgSpeed: 0,
      worstWard: '—',
      worstAqi: 0,
      alertCount: 0,
    );
  }

  final avgAqi = liveAsync.map((r) => r.aqi).reduce((a, b) => a + b) /
      liveAsync.length;
  final worst = liveAsync.reduce((a, b) => a.aqi > b.aqi ? a : b);
  final alerts = liveAsync.where((r) => r.aqi > 150).length;

  // Avg speed from traffic endpoint (optional — won't throw on failure)
  double avgSpeed = 0;
  try {
    final trafficResp =
        await ApiClient.instance.get(ApiConfig.trafficJunctions);
    final List tData = trafficResp.data as List;
    if (tData.isNotEmpty) {
      final speeds = tData
          .map((j) =>
              (j as Map<String, dynamic>)['avg_speed_kmph'] as num?)
          .whereType<num>()
          .toList();
      if (speeds.isNotEmpty) {
        avgSpeed =
            speeds.reduce((a, b) => a + b) / speeds.length;
      }
    }
  } catch (_) {
    // Traffic data is optional — KPI still valid without it
  }

  return DashboardKpi(
    cityAqi: avgAqi,
    avgSpeed: avgSpeed.toDouble(),
    worstWard: worst.ward,
    worstAqi: worst.aqi,
    alertCount: alerts,
  );
});
