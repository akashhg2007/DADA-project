import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lottie/lottie.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/glass_container.dart';
import '../../widgets/aqi_line_chart.dart';
import '../../models/aqi_model.dart';
import '../dashboard/dashboard_provider.dart';

// ── StateNotifier for forecast parameters ─────────────────────────────────────

class ForecastParams {
  final double trafficAdjust; // -50 to +50
  final double rainMm; // 0 to 10

  const ForecastParams({
    this.trafficAdjust = 0.0,
    this.rainMm = 0.0,
  });

  ForecastParams copyWith({double? trafficAdjust, double? rainMm}) {
    return ForecastParams(
      trafficAdjust: trafficAdjust ?? this.trafficAdjust,
      rainMm: rainMm ?? this.rainMm,
    );
  }
}

class ForecastParamsNotifier extends StateNotifier<ForecastParams> {
  ForecastParamsNotifier() : super(const ForecastParams());

  void setTrafficAdjust(double v) => state = state.copyWith(trafficAdjust: v);
  void setRainMm(double v) => state = state.copyWith(rainMm: v);
  void reset() => state = const ForecastParams();
}

final forecastParamsProvider =
    StateNotifierProvider<ForecastParamsNotifier, ForecastParams>(
  (ref) => ForecastParamsNotifier(),
);

// ── Forecast Screen ───────────────────────────────────────────────────────────

/// Forecast "What-If" screen:
/// — Two sliders (Traffic Change %, Rainfall mm) in GlassContainer
/// — 300ms debounce on slider change calls POST /api/forecast/whatif
/// — Updated AQI line chart (baseline vs what-if)
/// — AnimatedContainer showing the "% AQI Change" big number
/// — Lottie rain/cloud animation when rainMm > 0
class ForecastScreen extends ConsumerStatefulWidget {
  const ForecastScreen({super.key});

  @override
  ConsumerState<ForecastScreen> createState() => _ForecastScreenState();
}

