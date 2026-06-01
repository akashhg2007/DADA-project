import 'package:json_annotation/json_annotation.dart';

part 'traffic_junction.g.dart';

/// Model representing a TomTom traffic junction reading.
@JsonSerializable()
class TrafficJunction {
  @JsonKey(name: 'junction_name')
  final String junctionName;
  final double latitude;
  final double longitude;
  @JsonKey(name: 'congestion_level')
  final double congestionLevel;
  @JsonKey(name: 'avg_speed_kmph')
  final double? avgSpeedKmph;
  @JsonKey(name: 'AQI')
  final double? aqi;

  const TrafficJunction({
    required this.junctionName,
    required this.latitude,
    required this.longitude,
    required this.congestionLevel,
    this.avgSpeedKmph,
    this.aqi,
  });

  factory TrafficJunction.fromJson(Map<String, dynamic> json) =>
      _$TrafficJunctionFromJson(json);
  Map<String, dynamic> toJson() => _$TrafficJunctionToJson(this);
}
