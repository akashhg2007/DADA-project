import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/theme/app_theme.dart';
import '../core/theme/glass_container.dart';
import '../models/aqi_model.dart';

/// Reusable 24H AQI Trend line chart wrapped in a glassmorphic container.
/// Displays two series: "Actual" (solid white) and "Forecast" (dashed primary).
class AqiLineChart extends StatelessWidget {
  final List<AqiPoint> data; // Mapped to "Actual" series
  final List<AqiPoint>? comparisonData; // Mapped to "Forecast" series
  final String title;
  final double height;

  const AqiLineChart({
    super.key,
    required this.data,
    this.comparisonData,
    this.title = '24H AQI Trend',
    this.height = 220,
  });

  @override
  Widget build(BuildContext context) {
    if (data.isEmpty) {
      return GlassContainer(
        child: SizedBox(
          height: height,
          child: Center(
            child: Text(
              'No chart data available',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ),
      );
    }

    final actualSpots = _toSpots(data);
    final forecastSpots = comparisonData != null ? _toSpots(comparisonData!) : null;

    final allY = actualSpots.map((s) => s.y).toList();
    if (forecastSpots != null) allY.addAll(forecastSpots.map((s) => s.y));
    final minY = (allY.reduce((a, b) => a < b ? a : b) - 10).clamp(0.0, 500.0);
    final maxY = allY.reduce((a, b) => a > b ? a : b) + 20;

    return GlassContainer(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Chart Title Header
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
                title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Chart Drawing Canvas
          SizedBox(
            height: height,
            child: LineChart(
              LineChartData(
                minY: minY,
                maxY: maxY,
                // Grid setup
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: ((maxY - minY) / 4).clamp(10, 100),
                  getDrawingHorizontalLine: (value) => const FlLine(
                    color: Color(0xFF334155),
                    strokeWidth: 0.8,
                  ),
                ),
                // Title labels setup
                titlesData: FlTitlesData(
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 40,
                      interval: ((maxY - minY) / 4).clamp(10, 100),
                      getTitlesWidget: (val, _) => Text(
                        val.toInt().toString(),
                        style: const TextStyle(
                          color: AppColors.textDim,
                          fontSize: 10,
                        ),
                      ),
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 28,
                      interval: (actualSpots.length / 5).ceilToDouble().clamp(1, 100),
                      getTitlesWidget: (val, _) {
                        final idx = val.toInt();
                        if (idx < 0 || idx >= data.length) return const SizedBox();
                        return Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text(
                            DateFormat.Hm().format(data[idx].time),
                            style: const TextStyle(
                              color: AppColors.textDim,
                              fontSize: 9,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
                // Border setup
                borderData: FlBorderData(show: false),
                // Touch interaction & Tooltip setup
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    getTooltipColor: (_) => const Color(0xFF1E293B),
                    tooltipRoundedRadius: 10,
                    getTooltipItems: (spots) => spots.map((s) {
                      final isForecast = s.barIndex == 1;
                      return LineTooltipItem(
                        'AQI ${s.y.toInt()} (${isForecast ? 'Forecast' : 'Actual'})',
                        TextStyle(
                          color: isForecast ? AppColors.primary : Colors.white,
                          fontWeight: FontWeight.w600,
                          fontSize: 11,
                        ),
                      );
                    }).toList(),
                  ),
                ),
                // Data series setup
                lineBarsData: [
                  _actualLine(actualSpots),
                  if (forecastSpots != null) _forecastLine(forecastSpots),
                ],
              ),
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeInOut,
            ),
          ),
        ],
      ),
    );
  }

  // 1. "Actual" Line: color white, barWidth 3, isCurved true, dotData false
  LineChartBarData _actualLine(List<FlSpot> spots) {
    return LineChartBarData(
      spots: spots,
      isCurved: true,
      curveSmoothness: 0.25,
      color: Colors.white,
      barWidth: 3,
      isStrokeCapRound: true,
      dotData: const FlDotData(show: false),
      belowBarData: BarAreaData(show: false),
    );
  }

  // 2. "Forecast" Line: color primary, barWidth 3, isCurved true, dashArray [5,5]
  LineChartBarData _forecastLine(List<FlSpot> spots) {
    return LineChartBarData(
      spots: spots,
      isCurved: true,
      curveSmoothness: 0.25,
      color: AppColors.primary,
      barWidth: 3,
      isStrokeCapRound: true,
      dashArray: [5, 5],
      dotData: const FlDotData(show: false),
      belowBarData: BarAreaData(show: false),
    );
  }

  List<FlSpot> _toSpots(List<AqiPoint> pts) {
    return List.generate(
      pts.length,
      (i) => FlSpot(i.toDouble(), pts[i].value),
    );
  }
}
