import 'package:flutter/material.dart';
import '../core/theme/glass_container.dart';

/// Reusable glassmorphic card widget matching the UrbanPulse design system,
/// now backed by GlassContainer for BackdropFilter blur and gradients.
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final double borderRadius;

  const GlassCard({
    super.key,
    required this.child,
    this.padding,
    this.borderRadius = 16,
  });

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      padding: padding ?? const EdgeInsets.all(20),
      child: child,
    );
  }
}
