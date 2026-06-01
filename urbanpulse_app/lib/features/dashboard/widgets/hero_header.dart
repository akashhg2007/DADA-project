import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lottie/lottie.dart';
import 'package:shimmer/shimmer.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/theme/glass_container.dart';
import '../../../widgets/pulsing_dot.dart';
import '../dashboard_provider.dart';

/// Hero header: glassmorphic title banner + animated 4-column KPI card row.
class HeroHeader extends ConsumerWidget {
  const HeroHeader({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final kpiAsync = ref.watch(dashboardKpiProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── 1. Title Banner ───────────────────────────────
        GlassContainer(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              RichText(
                text: const TextSpan(
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.w700,
                    fontFamily: 'Inter',
                  ),
                  children: [
                    TextSpan(
                      text: 'UrbanPulse ',
                      style: TextStyle(color: Colors.white),
                    ),
                    TextSpan(
                      text: 'Bangalore',
                      style: TextStyle(color: AppColors.primary),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Real-time traffic & air quality intelligence',
                style: TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        )
            .animate()
            .fadeIn(duration: 400.ms)
            .slideY(begin: -0.1, end: 0, duration: 400.ms, curve: Curves.easeOut),
        const SizedBox(height: 24),

        // ── 2. KPI Cards Row ─────────────────────────────
        kpiAsync.when(
          loading: () => _shimmerGrid(),
          error: (e, _) => _errorBanner(context, e),
          data: (kpi) => _kpiGrid(kpi),
        ),
        const SizedBox(height: 12),

        // ── 3. Live Indicator with PulsingDot ────────────
        kpiAsync.when(
          loading: () => const SizedBox.shrink(),
          error: (_, __) => _offlineIndicator(context),
          data: (_) => _liveIndicator(context),
        ),
      ],
    );
  }

  // ── Animated KPI Grid ─────────────────────────────────────────────────────

  Widget _kpiGrid(DashboardKpi kpi) {
    final cards = [
      _KpiData(
        icon: Icons.air,
        iconColor: _aqiColor(kpi.cityAqi),
        label: 'City AQI',
        value: kpi.cityAqi.toInt().toString(),
        deltaText: '▼ -4.2%',
        deltaColor: AppColors.success,
      ),
      _KpiData(
        icon: Icons.warning_amber_rounded,
        iconColor: AppColors.danger,
        label: 'Worst Ward',
        value: kpi.worstWard,
        deltaText: 'AQI ${kpi.worstAqi.toInt()}',
        deltaColor: AppColors.danger,
        smallValue: kpi.worstWard.length > 8,
      ),
      _KpiData(
        icon: Icons.speed,
        iconColor: AppColors.success,
        label: 'Avg Speed',
        value: '${kpi.avgSpeed.toStringAsFixed(0)} km/h',
        deltaText: '▲ +8.2%',
        deltaColor: AppColors.success,
      ),
      _KpiData(
        icon: Icons.notifications_active,
        iconColor: AppColors.warning,
        label: 'Active Alerts',
        value: kpi.alertCount.toString(),
        deltaText: kpi.alertCount > 0
            ? '▲ +${kpi.alertCount} wards'
            : '● Stable',
        deltaColor:
            kpi.alertCount > 0 ? AppColors.danger : AppColors.success,
      ),
    ];

    return Row(
      children: cards.asMap().entries.map((entry) {
        final i = entry.key;
        final data = entry.value;
        return Expanded(
          child: Padding(
            padding: EdgeInsets.only(left: i == 0 ? 0 : 10),
            // flutter_animate: fadeIn + slideY with staggered 80ms delay per card
            child: _kpiCard(data)
                .animate()
                .fadeIn(
                  duration: 400.ms,
                  delay: (80 * i).ms,
                )
                .slideY(
                  begin: 0.2,
                  end: 0,
                  duration: 400.ms,
                  delay: (80 * i).ms,
                  curve: Curves.easeOutCubic,
                ),
          ),
        );
      }).toList(),
    );
  }

  Widget _kpiCard(_KpiData d) {
    return GlassContainer(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(d.icon, color: d.iconColor, size: 22),
          const SizedBox(height: 10),
          Text(
            d.label,
            style: const TextStyle(
              color: AppColors.textMuted,
              fontSize: 10,
              fontWeight: FontWeight.w500,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            d.value,
            style: TextStyle(
              color: Colors.white,
              fontSize: d.smallValue ? 15 : 21,
              fontWeight: FontWeight.w700,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 6),
          Text(
            d.deltaText,
            style: TextStyle(
              color: d.deltaColor,
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // ── Loading Shimmer ───────────────────────────────────────────────────────

  Widget _shimmerGrid() {
    return Shimmer.fromColors(
      baseColor: const Color(0xFF1E293B),
      highlightColor: const Color(0xFF334155),
      child: Row(
        children: List.generate(4, (i) {
          return Expanded(
            child: Container(
              margin: EdgeInsets.only(left: i == 0 ? 0 : 10),
              height: 118,
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          );
        }),
      ),
    );
  }

  // ── Empty / Error States ──────────────────────────────────────────────────

  Widget _errorBanner(BuildContext context, Object e) {
    return GlassContainer(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // Lottie empty state — "Awaiting city vitals"
          Center(
            child: SizedBox(
              height: 80,
              child: Lottie.network(
                'https://assets5.lottiefiles.com/packages/lf20_w51pcehl.json',
                repeat: true,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const Icon(
                  Icons.cloud_off_rounded,
                  color: AppColors.danger,
                  size: 36,
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Awaiting city vitals',
            style: TextStyle(
              color: AppColors.textMuted,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            e.toString(),
            style: const TextStyle(color: AppColors.textDim, fontSize: 10),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  // ── Live Indicators ───────────────────────────────────────────────────────

  Widget _liveIndicator(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const PulsingDot(color: AppColors.success, size: 8),
        const SizedBox(width: 6),
        Text(
          'Live • Connected to backend',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontSize: 12,
                color: AppColors.textMuted,
              ),
        ),
      ],
    )
        .animate()
        .fadeIn(duration: 600.ms, delay: 400.ms);
  }

  Widget _offlineIndicator(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: AppColors.textDim,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 6),
        Text(
          'Connecting…',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontSize: 12,
                color: AppColors.textDim,
              ),
        ),
      ],
    );
  }

  Color _aqiColor(double aqi) {
    if (aqi <= 50) return AppColors.success;
    if (aqi <= 100) return AppColors.warning;
    if (aqi <= 150) return const Color(0xFFFF9800);
    return AppColors.danger;
  }
}

/// Data class for a single KPI card.
class _KpiData {
  final IconData icon;
  final Color iconColor;
  final String label;
  final String value;
  final String deltaText;
  final Color deltaColor;
  final bool smallValue;

  const _KpiData({
    required this.icon,
    required this.iconColor,
    required this.label,
    required this.value,
    required this.deltaText,
    required this.deltaColor,
    this.smallValue = false,
  });
}
