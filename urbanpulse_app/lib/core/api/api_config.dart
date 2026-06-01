/// API configuration constants for the UrbanPulse backend.
class ApiConfig {
  ApiConfig._();

  /// Base URL for the UrbanPulse API.
  /// 10.0.2.2 resolves to host localhost from Android emulators.
  /// For physical devices on the same Wi-Fi, use your machine's LAN IP.
  static const String baseUrl = 'http://10.0.2.2:8000';

  /// API endpoints – must match FastAPI routes in backend/main.py
  static const String liveAqi = '/api/live/aqi';
  static const String historyAqi = '/api/history/aqi';
  static const String forecastAqi = '/api/forecast/aqi';
  static const String forecastWhatIf = '/api/forecast/whatif';
  static const String trafficJunctions = '/api/traffic/junctions';

  /// Request timeouts
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 15);

  /// Headers
  static Map<String, String> get defaultHeaders => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
}
