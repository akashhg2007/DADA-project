import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/glass_container.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/aqi_line_chart.dart';
import '../../widgets/pulsing_dot.dart';
import 'dashboard_provider.dart';
import 'widgets/hero_header.dart';
import 'widgets/correlation_heatmap.dart';

/// Main dashboard screen.
/// Demonstrates ref.watch(provider).when(data:, loading: Shimmer, error: ErrorCard).
class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Watch live AQI and history in parallel
    final liveAqiAsync = ref.watch(liveAqiProvider);
    final historyAsync = ref.watch(historyAqiProvider);

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.primary,
          backgroundColor: AppColors.bgCard,
          strokeWidth: 2.5,
          onRefresh: () async {
            // ref.invalidate causes each provider to re-fetch from the backend
            ref.invalidate(liveAqiProvider);
            ref.invalidate(historyAqiProvider);
            ref.invalidate(dashboardKpiProvider);
            // Wait for both to settle so the spinner stays visible
            await Future.wait([
              ref.read(liveAqiProvider.future).catchError((_) => []),
              ref.read(historyAqiProvider.future).catchError((_) => []),
            ]);
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 1. Hero KPI Header ──────────────────────
                // HeroHeader internally watches dashboardKpiProvider and shows
                // its own shimmer state for the 4 KPI cards.
                const HeroHeader(),
                const SizedBox(height: 24),

                // ── 2. Live Status Banner ───────────────────
                liveAqiAsync.when(
                  loading: () => _shimmerBanner(),
                  error: (e, _) => _errorCard(
                    context,
                    'Live data unavailable',
                    e.toString(),
                    onRetry: () => ref.invalidate(liveAqiProvider),
                  ),
                  data: (readings) {
                    if (readings.isEmpty) {
                      return _emptyCard(context, 'No live readings found.');
                    }
                    return _liveStatusBanner(context, readings.length);
                  },
                ),
                const SizedBox(height: 24),

                // ── 3. AQI Trend Line Chart ─────────────────
                historyAsync.when(
                  loading: () => _shimmerChart(height: 260),
                  error: (e, _) => _errorCard(
                    context,
                    'Could not load AQI history',
                    e.toString(),
                    onRetry: () => ref.invalidate(historyAqiProvider),
                  ),
                  data: (points) => AqiLineChart(
                    data: points,
                    title: '7-Day AQI Trend',
                  )
                      .animate()
                      .fadeIn(duration: 400.ms, delay: 100.ms)
                      .slideY(
                        begin: 0.08,
                        end: 0,
                        duration: 400.ms,
                        delay: 100.ms,
                        curve: Curves.easeOutCubic,
                      ),
                ),
                const SizedBox(height: 24),

                // ── 4. Correlation Heatmap ──────────────────
                historyAsync.when(
                  loading: () => _shimmerChart(height: 220),
                  error: (_, __) => _errorCard(
                    context,
                    'Heatmap unavailable',
                    'Could not load historical data.',
                    onRetry: () => ref.invalidate(historyAqiProvider),
                  ),
                  data: (points) => CorrelationHeatmap(data: points)
                      .animate()
                      .fadeIn(duration: 400.ms, delay: 200.ms)
                      .slideY(
                        begin: 0.08,
                        end: 0,
                        duration: 400.ms,
                        delay: 200.ms,
                        curve: Curves.easeOutCubic,
                      ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ── Shimmer Helpers ───────────────────────────────────────────────────────

  /// Animated shimmer placeholder for any chart.
  Widget _shimmerChart({double height = 220}) {
    return Shimmer.fromColors(
      baseColor: const Color(0xFF1E293B),
      highlightColor: const Color(0xFF334155),
      child: Container(
        height: height,
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(16),
        ),
      ),
    );
  }

  /// Animated shimmer for the live status banner.
  Widget _shimmerBanner() {
    return Shimmer.fromColors(
      baseColor: const Color(0xFF1E293B),
      highlightColor: const Color(0xFF334155),
      child: Container(
        height: 56,
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(16),
        ),
      ),
    );
  }

  // ── Error Card ────────────────────────────────────────────────────────────

  /// Glass error card with a Retry button.
  Widget _errorCard(
    BuildContext context,
    String title,
    String detail, {
    required VoidCallback onRetry,
  }) {
    return GlassCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.cloud_off_rounded, color: AppColors.danger, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.danger,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  detail,
                  style: const TextStyle(
                    color: AppColors.textDim,
                    fontSize: 11,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: onRetry,
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: AppColors.danger.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: AppColors.danger.withValues(alpha: 0.3)),
              ),
              child: const Text(
                'Retry',
                style: TextStyle(
                  color: AppColors.danger,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Empty state ───────────────────────────────────────────────────────────

  Widget _emptyCard(BuildContext context, String message) {
    return GlassCard(
      child: Row(
        children: [
          const Icon(Icons.info_outline, color: AppColors.textDim, size: 20),
          const SizedBox(width: 12),
          Text(message,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(fontSize: 13)),
        ],
      ),
    );
  }

  // ── Live Status Banner ────────────────────────────────────────────────────

  Widget _liveStatusBanner(BuildContext context, int count) {
    return GlassContainer(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          const PulsingDot(color: AppColors.success, size: 8),
          const SizedBox(width: 10),
          Text(
            'Live • $count wards connected to backend',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontSize: 13,
                  color: AppColors.textMuted,
                ),
          ),
          const Spacer(),
          const Text(
            'LIVE',
            style: TextStyle(
              color: AppColors.success,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.4,
            ),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 500.ms);
  }
}
