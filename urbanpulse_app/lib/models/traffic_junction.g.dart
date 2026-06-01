// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'traffic_junction.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TrafficJunction _$TrafficJunctionFromJson(Map<String, dynamic> json) =>
    TrafficJunction(
      junctionName: json['junction_name'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      congestionLevel: (json['congestion_level'] as num).toDouble(),
      avgSpeedKmph: (json['avg_speed_kmph'] as num?)?.toDouble(),
      aqi: (json['AQI'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$TrafficJunctionToJson(TrafficJunction instance) =>
    <String, dynamic>{
      'junction_name': instance.junctionName,
      'latitude': instance.latitude,
      'longitude': instance.longitude,
      'congestion_level': instance.congestionLevel,
      'avg_speed_kmph': instance.avgSpeedKmph,
      'AQI': instance.aqi,
    };