class _ForecastScreenState extends ConsumerState<ForecastScreen>
    with SingleTickerProviderStateMixin {
  Timer? _debounce;
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  /// Debounce slider updates by 300ms before firing the what-if API call.
  void _onParamChanged(void Function() immediateUpdate) {
    immediateUpdate(); // Instant visual feedback
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      // Invalidate the what-if provider so it re-fires with new param state
      ref.invalidate(whatIfForecastProvider);
      _pulseController.forward(from: 0);
    });
  }

  @override
  Widget build(BuildContext context) {
    final params = ref.watch(forecastParamsProvider);
    final baselineAsync = ref.watch(forecastProvider);
    final whatIfAsync = ref.watch(whatIfForecastProvider);

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Page Header ─────────────────────────────
              Text(
                '24H AI Forecast',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 4),
              Text(
                'XGBoost-powered predictions with what-if scenario simulation',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 20),

              // ── Lottie Rain/Cloud Animation (rainMm > 0) ──
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 400),
                transitionBuilder: (child, anim) =>
                    FadeTransition(opacity: anim, child: child),
                child: params.rainMm > 0
                    ? Center(
                        key: const ValueKey('rain_lottie'),
                        child: SizedBox(
                          height: 90,
                          child: Lottie.network(
                            'https://raw.githubusercontent.com/lottie-react/lottie-react/master/stories/data/rain.json',
                            repeat: true,
                            fit: BoxFit.contain,
                            errorBuilder: (ctx, e, st) => const Icon(
                              Icons.water_drop_outlined,
                              color: AppColors.primary,
                              size: 48,
                            ),
                          ),
                        ),
                      )
                    : const SizedBox(key: ValueKey('no_rain'), height: 0),
              ),

              // ── What-If Sliders Card ─────────────────────
              GlassContainer(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Card header
                    Row(
                      children: [
                        Container(
                          width: 4,
                          height: 16,
                          decoration: BoxDecoration(
                            color: AppColors.primary,
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'What-If Controls',
                          style:
                              Theme.of(context).textTheme.titleLarge?.copyWith(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w600,
                                  ),
                        ),
                        const Spacer(),
                        // Reset button
                        GestureDetector(
                          onTap: () {
                            ref.read(forecastParamsProvider.notifier).reset();
                            ref.invalidate(whatIfForecastProvider);
                          },
                          child: const Text(
                            'Reset',
                            style: TextStyle(
                              color: AppColors.textDim,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // ── Traffic Change % Slider ──────────────
                    Row(
                      children: [
                        const Icon(Icons.traffic,
                            color: AppColors.warning, size: 16),
                        const SizedBox(width: 8),
                        const Text(
                          'Traffic Change %',
                          style: TextStyle(
                            color: AppColors.textMuted,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppColors.warning.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '${params.trafficAdjust >= 0 ? '+' : ''}${params.trafficAdjust.toStringAsFixed(0)}%',
                            style: const TextStyle(
                              color: AppColors.warning,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    SliderTheme(
                      data: SliderTheme.of(context).copyWith(
                        activeTrackColor: AppColors.primary,
                        inactiveTrackColor: AppColors.bgElevated,
                        thumbColor: AppColors.primary,
                        overlayColor: AppColors.primary.withValues(alpha: 0.15),
                        trackHeight: 3,
                        thumbShape: const RoundSliderThumbShape(
                          enabledThumbRadius: 8,
                        ),
                        valueIndicatorColor: AppColors.bgCard,
                        valueIndicatorTextStyle: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                        ),
                      ),
                      child: Slider(
                        value: params.trafficAdjust,
                        min: -50,
                        max: 50,
                        divisions: 20,
                        label:
                            '${params.trafficAdjust >= 0 ? '+' : ''}${params.trafficAdjust.toStringAsFixed(0)}%',
                        onChanged: (v) => _onParamChanged(() {
                          ref
                              .read(forecastParamsProvider.notifier)
                              .setTrafficAdjust(v);
                        }),
                      ),
                    ),
                    // Range labels
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('-50%',
                              style: TextStyle(
                                  color: AppColors.textDim, fontSize: 9)),
                          Text('0',
                              style: TextStyle(
                                  color: AppColors.textDim, fontSize: 9)),
                          Text('+50%',
                              style: TextStyle(
                                  color: AppColors.textDim, fontSize: 9)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    // ── Rainfall mm Slider ───────────────────
                    Row(
                      children: [
                        const Icon(Icons.water_drop,
                            color: AppColors.primaryLight, size: 16),
                        const SizedBox(width: 8),
                        const Text(
                          'Rainfall mm',
                          style: TextStyle(
                            color: AppColors.textMuted,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppColors.primaryLight.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '${params.rainMm.toStringAsFixed(1)} mm',
                            style: const TextStyle(
                              color: AppColors.primaryLight,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    SliderTheme(
                      data: SliderTheme.of(context).copyWith(
                        activeTrackColor: AppColors.primaryLight,
                        inactiveTrackColor: AppColors.bgElevated,
                        thumbColor: AppColors.primaryLight,
                        overlayColor:
                            AppColors.primaryLight.withValues(alpha: 0.15),
                        trackHeight: 3,
                        thumbShape: const RoundSliderThumbShape(
                          enabledThumbRadius: 8,
                        ),
                        valueIndicatorColor: AppColors.bgCard,
                        valueIndicatorTextStyle: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                        ),
                      ),
                      child: Slider(
                        value: params.rainMm,
                        min: 0,
                        max: 10,
                        divisions: 20,
                        label: '${params.rainMm.toStringAsFixed(1)} mm',
                        onChanged: (v) => _onParamChanged(() {
                          ref
                              .read(forecastParamsProvider.notifier)
                              .setRainMm(v);
                        }),
                      ),
                    ),
                    // Range labels
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('0 mm',
                              style: TextStyle(
                                  color: AppColors.textDim, fontSize: 9)),
                          Text('5 mm',
                              style: TextStyle(
                                  color: AppColors.textDim, fontSize: 9)),
                          Text('10 mm',
                              style: TextStyle(
                                  color: AppColors.textDim, fontSize: 9)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // ── % AQI Change AnimatedContainer ──────────────
              _buildAqiChangeBanner(baselineAsync, whatIfAsync),
              const SizedBox(height: 20),

              // ── Dual AQI Line Chart ─────────────────────────
              _buildChart(baselineAsync, whatIfAsync),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  /// AnimatedContainer displaying "% AQI Change" big number.
  Widget _buildAqiChangeBanner(
    AsyncValue<List<AqiPoint>> baselineAsync,
    AsyncValue<List<AqiPoint>> whatIfAsync,
  ) {
    return baselineAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (basePts) {
        return whatIfAsync.when(
          loading: () => const SizedBox.shrink(),
          error: (_, __) => const SizedBox.shrink(),
          data: (whatIfPts) {
            if (basePts.isEmpty || whatIfPts.isEmpty) {
              return const SizedBox.shrink();
            }

            final baseAvg = basePts.map((p) => p.value).reduce((a, b) => a + b) /
                basePts.length;
            final whatIfAvg = whatIfPts
                    .map((p) => p.value)
                    .reduce((a, b) => a + b) /
                whatIfPts.length;
            final delta = whatIfAvg - baseAvg;
            final pct = baseAvg > 0 ? (delta / baseAvg * 100) : 0.0;
            final better = delta < 0;
            final color = better ? AppColors.success : AppColors.danger;
            final icon = better ? Icons.trending_down : Icons.trending_up;

            return AnimatedContainer(
              duration: const Duration(milliseconds: 500),
              curve: Curves.easeOutCubic,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    color.withValues(alpha: 0.12),
                    color.withValues(alpha: 0.05),
                  ],
                ),
                border: Border.all(color: color.withValues(alpha: 0.3)),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
              child: Row(
                children: [
                  Icon(icon, color: color, size: 40),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Big % number
                      Text(
                        '${better ? '' : '+'}${pct.toStringAsFixed(1)}%',
                        style: TextStyle(
                          color: color,
                          fontSize: 36,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -1.5,
                        ),
                      ),
                      Text(
                        'AQI Change vs Baseline',
                        style: const TextStyle(
                          color: AppColors.textMuted,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        'Baseline',
                        style: const TextStyle(
                          color: AppColors.textDim,
                          fontSize: 10,
                        ),
                      ),
                      Text(
                        '${baseAvg.toInt()} AQI',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Scenario',
                        style: const TextStyle(
                          color: AppColors.textDim,
                          fontSize: 10,
                        ),
                      ),
                      Text(
                        '${whatIfAvg.toInt()} AQI',
                        style: TextStyle(
                          color: color,
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  /// Dual-line AQI chart: Actual baseline (white) + What-If forecast (dashed primary).
  Widget _buildChart(
    AsyncValue<List<AqiPoint>> baselineAsync,
    AsyncValue<List<AqiPoint>> whatIfAsync,
  ) {
    return baselineAsync.when(
      loading: () => GlassContainer(
        child: const SizedBox(
          height: 220,
          child: Center(
            child: CircularProgressIndicator(
              color: AppColors.primary,
              strokeWidth: 2,
            ),
          ),
        ),
      ),
      error: (e, _) => GlassContainer(
        child: SizedBox(
          height: 220,
          child: Center(
            child: Text(
              'Error loading forecast: $e',
              style: const TextStyle(color: AppColors.danger, fontSize: 12),
            ),
          ),
        ),
      ),
      data: (basePts) {
        final compPts = whatIfAsync.valueOrNull;
        return AqiLineChart(
          data: basePts,
          comparisonData: compPts,
          title: '24H AQI Forecast',
        );
      },
    );
  }
}
