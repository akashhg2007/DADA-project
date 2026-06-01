import 'package:json_annotation/json_annotation.dart';

part 'aqi_reading.g.dart';

/// Model representing a single AQI reading from a monitoring station.
@JsonSerializable()
class AqiReading {
  final String location;
  final DateTime timestamp;
  @JsonKey(name: 'AQI')
  final double aqi;
  @JsonKey(name: 'PM2.5')
  final double? pm25;
  @JsonKey(name: 'PM10')
  final double? pm10;
  @JsonKey(name: 'NO2')
  final double? no2;
  @JsonKey(name: 'SO2')
  final double? so2;

  const AqiReading({
    required this.location,
    required this.timestamp,
    required this.aqi,
    this.pm25,
    this.pm10,
    this.no2,
    this.so2,
  });

  factory AqiReading.fromJson(Map<String, dynamic> json) =>
      _$AqiReadingFromJson(json);
  Map<String, dynamic> toJson() => _$AqiReadingToJson(this);
}
