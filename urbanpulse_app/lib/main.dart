import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme/app_theme.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/map/map_screen.dart';
import 'features/forecast/forecast_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Globally slow animations for testing on low-powered devices
  Animate.restartOnHotReload = true;

  // Lock to dark system overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: AppColors.bgDark,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  runApp(
    const ProviderScope(
      child: UrbanPulseApp(),
    ),
  );
}

class UrbanPulseApp extends StatelessWidget {
  const UrbanPulseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'UrbanPulse Bangalore',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      darkTheme: AppTheme.darkTheme,
      home: const AppShell(),
    );
  }
}

/// Main navigation shell with fade + slide page transitions.
class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _currentIndex = 0;
  int _previousIndex = 0;

  static const List<Widget> _screens = [
    DashboardScreen(),
    MapScreen(),
    ForecastScreen(),
  ];

  void _onDestinationSelected(int index) {
    if (index == _currentIndex) return;
    setState(() {
      _previousIndex = _currentIndex;
      _currentIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _PageSwitcher(
        currentIndex: _currentIndex,
        previousIndex: _previousIndex,
        screens: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: _onDestinationSelected,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.map_outlined),
            selectedIcon: Icon(Icons.map),
            label: 'Map',
          ),
          NavigationDestination(
            icon: Icon(Icons.trending_up_outlined),
            selectedIcon: Icon(Icons.trending_up),
            label: 'Forecast',
          ),
        ],
      ),
    );
  }
}

/// Custom page switcher using PageRouteBuilder-style FadeTransition + slideY.
class _PageSwitcher extends StatelessWidget {
  final int currentIndex;
  final int previousIndex;
  final List<Widget> screens;

  const _PageSwitcher({
    required this.currentIndex,
    required this.previousIndex,
    required this.screens,
  });

  @override
  Widget build(BuildContext context) {
    // Use flutter_animate's .animate() on the incoming page for
    // a smooth fade-in + upward slide transition.
    return IndexedStack(
      index: currentIndex,
      children: screens.asMap().entries.map((entry) {
        final i = entry.key;
        final screen = entry.value;
        if (i != currentIndex) return screen;
        // Animate only the active (incoming) page
        return screen
            .animate(key: ValueKey(currentIndex))
            .fadeIn(duration: 350.ms, curve: Curves.easeOut)
            .slideY(
              begin: 0.06,
              end: 0,
              duration: 350.ms,
              curve: Curves.easeOutCubic,
            );
      }).toList(),
    );
  }
}
