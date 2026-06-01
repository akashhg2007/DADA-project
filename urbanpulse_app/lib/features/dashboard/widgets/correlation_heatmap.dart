import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/theme/glass_container.dart';
import '../../../models/aqi_model.dart';

/// 7×24 AQI heatmap (day-of-week × hour-of-day) showing when Bangalore is most polluted.
class CorrelationHeatmap extends StatelessWidget {
  final List<AqiPoint> data;

  const CorrelationHeatmap({super.key, required this.data});

  static const _days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  @override
  Widget build(BuildContext context) {
    // Build a 7×24 matrix of average AQI.
    final matrix = List.generate(7, (_) => List.filled(24, 0.0));
    final counts = List.generate(7, (_) => List.filled(24, 0));

    for (final pt in data) {
      final dow = pt.time.weekday - 1; // 0=Mon
      final hour = pt.time.hour;
      matrix[dow][hour] += pt.value;
      counts[dow][hour] += 1;
    }

    // Compute averages and find range for color mapping.
    double maxVal = 1;
    for (int d = 0; d < 7; d++) {
      for (int h = 0; h < 24; h++) {
        if (counts[d][h] > 0) {
          matrix[d][h] /= counts[d][h];
          if (matrix[d][h] > maxVal) maxVal = matrix[d][h];
        }
      }
    }

    return GlassContainer(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Title Banner
          Row(
            children: [
              Container(
                width: 4,
                height: 16,
                decoration: BoxDecoration(
                  color: AppColors.warning,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                'When is Bangalore Most Polluted?',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Day labels + Heatmap Row
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Y-Axis Day Labels
              Column(
                children: List.generate(7, (d) {
                  return SizedBox(
                    height: 16,
                    width: 32,
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        _days[d],
                        style: const TextStyle(
                          color: AppColors.textDim,
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(width: 8),

              // 7×24 GridView Area
              Expanded(
                child: GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 24,
                    mainAxisSpacing: 1.5,
                    crossAxisSpacing: 1.5,
                    childAspectRatio: 1.0,
                  ),
                  itemCount: 168,
                  itemBuilder: (context, index) {
                    final d = index ~/ 24;
                    final h = index % 24;
                    final val = matrix[d][h];
                    final t = maxVal > 0 ? (val / maxVal).clamp(0.0, 1.0) : 0.0;
                    
                    // Each cell: Container color from AQI value, lerp between #1E293B and #EF4444
                    final color = Color.lerp(
                      const Color(0xFF1E293B),
                      const Color(0xFFEF4444),
                      t,
                    )!;

                    final hourStr = _formatHour(h);
                    final dayStr = _days[d];

                    // OnTap: showTooltip with "Mon 9am: AQI 156"
                    return Tooltip(
                      message: '$dayStr $hourStr: AQI ${val.toInt()}',
                      triggerMode: TooltipTriggerMode.tap,
                      preferBelow: false,
                      child: GestureDetector(
                        onTap: () {}, // empty callback ensures GestureDetector works with Tooltip tap trigger
                        child: Container(
                          decoration: BoxDecoration(
                            color: color,
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Hour axis helper indicators (labels under the grid)
          Row(
            children: [
              const SizedBox(width: 40),
              ...List.generate(24, (h) {
                if (h % 6 == 0) {
                  return Expanded(
                    flex: 6,
                    child: Text(
                      _formatHour(h),
                      style: const TextStyle(
                        color: AppColors.textDim,
                        fontSize: 8,
                      ),
                    ),
                  );
                }
                return const SizedBox.shrink();
              }),
            ],
          ),
          const SizedBox(height: 16),

          // Legend Row
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                'Low AQI',
                style: TextStyle(color: AppColors.textDim, fontSize: 10),
              ),
              const SizedBox(width: 8),
              
              // Dynamic gradient Container showing the color ramp
              Container(
                height: 8,
                width: 140,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(4),
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF1E293B),
                      Color(0xFFEF4444),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                'High AQI',
                style: TextStyle(color: AppColors.textDim, fontSize: 10),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatHour(int h) {
    if (h == 0) return '12am';
    if (h < 12) return '${h}am';
    if (h == 12) return '12pm';
    return '${h - 12}pm';
  }
}
