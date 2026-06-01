import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

/// Dashboard KPI metric card with accent color strip.
class KpiCard extends StatelessWidget {
  final String title;
  final String value;
  final String subtitle;
  final Color accentColor;
  final IconData? icon;

  const KpiCard({
    super.key,
    required this.title,
    required this.value,
    required this.subtitle,
    required this.accentColor,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: glassDecoration(),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Stack(
          children: [
            // Accent strip at top
            Positioned(
              top: 0,
              left: 0,
              right: 0,
              child: Container(
                height: 3,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      accentColor,
                      accentColor.withValues(alpha: 0.3),
                    ],
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 18, 16, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Title row
                  Row(
                    children: [
                      if (icon != null) ...[
                        Icon(icon, size: 14, color: AppColors.textMuted),
                        const SizedBox(width: 6),
                      ],
                      Text(
                        title.toUpperCase(),
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: AppColors.textMuted,
                              fontSize: 10,
                              letterSpacing: 1.4,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // Big value
                  Text(
                    value,
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                          fontSize: 26,
                          color: AppColors.textMain,
                        ),
                  ),
                  const SizedBox(height: 4),

                  // Subtitle / delta
                  Text(
                    subtitle,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontSize: 12,
                          color: AppColors.textMuted,
                        ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
