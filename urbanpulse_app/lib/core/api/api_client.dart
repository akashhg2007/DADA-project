import 'package:dio/dio.dart';
import 'api_config.dart';

/// Centralized Dio HTTP client for all UrbanPulse API calls.
class ApiClient {
  static Dio? _instance;

  static Dio get instance {
    if (_instance != null) return _instance!;

    _instance = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl, // http://10.0.2.2:8000 (Android emulator)
        connectTimeout: ApiConfig.connectTimeout,
        receiveTimeout: ApiConfig.receiveTimeout,
        headers: ApiConfig.defaultHeaders,
        validateStatus: (status) => status != null && status < 500,
      ),
    );

    _instance!.interceptors.addAll([
      // 1. Request / response logger
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        requestHeader: false,
        responseHeader: false,
        error: true,
        logPrint: (obj) => _log(obj.toString()),
      ),

      // 2. Error-handling interceptor
      InterceptorsWrapper(
        onError: (DioException err, ErrorInterceptorHandler handler) {
          final message = _mapError(err);
          handler.reject(
            DioException(
              requestOptions: err.requestOptions,
              response: err.response,
              type: err.type,
              error: message,
              message: message,
            ),
          );
        },
      ),
    ]);

    return _instance!;
  }

  /// Converts a DioException to a user-readable message.
  static String _mapError(DioException err) {
    switch (err.type) {
      case DioExceptionType.connectionTimeout:
        return 'Connection timed out. Is the backend running on ${ApiConfig.baseUrl}?';
      case DioExceptionType.receiveTimeout:
        return 'Server took too long to respond.';
      case DioExceptionType.sendTimeout:
        return 'Request timed out while sending data.';
      case DioExceptionType.connectionError:
        return 'Cannot reach backend at ${ApiConfig.baseUrl}. '
            'Make sure the FastAPI server is running.';
      case DioExceptionType.badResponse:
        final status = err.response?.statusCode;
        final body = err.response?.data;
        return 'Server error $status: $body';
      case DioExceptionType.cancel:
        return 'Request cancelled.';
      default:
        return err.message ?? 'Unexpected network error.';
    }
  }

  static void _log(String msg) {
    // ignore: avoid_print
    print('[ApiClient] $msg');
  }

  /// Tear down the singleton (useful for tests).
  static void reset() {
    _instance?.close();
    _instance = null;
  }
}
