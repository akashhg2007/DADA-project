import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/theme/app_theme.dart';

/// A pulsing animated dot used for live status indicators.
/// The dot scales and fades in/out to create a heartbeat effect.
class PulsingDot extends StatelessWidget {
  final Color color;
  final double size;

  const PulsingDot({
    super.key,
    this.color = AppColors.success,
    this.size = 8,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size + 8,
      height: size + 8,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Outer pulsing ring
          Container(
            width: size + 8,
            height: size + 8,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.0),
              shape: BoxShape.circle,
            ),
          )
              .animate(onPlay: (c) => c.repeat())
              .custom(
                duration: 1400.ms,
                curve: Curves.easeOut,
                builder: (context, value, child) {
                  return Container(
                    width: (size + 8) * value,
                    height: (size + 8) * value,
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: (1 - value) * 0.45),
                      shape: BoxShape.circle,
                    ),
                  );
                },
              ),

          // Solid inner dot
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: color.withValues(alpha: 0.6),
                  blurRadius: 5,
                  spreadRadius: 1,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
